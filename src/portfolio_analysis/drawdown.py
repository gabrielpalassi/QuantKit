#
# Imports
#

import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import sys
import os

# Local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from portfolio_analysis.utils import drawdown_series, price_series, weighted_portfolio_prices
from utils import (
    configure_yfinance_logging,
    get_start_date_input,
    fetch_asset_ticker_input,
    get_portfolio_weights,
    setup_mplcursors,
    apply_mpl_style,
    print_with_separator,
)


def main() -> None:
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

    assets = fetch_asset_ticker_input(start_date)

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
        asset_drawdowns = drawdown_series(price_series(asset_data, ticker))
        max_drawdowns[ticker] = asset_drawdowns.min()

    # Calculate the maximum drawdown of the portfolio if portfolio was selected
    if drawdown_type == "portfolio":
        combined_asset_data = weighted_portfolio_prices(assets, asset_weights)
        combined_portfolio_drawdowns = drawdown_series(combined_asset_data)
        max_drawdowns["Portfolio"] = combined_portfolio_drawdowns.min()

    #
    # Graph
    #

    apply_mpl_style()

    _, axes = plt.subplots(figsize=(14, 8))

    if drawdown_type == "assets":
        for ticker, asset_data in assets.items():
            axes.plot(drawdown_series(price_series(asset_data, ticker)), label=ticker)
    elif drawdown_type == "portfolio":
        axes.plot(combined_portfolio_drawdowns, label="Portfolio")

    axes.yaxis.set_major_formatter(mplticker.PercentFormatter(1.0))
    plt.xlabel("Time")
    plt.ylabel("Drawdown")
    axes.set_title("Drawdown x Time")

    legend_text = "\n".join([f"{ticker}: {max_drawdown:.2%}" for ticker, max_drawdown in max_drawdowns.items()]) + "\n"
    plt.legend(title=f"Max. Drawdowns:\n\n{legend_text}")

    setup_mplcursors()

    plt.show()


if __name__ == "__main__":
    main()
