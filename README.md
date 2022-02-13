# Financial Market Dashboard
A visualisation tool for financial market data from [Yahoo finance](https://finance.yahoo.com/lookup) including data exploration and model forecasting. 
This dashboard is a Python Dash app that is deployed via docker.

Screenshot of the dashboard:
![Screenshot](screenshot.png)

## Installation
Build and run the docker image with the following commands:
```
docker-compose build
docker compose up
```
The dashboard can be accessed in the browser via `http://localhost:5050` 


### Dependencies
* Docker Desktop or Docker Engine


## Description

### Data input
In this section the tickers from [Yahoo finance](https://finance.yahoo.com/lookup), the start date, end date and the data frequency can be specified.

### Data exploration
This section shows multiple figures (price, index, return, density) and a summary of the returns and statistics for the time series.   

### Model forecasting 
This section performs a one-step-ahead forecast from the selected models. 
The models are validated by measuring the one-step-ahead forecast accuracy over a historic period, i.e., the number of validation steps. The following validation metrics are defined:

* accuracy: the percentage of correctly forecasting an increase or a decrease in the price. 
* payout_from_100: the payout for following the model strategy* with 100 EUR (excl. transaction fees and difference bid-ask spread)

_*Buy if a price increase is forecasted, sell if a price decrease is forecasted._



## Next steps
Implement more models, e.g., Copula's, LSTM (recurrent neural network), Prophet (additive trend/seasonality model).


