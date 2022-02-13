""" Library for model training: arima """
import os
import pandas as pd
import statsmodels.api as sm
from plotly.subplots import make_subplots


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


def model_forecast(data_in, steps, order=(1, 0, 0)):
    # Perform h-step ahead forecast with ARIMA model

    # Initialise
    alpha = 0.05  # CI = [0.025, 0.975]
    results = pd.DataFrame(index=['forecast', 'ci_lower', 'ci_upper'], columns=data_in.columns)

    # Loop over time series
    for ts in data_in.columns:
        series = data_in.loc[:, ts].dropna()

        model = sm.tsa.arima.ARIMA(series, order=order)
        res = model.fit(method='innovations_mle')
        forecast = res.get_forecast(steps).summary_frame(alpha=alpha).iloc[-1, ]
        results.loc[:, ts] = forecast[['mean', 'mean_ci_lower', 'mean_ci_upper']].values

    results = pd.concat([(results.loc[['forecast'], ] > 0).rename({'forecast': 'invest'}), results])

    return results


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
        test = data_in.iloc[[count], ]

        # Forecast
        forecast_res = func_model_forecast(train, 1, *argv)

        # Save results
        results.loc[test.index, (slice(None), 'forecast')] = forecast_res.loc['forecast', ].values
        results.loc[test.index, (slice(None), 'ci_lower')] = forecast_res.loc['ci_lower', ].values
        results.loc[test.index, (slice(None), 'ci_upper')] = forecast_res.loc['ci_upper', ].values

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

    results.loc['accuracy', ] = accuracy
    results.loc['payout_from_100', ] = payout

    return results


def plot_validation(forecast_results, title=''):
    # Create forecast plots

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
        df_fc_ts['correct'] = correct

        fig.add_scatter(x=df_fc_ts.index, y=df_fc_ts['actual'], name='actual', mode='lines',
                        line=dict(color='#1f77b4'), row=r + 1, col=n_cols)
        # fig.add_scatter(x=df_fc_ts.index, y=df_fc_ts['forecast'], name='forecast', mode='markers',
        #                 marker=dict(color='#2ca02c'), row=r + 1, col=n_cols)
        fig.add_scatter(x=df_fc_ts.index[correct], y=df_fc_ts['forecast'][correct], name='correct forecast',
                        mode='markers', marker=dict(color='#2ca02c'), row=r + 1, col=n_cols)
        fig.add_scatter(x=df_fc_ts.index[~correct], y=df_fc_ts['forecast'][~correct], name='wrong forecast',
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
    fig.update_yaxes({'tickformat': ',.0%'})
    fig.update_layout(height=len(series) * 300, title_text=title)
    fig.show()

    return fig


def load(forecast_summary, forecast_results):
    # Save data
    output_path = os.getcwd() + '/output/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    forecast_summary.to_csv(output_path + 'model_arima_forecast_summary.csv')
    forecast_results.to_csv(output_path + 'model_arima_forecast_results.csv')

    return


def execute(data_in, validation_steps=24, *argv):
    # The model_forecast parameters are supplied with argv

    forecast_summary, forecast_results = get_model_forecast_and_validation(data_in, validation_steps, *argv)

    load(forecast_summary, forecast_results)

    return forecast_summary, forecast_results
