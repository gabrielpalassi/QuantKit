import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import pandas as pd
from datetime import date
import sys
import os

# Add the src directory to the path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import (
    configure_yfinance_logging,
    get_start_date_input,
    fetch_asset_ticker_input,
    get_portfolio_weights,
    setup_mplcursors,
    apply_mpl_style,
    print_with_separator,
)

#
# Overview
#

print_with_separator(
    [
        "Portfolio Backtest",
        "",
        "This program backtests a weighted portfolio to evaluate historical performance.",
        "",
        "Analysis",
        "- Calculates cumulative returns for the entire portfolio",
        "- Shows individual asset performance for comparison",
        "Output",
        "- Interactive cumulative returns chart",
        "- Portfolio performance vs. individual assets",
    ]
)

#
# Inputs
#

configure_yfinance_logging()

start_date = get_start_date_input()

assets = fetch_asset_ticker_input(start_date)

asset_weights = get_portfolio_weights(assets)

#
# Calculate Cumulative Returns
#

# Find the date when all assets are available
earliest_common_date = max([data.index.min() for data in assets.values()])

# Filter all assets to start from the earliest common date
filtered_assets = {ticker: data[data.index >= earliest_common_date] for ticker, data in assets.items()}

# Align all assets data by reindexing them to the same dates
all_dates = pd.date_range(start=earliest_common_date, end=date.today())
aligned_assets = {ticker: data.reindex(all_dates).ffill() for ticker, data in filtered_assets.items()}

# Calculate cumulative returns for each asset
asset_cumulative_returns = {}
for ticker, data in aligned_assets.items():
    # Calculate daily returns
    daily_returns = data.pct_change().fillna(0)
    # Calculate cumulative returns
    asset_cumulative_returns[ticker] = (1 + daily_returns).cumprod() - 1

# Calculate cumulative returns for the portfolio
portfolio_returns = sum([data[ticker].pct_change().fillna(0) * (asset_weights[ticker] / 100) for ticker, data in aligned_assets.items()])
cumulative_portfolio_returns = (1 + portfolio_returns).cumprod() - 1

#
# Graph
#

apply_mpl_style()

# Plot the cumulative returns
plt.figure(figsize=(14, 8))

# Plot portfolio cumulative returns
plt.plot(cumulative_portfolio_returns.index, cumulative_portfolio_returns, label="Portfolio", linewidth=2)

# Plot cumulative returns for each asset
for ticker, cum_returns in asset_cumulative_returns.items():
    plt.plot(cum_returns.index, cum_returns, label=f"{ticker}", alpha=0.3)

plt.xlabel("Date")
plt.ylabel("Returns")
plt.title("Portfolio and Asset Cumulative Returns Over Time")
plt.legend()

# Format y-axis tick labels as percentages
plt.gca().yaxis.set_major_formatter(mplticker.PercentFormatter(1.0))

setup_mplcursors()

# Show the plot
plt.show()
