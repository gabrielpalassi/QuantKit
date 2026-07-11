#
# Imports
#

import os
import sys
import pandas as pd

# Local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from strategies.utils import download_monthly_ibov_cdi, non_negative_float, prompt_value, report_strategy, run_allocation_backtest
from utils import configure_yfinance_logging, get_start_date_input, print_with_separator

#
# Strategy
#


def relative_momentum_signals(risky_returns: pd.Series, defensive_returns: pd.Series) -> pd.DataFrame:
    # Align the risky and defensive returns on common dates
    returns = pd.concat(
        [risky_returns.rename("Risky Return"), defensive_returns.rename("Defensive Return")],
        axis=1,
        join="inner",
    ).dropna()
    # Ensure the assets have an overlapping history
    if returns.empty:
        raise ValueError("risky and defensive returns do not overlap")
    # Select IBOV when it outperforms CDI during the month
    returns["Signal"] = (returns["Risky Return"] > returns["Defensive Return"]).astype(float)
    return returns


#
# Main
#


def main() -> None:
    #
    # Overview
    #

    print_with_separator(
        [
            "Strategy Backtest: Relative Momentum Allocation",
            "",
            "Invests in IBOV after it outperforms CDI for a month.",
            "Otherwise, it invests in CDI. Decisions execute the following month.",
        ]
    )

    #
    # Inputs
    #

    # Get the analysis period and transaction cost
    configure_yfinance_logging()
    start_date = get_start_date_input(1825)
    transaction_cost_bps = prompt_value(
        "Transaction cost in basis points per allocation change (e.g., 10, or 0): ",
        non_negative_float,
        "Invalid input. Please enter zero or a positive number.",
    )

    #
    # Backtest
    #

    # Download monthly data and compare relative performance
    _, ibov_returns, cdi_returns = download_monthly_ibov_cdi(start_date)
    signals = relative_momentum_signals(ibov_returns, cdi_returns)
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
        "Relative Momentum Allocation",
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
