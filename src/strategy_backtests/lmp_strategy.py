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
        "Strategy Backtest: Last Month Performance Strategy",
        "",
        "This program backtests a momentum-based tactical asset allocation strategy.",
        "",
        "Strategy Logic",
        "- Monthly rebalancing on the first day of each month",
        "- If IBOV outperformed CDI last month → Invest 100% in IBOV (stocks)",
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

start_date = get_start_date_input(1825)  # Limit to the last 5 years (1825 days)

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

# Calculate returns for the first month (missing previously)
cdi_month_opening = cdi_cumulative_daily_returns.resample("ME").first()
first_month_cdi_returns = (cdi_month_closing.iloc[0] - cdi_month_opening.iloc[0]) / cdi_month_opening.iloc[0]

#
# IBOV
#

# Download historical data for the Bovespa index (^BVSP)
ibov = yf.download("^BVSP", start=start_date, auto_adjust=True)["Close"]

# Convert the index to datetime and sort the data by date in ascending order for all DataFrames
ibov.index = pd.to_datetime(ibov.index)
ibov = ibov.sort_index(ascending=True)

ibov_month_closing = ibov.resample("ME").last()
ibov_returns = ibov.resample("ME").last().pct_change().dropna()

# Calculate returns for the first month (missing previously)
ibov_month_opening = ibov.resample("ME").first()
first_month_ibov_returns = (ibov_month_closing.iloc[0] - ibov_month_opening.iloc[0]) / ibov_month_opening.iloc[0]

#
# Model
#

returns = pd.DataFrame(columns=["CDI", "IBOV", "Last Month Perf. Strategy"], index=ibov_returns.index)
returns["CDI"] = cdi_returns
returns["IBOV"] = ibov_returns

choices = pd.DataFrame(columns=["Last Month Perf. Strategy"], index=ibov_returns.index)

for index, date in enumerate(ibov_returns.index):
    if index < len(ibov_returns.index):
        if index > 0:
            if ibov_returns.iloc[index - 1].item() > cdi_returns.iloc[index - 1].item():
                lm_returns = ibov_returns.iloc[index].item()
                lm_choice = "IBOV"
            else:
                lm_returns = cdi_returns.iloc[index].item()
                lm_choice = "CDI"
        else:
            if first_month_ibov_returns.item() > first_month_cdi_returns.item():
                lm_returns = ibov_returns.iloc[index].item()
                lm_choice = "IBOV"
            else:
                lm_returns = cdi_returns.iloc[index].item()
                lm_choice = "CDI"

        returns.loc[date, "Last Month Perf. Strategy"] = lm_returns
        choices.loc[date, "Last Month Perf. Strategy"] = lm_choice

cumulative_returns = (1 + returns).cumprod() - 1

#
# Graph
#

apply_mpl_style()

performance, axes = plt.subplots(figsize=(14, 8))

axes.plot(cumulative_returns["CDI"], label="CDI")
axes.plot(cumulative_returns["IBOV"], label="IBOV")
axes.plot(cumulative_returns["Last Month Perf. Strategy"], label="Last Month Perf. Strategy")

axes.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
plt.xlabel("Time")
plt.ylabel("Performance")
axes.set_title("Performance x Time")
plt.legend(title=f'LMP current investment: {choices["Last Month Perf. Strategy"].iloc[len(ibov_returns.index) - 1]}')

setup_mplcursors()


plt.show()
