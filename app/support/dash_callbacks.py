# Import dash libraries
from dash.dependencies import Input, Output, State

# Import app
from app import app

# Import libraries
import pandas as pd

# import user libraries
import support.data_processing as data_proc
import support.data_exploration as data_expl
import support.dash_processing as dash_proc
import support.model_arima as model_arima
import support.model_benchmark as model_benchmark

pd.options.mode.chained_assignment = None

""" Callbacks
See https://dash.plotly.com/basic-callbacks
"""


# Callback: Gather data from Yahoo Finance
@app.callback(
    [Output('intermediate-value', 'children'),
     Output(component_id='output-loading', component_property='children')
     ],
    [Input('button-update_data', 'n_clicks'),  # Only update on click
     State(component_id='input1', component_property='value'),
     State(component_id='input2', component_property='value'),
     State(component_id='input3', component_property='value'),
     State(component_id='input4', component_property='value'),
     State(component_id='input5', component_property='value'),
     State(component_id='input6', component_property='value'),
     State('my-date-picker-range', 'start_date'),
     State('my-date-picker-range', 'end_date'),
     State('radioitems-input_market', 'value')])
def get_data(n_clicks, input1, input2, input3, input4, input5, input6, start_date, end_date, market_indices):
    # Initialise
    index_list = [input1, input2, input3, input4, input5, input6]

    # Market indices: AEX, DAX, STOXX, S&P, Dow Jones, Nikkei, Shanghai
    index_market = ['^AEX', '^GDAXI', '^STOXX', '^GSPC', '^DJI']
    if market_indices:
        index_list += index_market

    # Remove empty and duplicates
    index_list = list(dict.fromkeys(index_list))
    index_list = [i for i in index_list if i != '']

    #  Debug print
    print(f"Data update clicked {n_clicks} times.")
    print(index_list)

    # Load data
    data = data_proc.execute(index=index_list, start_date=start_date, end_date=end_date)

    # dump to json
    return data.to_json(date_unit='ns'), ''


# Callback: Data exploration tables and figures
@app.callback(
          [Output(component_id='output-table_summary', component_property='children'),
           Output(component_id='output-table_returns', component_property='children'),
           Output(component_id='output-graph1', component_property='children'),
           Output(component_id='output-graph2', component_property='children'),
           Output(component_id='output-graph3', component_property='children'),
           Output(component_id='output-graph4', component_property='children')
           ],
          [Input('intermediate-value', 'children'),
           State('radioitems-frequency', 'value')])
def update_graphs(json_data, freq):
    # Get data and restructure multi index
    data = pd.read_json(json_data)
    multi_idx = pd.MultiIndex.from_tuples([eval(i) for i in data.columns], names=['freq', 'type', 'index'])
    data.columns = multi_idx

    # Run data exploration
    stats, returns = data_expl.execute(data, freq=freq)
    stats.columns = stats.columns.droplevel([0, 1])

    # Create tables
    data_level = data_proc.get_data_slice(data, freq, 'level')
    data_index = (data_level / data_level.apply(lambda x: x.dropna()[0], axis=0)) * 100
    data_ret = data_proc.get_data_slice(data, freq, 'return')

    stats = dash_proc.dataframe_formatting(stats, {'count': "{:.0f}"})  # dash table formatting
    # stats.loc['count', ] = stats.loc['count', ].astype(int).astype(str)
    table1 = dash_proc.create_dash_table_percentage(stats, scrolling=True)
    table2 = dash_proc.create_dash_table_percentage(returns, scrolling=True)

    graph1 = dash_proc.create_dash_figure(data_level, 'Price')
    graph2 = dash_proc.create_dash_figure(data_index, 'Index=100')
    graph3 = dash_proc.create_dash_figure(data_ret, 'Return')
    graph4 = dash_proc.create_dash_density_figure(data_ret, 'Density of returns')

    # Create tables and figures
    return table1, table2, graph1, graph2, graph3, graph4


# Callback: Train model and forecast
@app.callback(
          [Output(component_id='output-results_forecast', component_property='children'),
           Output(component_id='output-graph_forecast', component_property='children')],
          [Input('button-forecast', 'n_clicks'),  # Only update on click
           State('intermediate-value', 'children'),
           State('radioitems-frequency', 'value'),
           State('checklist-models', 'value'),
           State('input7', 'value'),
           State('input8', 'value'),
           State('input9', 'value')])
def train_forecast_model(n_clicks, json_data, freq, models, arma_p, arma_q, val_steps):
    #  Debug print
    print(f"Forecast clicked {n_clicks} times.")
    print(models)

    if not n_clicks:
        return 'Forecast not started yet.', ''
    elif not models:
        return 'Select at least one forecast model.', ''
    else:
        # Get data and restructure multi index
        data = pd.read_json(json_data)
        multi_idx = pd.MultiIndex.from_tuples([eval(i) for i in data.columns], names=['freq', 'type', 'index'])
        data.columns = multi_idx

        # get returns
        data_ret = data_proc.get_data_slice(data, freq, 'return')

        # Loop over models
        dict_fc_summary, dict_fc_res = dict(), dict()
        for model in models:
            if model == 'Benchmark-positive':
                dict_fc_summary[model], dict_fc_res[model] = model_benchmark.execute(data_ret, val_steps, True)
            elif model == 'Benchmark-negative':
                dict_fc_summary[model], dict_fc_res[model] = model_benchmark.execute(data_ret, val_steps, False)
            elif model == 'ARMA':
                model = f'ARMA({arma_p},{arma_q})'
                arima_order = (arma_p, 0, arma_q)
                dict_fc_summary[model], dict_fc_res[model] = model_arima.execute(data_ret, val_steps, arima_order)

        # Forecast results summary
        dict_fm = {'invest': "{}", 'accuracy': "{:.1%}", 'payout_from_100': "\u20ac {:.2f}"}
        for k, v in dict_fc_summary.items():
            v = v.drop('validation_steps')
            dict_fc_summary[k] = dash_proc.dataframe_formatting(v, dict_fm)
        df_forecast_all = pd.concat(dict_fc_summary).reset_index(level=1).rename({'level_1': 'metric'}, axis=1)

        table1 = dash_proc.create_dash_table_percentage(df_forecast_all, scrolling=True)

        # Forecast figure
        data_level = data_proc.get_data_slice(data, freq, 'level')
        graph1 = dash_proc.create_dash_forecast_figure(dict_fc_res, data_level)

        return table1, graph1
