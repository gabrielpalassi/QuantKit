from datetime import date
from bcb import sgs
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import sys
import os

# Add the src directory to the path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import configure_yfinance_logging, get_start_date_input, apply_mpl_style, setup_mplcursors, print_with_separator

#
# Overview
#

print_with_separator(
    [
        "Strategy Backtest: Moving Average Strategy",
        "",
        "This program backtests a technical analysis-based tactical asset allocation strategy.",
        "",
        "Strategy Logic",
        "- Monthly rebalancing on the first day of each month",
        "- If last month's IBOV closing price > Moving Average → Invest 100% in IBOV (stocks)",
        "- Otherwise → Invest 100% in CDI (fixed income)",
        "Assets",
        "- CDI: Brazil's benchmark fixed income rate",
        "- IBOV: Ibovespa stock market index (B3 exchange)",
        "Output",
        "- Cumulative returns comparison: Strategy vs. Buy-and-Hold",
    ]
)

#
# Inputs
#

configure_yfinance_logging()


def validate_ma(input_ma):
    try:
        ma = int(input_ma)
        if ma > 0:
            return True
    except:
        return False


start_date = get_start_date_input(1825)  # Limit to the last 5 years (1825 days)

ma_months = None
while ma_months is None:
    ma_months = input("Specify the number of months for the moving average: ")
    if validate_ma(ma_months):
        ma_months = int(ma_months)
    else:
        print("Invalid input. Please enter a positive integer for the moving average.")
        ma_months = None

#
# CDI
#

# Fetch historical CDI data
cdi_data = sgs.get({"CDI": 11}, start=start_date)
cdi_data = cdi_data["CDI"]

# Convert CDI rates to decimal form (dividing by 100)
cdi_daily_returns = cdi_data / 100


cdi_cumulative_daily_returns = (1 + cdi_daily_returns).cumprod()
cdi_month_closing = cdi_cumulative_daily_returns.resample("ME").last()
cdi_returns = cdi_cumulative_daily_returns.resample("ME").last().pct_change().dropna()

# Calculate returns for the first month (missing with the previous method)
cdi_month_opening = cdi_cumulative_daily_returns.resample("ME").first()
first_month_cdi_returns = (cdi_month_closing.iloc[0] - cdi_month_opening.iloc[0]) / cdi_month_opening.iloc[0]

#
# IBOV
#

# Download historical data for the Bovespa index (^BVSP)
ibov = yf.download("^BVSP", start=start_date, auto_adjust=True)["Close"]

# Calculate moving averages
ibov_ma = ibov.rolling(window=ma_months * 21).mean()  # Average of 21 working days / month

# Convert the index to datetime and sort the data by date in ascending order for all DataFrames
ibov.index = pd.to_datetime(ibov.index)
ibov = ibov.sort_index(ascending=True)
ibov_ma.index = pd.to_datetime(ibov_ma.index)
ibov_ma = ibov_ma.sort_index(ascending=True)

ibov_month_closing = ibov.resample("ME").last()
ibov_ma_month_closing = ibov_ma.resample("ME").last()
ibov_returns = ibov.resample("ME").last().pct_change().dropna()

# Calculate returns for the first month (missing previously)
ibov_month_opening = ibov.resample("ME").first()
first_month_ibov_returns = (ibov_month_closing.iloc[0] - ibov_month_opening.iloc[0]) / ibov_month_opening.iloc[0]

#
# Model
#

returns = pd.DataFrame(columns=["CDI", "IBOV", "Moving Average Strategy"], index=ibov_returns.index)
returns["CDI"] = cdi_returns
returns["IBOV"] = ibov_returns

choices = pd.DataFrame(columns=["Moving Average Strategy"], index=ibov_returns.index)

for index, date in enumerate(ibov_returns.index):
    if index < len(ibov_returns.index):
        if index > ma_months - 1:
            if ibov_month_closing.iloc[index].item() > ibov_ma_month_closing.iloc[index].item():
                ma_returns = ibov_returns.iloc[index].item()
                ma_choice = "IBOV"
            else:
                ma_returns = cdi_returns.iloc[index].item()
                ma_choice = "CDI"
        else:
            # For the first months, determine the 'Moving Average Strategy' as the CDI because of lack of data
            ma_returns = cdi_returns.iloc[index].item()
            ma_choice = "CDI"

        returns.loc[date, "Moving Average Strategy"] = ma_returns
        choices.loc[date, "Moving Average Strategy"] = ma_choice

cumulative_returns = (1 + returns).cumprod() - 1

#
# Graph
#

apply_mpl_style()

performance, axes = plt.subplots(figsize=(14, 8))

axes.plot(cumulative_returns["CDI"], label="CDI")
axes.plot(cumulative_returns["IBOV"], label="IBOV")
axes.plot(cumulative_returns["Moving Average Strategy"], label="Moving Average Strategy")

axes.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
plt.xlabel("Time")
plt.ylabel("Performance")
axes.set_title("Performance x Time")
plt.legend(title=f'MA current investment: {choices["Moving Average Strategy"].iloc[len(ibov_returns.index) - 1]}')

setup_mplcursors()


plt.show()
