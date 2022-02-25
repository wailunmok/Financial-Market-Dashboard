"""
Debugging script for testing dashboard functionality without Dash

"""

# Import libraries
from datetime import datetime
import os
import plotly.io as pio

# Import support libraries
import support.data_processing as data_proc
import support.data_exploration as data_expl
import support.model_arima as model_arima
import support.model_benchmark as model_benchmark
import support.model_prophet as model_prophet

# Show plotly plots in browser
pio.renderers.default = "browser"


def log(message):
    timestamp_format = '%Y-%m-%d %H:%M:%S'
    now = datetime.now()
    timestamp = now.strftime(timestamp_format)
    print(f'{timestamp}: {message}')
    with open('output/logfile.txt', 'a') as f: f.write(f'{timestamp}: {message}\n')


def main():
    # Initialise output path
    output_path = os.getcwd() + '/output/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    log('Job started...')
    start_date = datetime(2000, 1, 1)
    freq = 'BM'  # options: ['B', 'W-Fri', 'BM', 'BY']
    validation_steps = 12 #15*12
    order = (1, 0, 0)  # ARIMA order
    buy_positive = True  # Benchmark strategy: buy on positive or negative previous return

    # Load and transform data
    log('Data processing started...')
    data = data_proc.execute(start_date=start_date)

    # Data exploration
    log('Data exploration started...')
    stats, returns = data_expl.execute(data, freq=freq)

    # Train model
    log('Model training started...')
    data_in = data_proc.get_data_slice(data, freq, 'return')
    fc_benchmark_smry, fc_benchmark_res = model_benchmark.execute(data_in, validation_steps, buy_positive)
    log('Model training started ARMA...')
    fc_arima_smry, fc_arima_res = model_arima.execute(data_in, validation_steps, order)
    log('Model training started Prophet...')
    fc_prophet_smry, fc_prophet_res = model_prophet.execute(data_in, validation_steps)


    # Example figures
    dict_fig = {'benchmark': fc_benchmark_res, 'arima': fc_arima_res, 'prophet': fc_prophet_res}
    data_level = data_proc.get_data_slice(data, freq, 'level')
    for k, v in dict_fig.items():
        # fig = model_arima.plot_validation(v, k + ' forecast')  # return
        fig = model_arima.plot_validation(v, k + ' forecast', data_level)  # level
        fig.write_html(output_path + f'model_{k}_forecast_plot.html')

    # Print output
    print(stats)
    print(returns)
    print(fc_arima_smry)
    print(fc_prophet_smry)
    log('Job Finished')


if __name__ == "__main__":
    main()
