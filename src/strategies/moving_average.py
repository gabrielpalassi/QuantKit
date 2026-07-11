#
# Imports
#

import os
import sys
import pandas as pd

# Local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from strategies.utils import (
    download_monthly_ibov_cdi,
    integer_greater_than_one,
    non_negative_float,
    prompt_value,
    report_strategy,
    run_allocation_backtest,
)
from utils import configure_yfinance_logging, get_start_date_input, print_with_separator

#
# Strategy
#


def moving_average_signals(monthly_prices: pd.Series, window: int = 10) -> pd.DataFrame:
    # Validate the moving-average window
    if window <= 1:
        raise ValueError("window must be greater than one")

    # Sort prices and calculate the rolling average
    prices = monthly_prices.astype(float).sort_index()
    moving_average = prices.rolling(window).mean()

    # Select IBOV only when price is above the average
    signal = (prices > moving_average).astype(float).where(moving_average.notna(), 0.0)
    return pd.DataFrame({"Price": prices, "Moving Average": moving_average, "Signal": signal})


#
# Main
#


def main() -> None:
    #
    # Overview
    #

    print_with_separator(
        [
            "Strategy Backtest: Moving Average Allocation",
            "",
            "Invests in IBOV when its monthly close is above its moving average.",
            "Otherwise, it invests in CDI. Decisions execute the following month.",
        ]
    )

    #
    # Inputs
    #

    # Get the analysis period and strategy parameters
    configure_yfinance_logging()
    start_date = get_start_date_input(1825)
    window = prompt_value(
        "Specify the moving-average window in months: ",
        integer_greater_than_one,
        "Invalid input. Please enter an integer greater than one.",
    )
    transaction_cost_bps = prompt_value(
        "Transaction cost in basis points per allocation change (e.g., 10, or 0): ",
        non_negative_float,
        "Invalid input. Please enter zero or a positive number.",
    )

    #
    # Backtest
    #

    # Download monthly data and generate allocation signals
    prices, ibov_returns, cdi_returns = download_monthly_ibov_cdi(start_date)
    signals = moving_average_signals(prices, window=window)
    # Apply each allocation decision in the following month
    result = run_allocation_backtest(
        ibov_returns,
        cdi_returns,
        signals["Signal"],
        transaction_cost_bps=transaction_cost_bps,
    )

    #
    # Results
    #

    # Report performance against both available allocations
    current_asset = "IBOV" if result.signals.iloc[-1] == 1 else "CDI"
    report_strategy(
        "Moving Average Allocation",
        result.strategy_returns,
        result.equity,
        {
            "IBOV": (result.risky_returns, result.risky_equity),
            "CDI": (result.defensive_returns, result.defensive_equity),
        },
        periods_per_year=12,
        note=f"Next allocation: {current_asset}",
    )


if __name__ == "__main__":
    main()
