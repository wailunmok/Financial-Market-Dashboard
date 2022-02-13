"""

Process data to Dash figures and tables

"""
import dash_table as dt
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Sign
import dash_core_components as dcc
import plotly.figure_factory as ff
from plotly.subplots import make_subplots


def create_dash_table(df):
    df_dash = df.reset_index(inplace=False)
    data_dash = df_dash.to_dict('records')
    columns = [{"name": i, "id": i, } for i in df_dash.columns]

    return dt.DataTable(data=data_dash, columns=columns)


def create_dash_table_percentage(df, scrolling=False):
    # Percentage format
    df_dash = df.reset_index(inplace=False)
    data_dash = df_dash.to_dict('records')
    #     columns   =  [{"name": i, "id": i,} for i in (df_dash.columns)]

    columns = []
    for i in df_dash.columns:
        if i != 'index':
            columns.append(
                {"name": i, "id": i, "type": 'numeric', "format": FormatTemplate.percentage(1).sign(Sign.positive)})
        else:
            columns.append({"name": i, "id": i})

    if scrolling:
        return dt.DataTable(data=data_dash, columns=columns, fixed_rows={'headers': True}, style_table={'height': 300})
    else:
        return dt.DataTable(data=data_dash, columns=columns)


def create_dash_figure(df, title):
    def get_plot_format(df):
        list_plot = []

        for col in df.columns:
            dic = {'x': df.index, 'y': df[col], 'type': 'line', 'name': col}
            list_plot.append(dic)
        return list_plot

    graph = dcc.Graph(
              id='example-graph',
              figure={'data': get_plot_format(df),
                      'layout': {'title': title}
                      }
              )
    return graph


def create_dash_forecast_figure(dict_fc_res, df_level):
    # Create forecast plots

    # Initialise
    n_cols = len(dict_fc_res)  # number of models
    n_rows = df_level.shape[1]  # number of time series
    subplot_titles = [ts + ' - ' + model for ts in df_level.columns for model in dict_fc_res.keys()]
    fig = make_subplots(rows=n_rows, cols=n_cols, subplot_titles=subplot_titles, vertical_spacing=0.02)

    # loop over models
    for c, (model, df_fc_ret) in enumerate(dict_fc_res.items()):
        # Calculate output
        first_index = df_fc_ret.index[df_fc_ret.index.get_loc(df_fc_ret.dropna().index[0]) - 1]

        # loop over time series
        for r, ts in enumerate(df_fc_ret.columns.levels[0]):

            # Alternative: plot returns with  df_fc_ts
            df_fc_ts = df_fc_ret.loc[:, (ts, slice(None))].dropna().droplevel(0, axis=1)

            # Check if forecast was correct
            correct = (((df_fc_ts['actual'] < 0) & (df_fc_ts['forecast'] < 0)) |
                       ((df_fc_ts['actual'] > 0) & (df_fc_ts['forecast'] > 0)))

            df_fc_price = df_fc_ts.copy()
            price_prev = df_level.loc[first_index:df_level.index[-2], ts].values
            df_fc_price = df_fc_price.apply(lambda x: (1 + x) * price_prev, axis=0)
            df_fc_price.loc[first_index, :] = df_level.loc[first_index, ts]
            df_fc_price.sort_index(inplace=True)

            df_plot = df_fc_price

            fig.add_scatter(x=df_plot.index, y=df_plot['actual'], name='actual', mode='lines',
                            line=dict(color='#1f77b4'), row=r + 1, col=c + 1)
            # fig.add_scatter(x=df_plot.index[1:], y=df_plot['forecast'][1:], name='forecast', mode='markers',
            #                 marker=dict(color='#2ca02c'), row=r + 1, col=c + 1)
            fig.add_scatter(x=df_plot.index[1:][correct], y=df_plot['forecast'][1:][correct], name='correct forecast',
                            mode='markers', marker=dict(color='#2ca02c'), row=r + 1, col=c + 1)
            fig.add_scatter(x=df_plot.index[1:][~correct], y=df_plot['forecast'][1:][~correct], name='wrong forecast',
                            mode='markers', marker=dict(color='#d62728', symbol='x'), row=r + 1, col=c + 1)
            fig.add_scatter(x=df_plot.index, y=df_plot['ci_lower'], name='95%-confidence interval', mode='lines',
                            line=dict(dash='dot', color='#7f7f7f'), row=r + 1, col=c + 1)
            fig.add_scatter(x=df_plot.index, y=df_plot['ci_upper'], name='95%-confidence interval', mode='lines',
                            line=dict(dash='dot', color='#7f7f7f'), row=r + 1, col=c + 1)

    # Legend: remove duplicate names
    names = set()
    fig.for_each_trace(
        lambda trace:
        trace.update(showlegend=False)
        if (trace.name in names) else names.add(trace.name))
    # fig.update_yaxes({'tickformat': ',.0%'})
    fig.update_layout(height=n_rows * 400, title_text="Price forecasts")

    graph = dcc.Graph(
              id='example-graph',
              figure=fig
              )

    return graph


def create_dash_density_figure(df, title):
    hist_data = [df[i].dropna().values for i in df.columns]
    group_labels = list(df.columns)
    fig = ff.create_distplot(hist_data, group_labels, show_hist=False)
    fig.update_layout(title_text=title)

    graph = dcc.Graph(
              id='example-graph',
              figure=fig
              )
    return graph


def dataframe_formatting(df, dic_formatting):
    # Convert dataframe rows to specified string format via "{}.format(x)"
    # Examples: {'integer': "{:.0f}", 'float': "{:.2f}", 'percentage': "{:.1%}, 'perc_sign': "{0:+.1%}",
    #            'string': "{}", 'EUR': "\u20ac {:.2f}"}
    # dict = {'column name': 'formatting'}
    df_out = df.copy()

    for k, v in dic_formatting.items():
        df_out.loc[k, :] = df_out.loc[k, :].apply(lambda x: v.format(x))
    return df_out
