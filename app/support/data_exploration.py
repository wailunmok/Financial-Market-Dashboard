""" Library for data exploration """
import os
import pandas as pd
import statsmodels.tsa.stattools as tsa
import statsmodels.api as sm
from dateutil.relativedelta import relativedelta


def get_statistics(data):
    significance = 0.05
    stats = data.describe(percentiles=[0.005, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 0.995])
    stats.loc['skew', :] = data.skew()
    stats.loc['kurt', :] = data.kurt()
    stats.loc['sharpe_ratio', :] = stats.loc['mean', :] / stats.loc['std', :]

    acf_lags = 4
    for i in range(1, acf_lags + 1):
        stats.loc[f'acf_{i}', :] = data.apply(lambda x: tsa.acf(x.dropna(), nlags=i)[-1])

    # JB test for normality: H_0 = normal
    stats.loc['normality', :] = data.apply(lambda x: tsa.stats.jarque_bera(x)[1] > significance)

    # LB test for autocorrelation: H_0 = no autocorrelation
    stats.loc['autocorrelation', :] = data.apply(
        lambda x: sm.stats.acorr_ljungbox(x.dropna(), lags=acf_lags).iloc[-1, -1] < significance)

    # ADF test for stationarity: H_0 = non-stationary (unit root)
    stats.loc['stationary', :] = data.apply(lambda x: tsa.adfuller(x.dropna(), regression='c')[1] < significance)
    stats.loc['trend_stationary', :] = data.apply(lambda x: tsa.adfuller(x.dropna(), regression='ct')[1] < significance)

    return stats


def get_return_summary(data):
    # Calculate returns of periods: YTD, 1M, 2M, 3M, 6M, 1Y, 2Y, ...
    def nearest_date(items, pivot):
        return min(items, key=lambda x: abs(x - pivot))

    # Initialise
    dates = data.index
    oldest_date, current_date = dates[[0, -1]]
    max_years = (current_date - oldest_date).days / 365  # Act/365

    # Determine dates per term
    dict_terms = dict()
    dict_terms['YTD'] = nearest_date(dates, current_date.replace(month=1, day=1))  # datetime(end_date.year,1,1)
    if max_years > 0.25:
        dict_terms['1M'] = nearest_date(dates, current_date - relativedelta(months=1))
        dict_terms['3M'] = nearest_date(dates, current_date - relativedelta(months=3))
    if max_years > 0.5:
        dict_terms['6M'] = nearest_date(dates, current_date - relativedelta(months=6))
    for i in range(int(max_years)):
        i += 1
        dict_terms[str(i) + 'Y'] = nearest_date(dates, current_date - relativedelta(years=i))

    # Calculate cumulative and annualised return
    data_tmp = data.loc[:, ('B', 'level', slice(None))]
    data_tmp.columns = data_tmp.columns.droplevel([0, 1])
    returns = pd.DataFrame(index=dict_terms.keys(), columns=data_tmp.columns)
    for k, v in dict_terms.items():
        returns.loc[k, :] = data_tmp.loc[current_date, ] / data_tmp.loc[v, ] - 1
        # Add annualised return
        if k[-1] == 'Y':
            returns.loc[k + ' (ann)', :] = (1 + returns.loc[k, ]) ** (1 / int(k[:-1])) - 1

    return returns


def load(stats, returns):
    # Save data
    output_path = os.getcwd() + '/output/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    stats.to_csv(output_path + 'data_statistics.csv')
    returns.to_csv(output_path + 'data_returns.csv')

    return


def execute(data, freq='W-Fri'):
    data_in = data.loc[:, (freq, 'return', slice(None))].dropna(how='all', axis=0).dropna(how='all', axis=1)
    stats = get_statistics(data_in)
    returns = get_return_summary(data)
    load(stats, returns)

    return stats, returns
