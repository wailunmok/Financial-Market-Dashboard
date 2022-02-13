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
    validation_steps = 24
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
    fc_arima_smry, fc_arima_res = model_arima.execute(data_in, validation_steps, order)
    fc_benchmark_smry, fc_benchmark_res = model_benchmark.execute(data_in, validation_steps, buy_positive)

    # Example figure
    fig = model_arima.plot_validation(fc_arima_res, 'ARMA forecast')
    fig.show()

    # Print output
    print(stats)
    print(returns)
    print(fc_arima_smry)
    log('Job Finished')


if __name__ == "__main__":
    main()
