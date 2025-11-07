import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import pandas as pd
import sys
import os

# Add the src directory to the path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import (
    configure_yfinance_logging,
    get_start_date_input,
    get_asset_tickers_input,
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
        "Drawdown Analysis",
        "",
        "This program calculates and visualizes portfolio risk through drawdown analysis.",
        "",
        "Analysis Options",
        "- Individual Assets: Analyze drawdown for each asset separately",
        "- Portfolio: Analyze weighted portfolio drawdown",
        "Output",
        "- Interactive drawdown charts over time",
        "- Maximum drawdown value for each asset/portfolio",
    ]
)

#
# Inputs
#

configure_yfinance_logging()

start_date = get_start_date_input()

drawdown_type = input("Do you want the drawdown of individual assets or of the portfolio? (assets/portfolio): ")
while drawdown_type not in ["assets", "portfolio"]:
    drawdown_type = input('Invalid input. Please enter "assets" or "portfolio": ')

assets = get_asset_tickers_input(start_date)

# If calculating VaR for a portfolio, gather asset weights
asset_weights = {}
if drawdown_type == "portfolio":
    asset_weights = get_portfolio_weights(assets)

#
# Drawdown
#

# Calculate the maximum drawdown for each asset and store the results in a dictionary
max_drawdowns = {}
for ticker, asset_data in assets.items():
    asset_data_max = asset_data.cummax()
    drawdowns = (asset_data - asset_data_max) / asset_data_max
    drawdown_max = drawdowns.min()
    max_drawdowns[ticker] = drawdown_max

# Calculate the maximum drawdown of the portfolio if portfolio was selected
if drawdown_type == "portfolio":
    combined_asset_data = None
    for ticker, asset_data in assets.items():
        weighted_asset_data = asset_data[ticker] * asset_weights[ticker]
        if combined_asset_data is None:
            combined_asset_data = weighted_asset_data
        else:
            combined_asset_data += weighted_asset_data

    combined_asset_data_max = combined_asset_data.cummax()
    combined_portfolio_drawdowns = (combined_asset_data - combined_asset_data_max) / combined_asset_data_max
    max_drawdowns["Portfolio"] = pd.Series(combined_portfolio_drawdowns.min())

#
# Graph
#

apply_mpl_style()

drawdown, axes = plt.subplots(figsize=(14, 8))

if drawdown_type == "assets":
    for ticker, asset_data in assets.items():
        drawdowns = (asset_data - asset_data.cummax()) / asset_data.cummax()
        axes.plot(drawdowns, label=ticker)
elif drawdown_type == "portfolio":
    axes.plot(combined_portfolio_drawdowns, label="Portfolio")

axes.yaxis.set_major_formatter(mplticker.PercentFormatter(1.0))
plt.xlabel("Time")
plt.ylabel("Drawdown")
axes.set_title("Drawdown x Time")

legend_text = "\n".join([f"{ticker}: {float(max_drawdown.iloc[0]):.2%}" for ticker, max_drawdown in max_drawdowns.items()]) + "\n"
plt.legend(title=f"Max. Drawdowns:\n\n{legend_text}")

setup_mplcursors()

plt.show()
