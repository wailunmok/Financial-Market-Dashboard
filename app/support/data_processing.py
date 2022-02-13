""" Library for data processing """
import os
import pandas_datareader.data as web
from datetime import datetime
import numpy as np
import pandas as pd


def extract(indexlist, start, end):
    # Yahoo finance data contains weekday data with some missing values
    index_download = web.DataReader(indexlist, data_source='yahoo', start=start, end=end)
    df_prices = index_download['Adj Close']
    df_prices = df_prices.dropna(how='all', axis=0).dropna(how='all', axis=1)
    return df_prices


def transform(data, freq='D'):
    # Calculate returns for multiple frequencies
    # See https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
    # freq: B=business day frequency, W-Fri=weekly frequency Friday,
    # BM=business month end frequency, BY=business year frequency
    freq = ['B', 'W-Fri', 'BM', 'BY']

    # Specify frequency as 'business day frequency' and add missing dates
    data = data.groupby(pd.Grouper(freq='B')).last()

    # Replace missing value with preceding value
    data = data.fillna(method='ffill')

    # Create output dataframe
    multi_idx = pd.MultiIndex.from_product([freq, ('level', 'return'), data.columns], names=['freq', 'type', 'index'])
    data_out = pd.DataFrame(index=data.index, columns=multi_idx)

    # Loop over frequency
    for f in freq:
        data_tmp = data.groupby(pd.Grouper(freq=f)).last()
        # Drop last row if current date is not equal to the last business date
        if data.index[-1] != data_tmp.index[-1]:
            data_tmp = data_tmp.iloc[:-1, ]

        data_out.loc[data_tmp.index, (f, 'level', slice(None))] = data_tmp.values
        data_out.loc[data_tmp.index, (f, 'return', slice(None))] = data_tmp.pct_change().values

    data_out = data_out.astype(float)

    return data_out


def load(data):
    # Save data
    output_path = os.getcwd() + '/output/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    data.to_csv(output_path + 'cleaned_data.csv')
    return data


def get_data_slice(data, freq, type):
    # Support function: specify frequency, type and drop multi index
    data_out = data.loc[:, (freq, type, slice(None))].dropna(how='all', axis=0).dropna(how='all', axis=1)
    data_out = data_out.asfreq(freq)
    data_out.columns = data_out.columns.droplevel([0, 1])

    return data_out


def execute(index=None, start_date=None, end_date=None):
    # Check if optional parameters are supplied
    index = ['^AEX', '^GDAXI', '^STOXX', '^GSPC', '^DJI'] if isinstance(index, type(None)) else index
    start_date = datetime(2020, 1, 1) if isinstance(start_date, type(None)) else start_date
    end_date = datetime.now() if isinstance(end_date, type(None)) else end_date

    data = load(transform(extract(index, start_date, end_date)))

    return data
