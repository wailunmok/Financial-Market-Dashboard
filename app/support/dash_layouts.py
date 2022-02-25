import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from datetime import datetime

""" Layouts
See: https://dash-bootstrap-components.opensource.faculty.ai/docs/components/layout/
"""

""" Specify Dash objects """
# Data input
input_date = dcc.DatePickerRange(
    id='my-date-picker-range',
    min_date_allowed=datetime(1950, 1, 1),
    max_date_allowed=datetime.now(),
    initial_visible_month=datetime.now(),
    start_date=datetime(2020, 1, 1),
    end_date=datetime.now()
)
radio_items_frequency = dbc.RadioItems(
    options=[
        {"label": "Daily", "value": 'B'},
        {"label": "Weekly", "value": 'W-Fri'},
        {"label": "Monthly", "value": 'BM'},
        {"label": "Yearly", "value": 'BY'},

    ],
    value='BM',
    id="radioitems-frequency",
    inline=True
)
radio_items_market = dbc.RadioItems(
    options=[
        {"label": "Yes", "value": True},
        {"label": "No", "value": False},
    ],
    value=True,
    id="radioitems-input_market",
    inline=True
)
button_update = dbc.Button(
    "Update data", id="button-update_data", color="primary", className="me-1", n_clicks=0
)
loading_update = dbc.Spinner(
    html.Div(id="output-loading"), color="primary"
)

# Model forecasting
button_forecast = dbc.Button(
    "Forecast model", id="button-forecast", color="primary", className="me-1", n_clicks=0
)
results_forecast = dbc.Spinner(
    html.Div(id="output-results_forecast"), color="primary"
)
checklist_models = dbc.Checklist(
    options=[
        {"label": "Benchmark - buy if positive", "value": "Benchmark-positive"},
        {"label": "Benchmark - buy if negative", "value": "Benchmark-negative"},
        {"label": "ARMA(p,q)", "value": "ARMA"},
    ],
    id="checklist-models"
    # inline=True
)
input_arma = dbc.Row([
    dbc.Col(dbc.Input(id='input7', value=1, type='number', min=0, max=10, step=1), width='auto'),
    dbc.Col(dbc.Input(id='input8', value=0, type='number', min=0, max=10, step=1), width='auto')
], no_gutters=True
)
input_val_steps = dbc.Row([
    dbc.Col(dbc.Input(id='input9', value=12, type='number', min=1, max=1000, step=1), width='auto')
], no_gutters=True
)

""" Specify row items """
# Data input
row_ticker_info = dbc.Row(
    [
        dbc.Col(html.Div("Enter tickers from"), width='auto', style={"margin-left": "10px", "margin-right": "10px"}),
        dbc.Col(html.Div([html.A('Yahoo finance',
                                 href='https://finance.yahoo.com/lookup', target='_blank')]), width='auto'),
        dbc.Col(html.Div(":"), width='auto', style={'textAlign': 'left', "margin-right": "15px"})
    ],
    no_gutters=True, justify="start"
)
row_ticker_input = dbc.Row([
    dbc.Col(dbc.Input(id='input1', value='AGN.AS', type='text'), width=1, style={"margin-left": "10px"}),
    dbc.Col(dbc.Input(id='input2', value='ASRNL.AS', type='text'), width=1),
    dbc.Col(dbc.Input(id='input3', value='NN.AS', type='text'), width=1),
    dbc.Col(dbc.Input(id='input4', value='', type='text'), width=1),
    dbc.Col(dbc.Input(id='input5', value='', type='text'), width=1),
    dbc.Col(dbc.Input(id='input6', value='', type='text'), width=1),
], no_gutters=True
)
row_data_settings = dbc.Row([
    dbc.Col(html.Div("Date: "), width="auto", style={"margin-right": "10px", "margin": "10px"}),
    dbc.Col(input_date, width="auto", style={"margin": "10px"}),
    dbc.Col(html.Div("Frequency:"), width="auto", style={'textAlign': 'right', "margin-right": "10px",
                                                         "margin-left": "30px"}),
    dbc.Col(radio_items_frequency, width="auto"),
    dbc.Col(html.Div("Market indices:"), width="auto", style={'textAlign': 'right', "margin-right": "10px",
                                                              "margin-left": "30px"}),
    dbc.Col(radio_items_market, width="auto", style={'textAlign': 'right', "margin-right": "15px"})
],
    no_gutters=True, justify="start", align="center"
)
row_update_data = dbc.Row([
    dbc.Col(button_update, width='auto', style={"margin": "10px"}),
    dbc.Col(loading_update, width=1)
],
    no_gutters=True, justify="start", align="center"
)

# Data exploration
row_figures = html.Div([
    dbc.Row([
        dbc.Col(html.Div(id='output-graph1'), width=6),
        dbc.Col(html.Div(id='output-graph2'), width=6),
    ]),
    dbc.Row([
        dbc.Col(html.Div(id='output-graph3'), width=6),
        dbc.Col(html.Div(id='output-graph4'), width=6)
    ])
])
row_tables = html.Div([
    dbc.Row([
        dbc.Col(html.Div("Summary returns: "), width=1, style={"margin": "10px"}),
        dbc.Col(html.Div(id="output-table_returns"), width=10)
    ], no_gutters=False, justify="start"),
    dbc.Row([
        dbc.Col(html.Div("Summary statistics: "), width=1, style={"margin": "10px"}),
        dbc.Col(html.Div(id="output-table_summary"), width=10)
    ], no_gutters=False, justify="start")
])

# Model forecasting
row_forecast_settings = dbc.Row([
    dbc.Col(html.Div("Steps for validation:"), width="auto", style={"margin": "10px"}, align="top"),
    dbc.Col(input_val_steps, width="auto", align="top"),
    dbc.Col(html.Div("Models:"), width="auto", style={"textAlign": "right", "margin": "10px", "margin-left": "60px"}),
    dbc.Col(checklist_models, width="auto", style={"margin": "10px"}),
    dbc.Col(html.Div("(p,q)="), width="auto", style={"textAlign": "right", "margin": "10px"}, align="end"),
    dbc.Col(input_arma, width="auto", align="end"),
],
    no_gutters=True, justify="start", align="center"
)
row_update_forecast = dbc.Row([
    dbc.Col(button_forecast, width="auto", style={"margin": "10px"})
],
    no_gutters=True, justify="start", align="center"
)
row_forecast_tables = dbc.Row([
    dbc.Col(html.Div("Summary forecast: "), width=1, style={"margin": "10px"}),
    dbc.Col(results_forecast, width=10, style={"margin": "10px"})
], no_gutters=False, justify="start",
)
row_forecast_figures = html.Div([
    dbc.Row([
        dbc.Col(html.Div(id='output-graph_forecast'), width=12)
    ])
])

# Titles and lines
row_line = dbc.Row([
    html.Hr(style={'borderWidth': ".3vh", "width": "100%", "borderColor": "#1f77b4", "opacity": "unset"})
])


def row_title(title):
    row = dbc.Row([
        dbc.Col(html.H1(title, style={'color': 'white', "font-weight": "bold"}),
                width=4, style={"textAlign": "center"}),
        dbc.Col(html.Div([html.A('Git repository',
                                 href='https://github.com/wailunmok/Financial-Market-Dashboard',
                                 target='_blank',  style={'color': 'white', "font-weight": "bold"})]),
                width=4, style={"textAlign": "right", "margin": "10px"}, align="end")
    ],
        no_gutters=True, justify="end", align="center", style={'backgroundColor': '#1f77b4'}
    )
    return row


def row_subtitle(title):
    row = dbc.Row([
        html.H3(title)
    ],
        no_gutters=True, justify="start", align="center"
    )
    return row


# Specify start layout
start_layout = html.Div(children=[
    row_title('Financial Market Dashboard'),

    row_subtitle('Data input'),
    row_ticker_info,
    row_ticker_input,
    row_data_settings,
    row_update_data,
    row_line,

    row_subtitle('Data exploration'),
    row_figures,
    row_tables,
    row_line,

    row_subtitle('Model forecasting'),
    row_forecast_settings,
    row_update_forecast,
    row_forecast_tables,
    row_forecast_figures,

    # Hidden div inside the app that stores the intermediate value
    html.Div(id='intermediate-value', style={'display': 'none'})
])
