#
# Imports
#

from dataclasses import dataclass

from bcb import sgs
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.axes import Axes
import numpy as np
import pandas as pd
import yfinance as yf

# Local imports
from utils import apply_mpl_style, print_with_separator, setup_mplcursors

#
# Results
#


@dataclass(frozen=True)
class BacktestResult:
    """Time series produced by a single-asset backtest."""

    prices: pd.Series
    signals: pd.Series
    positions: pd.Series
    trades: pd.Series
    asset_returns: pd.Series
    strategy_returns: pd.Series
    benchmark_returns: pd.Series
    equity: pd.Series
    benchmark_equity: pd.Series
    drawdown: pd.Series


@dataclass(frozen=True)
class AllocationBacktestResult:
    """Time series produced by a two-asset tactical allocation backtest."""

    signals: pd.Series
    risky_weights: pd.Series
    trades: pd.Series
    risky_returns: pd.Series
    defensive_returns: pd.Series
    strategy_returns: pd.Series
    equity: pd.Series
    risky_equity: pd.Series
    defensive_equity: pd.Series
    drawdown: pd.Series


#
# Metrics
#


def performance_metrics(returns: pd.Series, periods_per_year: int = 252) -> pd.Series:
    """Calculate common metrics from a periodic return series."""
    # Remove missing observations before calculating metrics
    clean_returns = returns.dropna().astype(float)
    if clean_returns.empty:
        raise ValueError("returns cannot be empty")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")

    # Build the equity curve and annualize return statistics
    equity = (1.0 + clean_returns).cumprod()
    total_return = equity.iloc[-1] - 1.0
    years = len(clean_returns) / periods_per_year
    annual_return = equity.iloc[-1] ** (1.0 / years) - 1.0 if years > 0 and equity.iloc[-1] > 0 else np.nan
    annual_volatility = clean_returns.std(ddof=1) * np.sqrt(periods_per_year)
    annualized_mean_return = clean_returns.mean() * periods_per_year
    sharpe_ratio = annualized_mean_return / annual_volatility if annual_volatility > 0 else np.nan
    # Calculate the largest decline from a previous peak
    max_drawdown = (equity / equity.cummax() - 1.0).min()

    return pd.Series(
        {
            "Total Return": total_return,
            "Annual Return": annual_return,
            "Annual Volatility": annual_volatility,
            "Sharpe Ratio": sharpe_ratio,
            "Maximum Drawdown": max_drawdown,
        },
        dtype=float,
    )


#
# Backtesting
#


def run_backtest(prices: pd.Series, signals: pd.Series, transaction_cost_bps: float = 0.0) -> BacktestResult:
    """Backtest positions from signals using next-period execution."""
    # Validate prices, signals, and transaction costs
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps cannot be negative")
    if prices.empty:
        raise ValueError("prices cannot be empty")
    if not prices.index.is_unique or not signals.index.is_unique:
        raise ValueError("prices and signals must have unique indices")

    clean_prices = prices.astype(float).sort_index().dropna()
    if (clean_prices <= 0).any():
        raise ValueError("prices must be positive")
    # Align signals with the available price history
    aligned_signals = signals.reindex(clean_prices.index).ffill().fillna(0.0).astype(float)
    if not aligned_signals.isin([-1.0, 0.0, 1.0]).all():
        raise ValueError("signals must contain only -1, 0, or 1")

    # Delay positions by one period to prevent lookahead bias
    positions = aligned_signals.shift(1).fillna(0.0)
    trades = positions.diff().fillna(positions).abs()
    asset_returns = clean_prices.pct_change().fillna(0.0)
    # Apply asset returns and transaction costs to each position
    strategy_returns = (positions * asset_returns - trades * (transaction_cost_bps / 10_000)).rename("Strategy")
    benchmark_returns = asset_returns.rename("Buy and Hold")
    equity = (1.0 + strategy_returns).cumprod().rename("Strategy")
    benchmark_equity = (1.0 + benchmark_returns).cumprod().rename("Buy and Hold")
    drawdown = (equity / equity.cummax() - 1.0).rename("Drawdown")
    return BacktestResult(
        clean_prices,
        aligned_signals,
        positions,
        trades,
        asset_returns,
        strategy_returns,
        benchmark_returns,
        equity,
        benchmark_equity,
        drawdown,
    )


def run_allocation_backtest(
    risky_returns: pd.Series,
    defensive_returns: pd.Series,
    signals: pd.Series,
    transaction_cost_bps: float = 0.0,
) -> AllocationBacktestResult:
    """Backtest next-period switches between risky and defensive assets."""
    # Align both return series on common dates
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps cannot be negative")
    returns = pd.concat([risky_returns.rename("Risky"), defensive_returns.rename("Defensive")], axis=1, join="inner").dropna()
    if returns.empty:
        raise ValueError("risky and defensive returns do not overlap")
    if not returns.index.is_unique or not signals.index.is_unique:
        raise ValueError("returns and signals must have unique indices")
    if (returns <= -1.0).any().any():
        raise ValueError("returns must be greater than -100%")

    # Align allocation decisions with the return history
    aligned_signals = signals.reindex(returns.index).ffill().fillna(0.0).astype(float)
    if not aligned_signals.isin([0.0, 1.0]).all():
        raise ValueError("allocation signals must contain only 0 or 1")
    # Delay allocation changes by one period to prevent lookahead bias
    risky_weights = aligned_signals.shift(1).fillna(0.0).rename("Risky Weight")
    trades = risky_weights.diff().fillna(risky_weights).abs().rename("Turnover")
    # Combine risky and defensive returns after transaction costs
    strategy_returns = (risky_weights * returns["Risky"] + (1.0 - risky_weights) * returns["Defensive"] - trades * (transaction_cost_bps / 10_000)).rename(
        "Strategy"
    )
    equity = (1.0 + strategy_returns).cumprod().rename("Strategy")
    risky_equity = (1.0 + returns["Risky"]).cumprod().rename("Risky")
    defensive_equity = (1.0 + returns["Defensive"]).cumprod().rename("Defensive")
    drawdown = (equity / equity.cummax() - 1.0).rename("Drawdown")
    return AllocationBacktestResult(
        aligned_signals,
        risky_weights,
        trades,
        returns["Risky"],
        returns["Defensive"],
        strategy_returns,
        equity,
        risky_equity,
        defensive_equity,
        drawdown,
    )


#
# Inputs
#


def positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise ValueError
    return parsed


def integer_greater_than_one(value: str) -> int:
    parsed = int(value)
    if parsed <= 1:
        raise ValueError
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise ValueError
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise ValueError
    return parsed


def prompt_value(message: str, parser, error_message: str):
    while True:
        try:
            return parser(input(message))
        except ValueError:
            print(error_message)


#
# Data
#


def download_monthly_ibov_cdi(start_date: str) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Download aligned IBOV prices/returns and CDI returns."""
    # Convert daily CDI rates into monthly returns
    cdi_daily_returns = sgs.get({"CDI": 11}, start=start_date)["CDI"] / 100.0
    cdi_monthly_returns = (1.0 + cdi_daily_returns).cumprod().resample("ME").last().pct_change()

    # Download IBOV prices and resample them monthly
    ibov = yf.download("^BVSP", start=start_date, auto_adjust=True, progress=False)["Close"]
    if isinstance(ibov, pd.DataFrame):
        ibov = ibov.iloc[:, 0]
    ibov.index = pd.to_datetime(ibov.index)
    ibov_monthly_prices = ibov.sort_index().resample("ME").last()
    ibov_monthly_returns = ibov_monthly_prices.pct_change()

    # Keep only dates available for both IBOV and CDI
    aligned = pd.concat(
        [
            ibov_monthly_prices.rename("IBOV Price"),
            ibov_monthly_returns.rename("IBOV Return"),
            cdi_monthly_returns.rename("CDI Return"),
        ],
        axis=1,
        join="inner",
    ).dropna(subset=["IBOV Return", "CDI Return"])
    if aligned.empty:
        raise ValueError("IBOV and CDI data do not overlap for the selected period")
    return aligned["IBOV Price"], aligned["IBOV Return"], aligned["CDI Return"]


#
# Graphs
#


def plot_performance(
    axes: Axes,
    curves: dict[str, pd.Series],
    title: str,
    legend_title: str | None = None,
) -> None:
    """Plot consistently formatted cumulative-performance curves."""
    # Plot every strategy and benchmark with consistent formatting
    for label, curve in curves.items():
        axes.plot(curve, label=label, linewidth=2)
    axes.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    axes.set_xlabel("Time")
    axes.set_ylabel("Performance")
    axes.set_title(title)
    axes.legend(title=legend_title)
    axes.grid(True, alpha=0.3)


def report_strategy(
    strategy_name: str,
    strategy_returns: pd.Series,
    strategy_equity: pd.Series,
    benchmarks: dict[str, tuple[pd.Series, pd.Series]],
    periods_per_year: int,
    note: str | None = None,
) -> None:
    """Display the same metrics and performance chart for every strategy."""
    # Calculate the same metrics for the strategy and all benchmarks
    returns = {strategy_name: strategy_returns}
    returns.update({name: benchmark_returns for name, (benchmark_returns, _) in benchmarks.items()})
    metrics = pd.concat(
        {name: performance_metrics(values, periods_per_year=periods_per_year) for name, values in returns.items()},
        axis=1,
    )
    # Format returns and risk values for terminal output
    formatted = metrics.copy().astype(object)
    percent_rows = ["Total Return", "Annual Return", "Annual Volatility", "Maximum Drawdown"]
    formatted.loc[percent_rows] = metrics.loc[percent_rows].map(lambda value: f"{value:.2%}")
    formatted.loc["Sharpe Ratio"] = metrics.loc["Sharpe Ratio"].map(lambda value: f"{value:.2f}")
    output = ["Performance Metrics", "", formatted.to_string()]
    if note:
        output.extend(["", note])
    print_with_separator(output)

    # Plot cumulative performance for the strategy and benchmarks
    apply_mpl_style()
    _, axes = plt.subplots(figsize=(14, 8))
    curves = {name: equity - 1.0 for name, (_, equity) in benchmarks.items()}
    curves[strategy_name] = strategy_equity - 1.0
    plot_performance(
        axes,
        curves,
        title="Strategy Performance Comparison",
    )
    setup_mplcursors()
    plt.tight_layout()
    plt.show()
