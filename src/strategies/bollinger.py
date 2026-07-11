#
# Imports
#

import os
import sys
import pandas as pd

# Local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from strategies.utils import non_negative_float, positive_float, positive_integer, prompt_value, report_strategy, run_backtest
from utils import (
    configure_yfinance_logging,
    fetch_asset_ticker_input,
    get_start_date_input,
    print_with_separator,
)

#
# Strategy
#


def bollinger_signals(prices: pd.Series, window: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """Return Bollinger Bands and persistent long/short signals."""
    # Validate the strategy parameters
    if window <= 1:
        raise ValueError("window must be greater than one")
    if std_dev <= 0:
        raise ValueError("std_dev must be positive")

    # Sort prices before calculating rolling statistics
    clean_prices = prices.astype(float).sort_index()

    # Calculate the middle, upper, and lower Bollinger Bands
    middle = clean_prices.rolling(window).mean()
    rolling_std = clean_prices.rolling(window).std()
    upper = middle + rolling_std * std_dev
    lower = middle - rolling_std * std_dev

    # Generate long and short signals when prices cross the bands
    raw_signal = pd.Series(index=clean_prices.index, dtype=float)
    raw_signal.loc[clean_prices < lower] = 1.0
    raw_signal.loc[clean_prices > upper] = -1.0
    # Keep the latest position until a new signal occurs
    position_signal = raw_signal.ffill().fillna(0.0)

    return pd.DataFrame(
        {
            "Price": clean_prices,
            "Middle Band": middle,
            "Upper Band": upper,
            "Lower Band": lower,
            "Signal": position_signal,
            "Signal Change": position_signal.diff().fillna(position_signal),
        }
    )


#
# Main
#


def main() -> None:
    #
    # Overview
    #

    print_with_separator(
        [
            "Strategy Backtest: Bollinger Bands Strategy",
            "",
            "Long below the lower band and short above the upper band.",
            "Signals execute on the next period to avoid lookahead bias.",
        ]
    )

    #
    # Inputs
    #

    # Get the asset and analysis period
    configure_yfinance_logging()
    start_date = get_start_date_input()
    assets = fetch_asset_ticker_input(start_date, single_asset=True)
    asset_ticker = next(iter(assets))
    asset_data = assets[asset_ticker]
    if isinstance(asset_data, pd.DataFrame):
        asset_data = asset_data.iloc[:, 0]
    asset_data.index = pd.to_datetime(asset_data.index)

    # Get the strategy parameters
    window = prompt_value(
        "Specify the Bollinger Bands window period (in days, e.g., 20): ",
        positive_integer,
        "Invalid input. Please enter a positive integer.",
    )
    std_dev = prompt_value(
        "Specify the standard deviation multiplier (e.g., 2.0): ",
        positive_float,
        "Invalid input. Please enter a positive number.",
    )
    transaction_cost_bps = prompt_value(
        "Transaction cost in basis points per position change (e.g., 10, or 0): ",
        non_negative_float,
        "Invalid input. Please enter zero or a positive number.",
    )

    #
    # Backtest
    #

    # Generate signals and apply next-period execution
    bands = bollinger_signals(asset_data, window=window, std_dev=std_dev)
    result = run_backtest(asset_data, bands["Signal"], transaction_cost_bps=transaction_cost_bps)

    #
    # Results
    #

    # Compare the strategy against buy and hold
    report_strategy(
        "Bollinger Bands Strategy",
        result.strategy_returns,
        result.equity,
        {"Buy and Hold": (result.benchmark_returns, result.benchmark_equity)},
        periods_per_year=252,
        note=f"Asset: {asset_ticker} | Window: {window} | Std Dev: {std_dev}",
    )


if __name__ == "__main__":
    main()
