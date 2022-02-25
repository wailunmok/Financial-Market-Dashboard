""" Library for model training: arima """
import os
import pandas as pd
from plotly.subplots import make_subplots
from prophet import Prophet
from prophet.diagnostics import cross_validation
from prophet.plot import plot_plotly, plot_components_plotly


def get_model_forecast_and_validation(data_in, validation_steps, *argv):
    # Perform model forecast (1 step ahead) and validation

    # Initialise max validation steps: at least 10 observations required
    actual_val_steps = min(data_in.dropna().shape[0] - 10, validation_steps)

    # forecast and validation
    res_forecast = model_forecast(data_in, 1, *argv)
    res_validation, res_val_summary = model_validation(data_in, actual_val_steps, model_forecast, *argv)

    results = pd.concat([res_forecast, res_val_summary])
    results.loc['validation_steps', :] = actual_val_steps

    return results, res_validation


def model_forecast(data_in, steps, *argv):
    # Perform h-step ahead forecast with prophet model

    # Initialise
    alpha = 0.05  # CI = [0.025, 0.975]
    results = pd.DataFrame(index=['forecast', 'ci_lower', 'ci_upper'], columns=data_in.columns)

    # model settings
    model_settings = {'growth': 'linear', 'seasonality_mode': 'additive', 'interval_width': (1 - alpha),
                      'weekly_seasonality': 'auto', 'yearly_seasonality': True}

    # Loop over time series
    for ts in data_in.columns:
        series = data_in.loc[:, ts].dropna()
        df = pd.DataFrame([series.index, series.values], index=['ds', 'y']).T

        # fit model
        with suppress_stdout_stderr():
            model = Prophet(**model_settings)
            model.fit(df)

        # forecast
        future = model.make_future_dataframe(periods=steps, freq=series.index.freq, include_history=False)
        forecast = model.predict(future).iloc[-1, ]
        results.loc[:, ts] = forecast[['yhat', 'yhat_lower', 'yhat_upper']].values

    results = pd.concat([(results.loc[['forecast'], ] > 0).rename({'forecast': 'invest'}), results])

    return results


# Decorator class to suppress pystan/prophet output
# from https://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions
class suppress_stdout_stderr(object):
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = (os.dup(1), os.dup(2))

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0], 1)
        os.dup2(self.save_fds[1], 2)
        # Close the null files
        os.close(self.null_fds[0])
        os.close(self.null_fds[1])
    # used like
    #  with suppress_stdout_stderr():
    #      p = Propet(*kwargs).fit(training_data)


def model_validation(data_in, steps, func_model_forecast, *argv):
    # Perform rolling window forecast (generic function)
    # The model_forecast parameters are supplied with argv

    # Initialise
    multi_idx = pd.MultiIndex.from_product([data_in.columns, ('actual', 'forecast', 'ci_lower', 'ci_upper')],
                                           names=['index', 'type'])
    results = pd.DataFrame(index=data_in.index, columns=multi_idx)
    results.loc[:, (slice(None), 'actual')] = data_in.values

    # Loop over steps
    n_obs = data_in.shape[0]
    for count in range(n_obs - steps, n_obs):
        # Initialise train test split
        train = data_in.iloc[:count, ]
        test = data_in.iloc[[count],]

        # Forecast
        forecast_res = func_model_forecast(train, 1, *argv)

        # Save results
        results.loc[test.index, (slice(None), 'forecast')] = forecast_res.loc['forecast',].values
        results.loc[test.index, (slice(None), 'ci_lower')] = forecast_res.loc['ci_lower',].values
        results.loc[test.index, (slice(None), 'ci_upper')] = forecast_res.loc['ci_upper',].values

    results_summary = model_validation_summary(results)

    return results, results_summary


def model_validation_summary(forecast_results):
    # Calculate summary statistics from the rolling forecast (generic function)
    # accuracy: correct forecast of positive and negative returns
    # payout: payout for following strategy with 100 EUR (excl. transaction fees and bid-ask spread)

    res = forecast_results.dropna()
    results = pd.DataFrame(index=['accuracy', 'payout_from_100'], columns=res.columns.levels[0])

    # Calculate accuracy
    pos_ret_act = res.loc[:, (slice(None), 'actual')] > 0
    pos_ret_for = res.loc[:, (slice(None), 'forecast')] > 0
    accuracy = (pos_ret_act.values == pos_ret_for.values).sum(axis=0) / res.shape[0]

    # Calculate payout
    ret_act = res.loc[:, (slice(None), 'actual')]
    payout = (ret_act.values * pos_ret_for.values + 1).prod(axis=0) * 100

    results.loc['accuracy',] = accuracy
    results.loc['payout_from_100',] = payout

    return results


def plot_validation(forecast_results, title='', data_level=None):
    # Create forecast plots
    # Plot levels if supplied

    # initialise
    series = forecast_results.columns.levels[0]
    n_rows = len(series)
    n_cols = 1
    fig = make_subplots(rows=n_rows, cols=1, subplot_titles=series, vertical_spacing=0.05)

    # loop over series
    for r, ts in enumerate(series):
        df_fc_ts = forecast_results.loc[:, (ts, slice(None))].dropna().droplevel(0, axis=1)

        correct = (((df_fc_ts['actual'] < 0) & (df_fc_ts['forecast'] < 0)) |
                   ((df_fc_ts['actual'] > 0) & (df_fc_ts['forecast'] > 0)))
        correct_idx = correct.index[correct]
        incorrect_idx = correct.index[~correct]

        # Check if level data is supplied
        if not isinstance(data_level, type(None)):
            first_index = data_level.index[data_level.index.get_loc(df_fc_ts.index[0]) - 1]
            df_fc_price = df_fc_ts.copy()

            price_prev = data_level.loc[first_index:data_level.index[-2], ts].values
            df_fc_price = df_fc_price.apply(lambda x: (1 + x) * price_prev, axis=0)
            df_fc_price.loc[first_index, :] = data_level.loc[first_index, ts]
            df_fc_price.sort_index(inplace=True)
            df_fc_ts = df_fc_price

        fig.add_scatter(x=df_fc_ts.index, y=df_fc_ts['actual'], name='actual', mode='lines',
                        line=dict(color='#1f77b4'), row=r + 1, col=n_cols)
        # fig.add_scatter(x=df_fc_ts.index, y=df_fc_ts['forecast'], name='forecast', mode='markers',
        #                 marker=dict(color='#2ca02c'), row=r + 1, col=n_cols)
        fig.add_scatter(x=correct_idx, y=df_fc_ts['forecast'][correct_idx], name='correct forecast',
                        mode='markers', marker=dict(color='#2ca02c'), row=r + 1, col=n_cols)
        fig.add_scatter(x=incorrect_idx, y=df_fc_ts['forecast'][incorrect_idx], name='wrong forecast',
                        mode='markers', marker=dict(color='#d62728', symbol='x'), row=r + 1, col=n_cols)
        fig.add_scatter(x=df_fc_ts.index, y=df_fc_ts['ci_lower'], name='95%-confidence interval', mode='lines',
                        line=dict(dash='dot', color='#7f7f7f'), row=r + 1, col=n_cols)
        fig.add_scatter(x=df_fc_ts.index, y=df_fc_ts['ci_upper'], name='95%-confidence interval', mode='lines',
                        line=dict(dash='dot', color='#7f7f7f'), row=r + 1, col=n_cols)

    # Legend: remove duplicate names
    names = set()
    fig.for_each_trace(
        lambda trace:
        trace.update(showlegend=False)
        if (trace.name in names) else names.add(trace.name))
    if isinstance(data_level, type(None)):
        fig.update_yaxes({'tickformat': ',.0%'})
    fig.update_layout(height=len(series) * 300, title_text=title)
    fig.show()

    return fig


def load(forecast_summary, forecast_results):
    # Save data
    output_path = os.getcwd() + '/output/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    forecast_summary.to_csv(output_path + 'model_prophet_forecast_summary.csv')
    forecast_results.to_csv(output_path + 'model_prophet_forecast_results.csv')

    return


def model_dev(data_in):
    # initialise
    series = data_in['^AEX'].dropna()

    df = pd.DataFrame()
    df['ds'] = series.index
    df['y'] = series.values

    # Fit model
    model = Prophet(growth='linear', seasonality_mode='additive', weekly_seasonality='auto', yearly_seasonality=True)
    model.fit(df)

    # forecast (daily freq)
    future = model.make_future_dataframe(periods=12)
    forecast = model.predict(future)
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()

    # Cross validation fixed cutoff
    val_steps = 12
    cutoffs = series.index[-(val_steps + 1)]
    horizon = series.index[-1] - cutoffs
    df_cv = cross_validation(model, horizon=horizon, cutoffs=[cutoffs])

    # Cross validation rolling cutoff (does not always work for month due to unequally spaced horizon)
    val_steps = 12
    cutoffs = series.index[-(val_steps + 1):-1].to_list()
    horizon = (series.index[1:] - series.index[:-1]).max()
    df_cv = cross_validation(model, horizon=horizon, cutoffs=cutoffs)

    # cross validation 1 step
    cutoffs = [series.index[-3], series.index[-2]]
    horizon = series.index[-1] - series.index[-2]
    df_cv = cross_validation(model, horizon=horizon, cutoffs=cutoffs)

    # forecast test
    df2 = df.iloc[:-1, ]
    model = Prophet(growth='linear', seasonality_mode='additive', weekly_seasonality='auto', yearly_seasonality=True)
    model.fit(df2)
    future = model.make_future_dataframe(periods=2, freq=series.index.freq, include_history=False)
    forecast = model.predict(future)
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()


    # plot (does not work in debug)
    # fig1 = model.plot(forecast)
    # fig2 = model.plot_components(forecast)

    # plotly
    fig = plot_plotly(model, forecast)
    fig.show()

    fig = plot_components_plotly(model, forecast)
    fig.show()

    # extra: hyperparameter tuning

    return


def execute(data_in, validation_steps=24, *argv):
    # The model_forecast parameters are supplied with argv

    forecast_summary, forecast_results = get_model_forecast_and_validation(data_in, validation_steps, *argv)

    load(forecast_summary, forecast_results)

    return forecast_summary, forecast_results
