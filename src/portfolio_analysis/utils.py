#
# Imports
#

from collections.abc import Mapping
import numpy as np
import pandas as pd


def price_series(data: pd.Series | pd.DataFrame, ticker: str | None = None) -> pd.Series:
    """Normalize downloaded price data to a Series."""
    if isinstance(data, pd.Series):
        return data.astype(float)
    if ticker is not None and ticker in data.columns:
        return data[ticker].astype(float)
    if data.shape[1] == 1:
        return data.iloc[:, 0].astype(float)
    raise ValueError("price data must contain exactly one applicable column")


def weighted_portfolio_prices(assets: Mapping[str, pd.Series | pd.DataFrame], weights: Mapping[str, float]) -> pd.Series:
    """Combine aligned asset prices using percentage weights."""
    weighted = [price_series(data, ticker) * (weights[ticker] / 100.0) for ticker, data in assets.items()]
    return pd.concat(weighted, axis=1, join="inner").sum(axis=1).rename("Portfolio")


def drawdown_series(prices: pd.Series) -> pd.Series:
    """Calculate percentage decline from each prior peak."""
    running_peak = prices.cummax()
    return (prices / running_peak - 1.0).rename("Drawdown")


def historical_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """Calculate positive historical Value at Risk in decimal form."""
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between zero and one")
    clean_returns = returns.dropna().to_numpy(dtype=float)
    if clean_returns.size == 0:
        raise ValueError("returns cannot be empty")
    return abs(float(np.quantile(clean_returns, 1.0 - confidence_level, method="lower")))
