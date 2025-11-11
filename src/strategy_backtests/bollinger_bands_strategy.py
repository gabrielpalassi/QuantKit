import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import sys
import os

# Add the src directory to the path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import configure_yfinance_logging, get_start_date_input, apply_mpl_style, setup_mplcursors, print_with_separator, get_asset_tickers_input

#
# Overview
#

print_with_separator(
    [
        "Strategy Backtest: Bollinger Bands Strategy",
        "",
        "This program backtests a technical analysis strategy using Bollinger Bands.",
        "",
        "Strategy Logic",
        "- Long signal: Price crosses below the lower Bollinger Band (expecting mean reversion up)",
        "- Short signal: Price crosses above the upper Bollinger Band (expecting mean reversion down)",
        "Output",
        "- Cumulative returns comparison: Strategy vs. Buy-and-Hold",
        "- Bollinger Bands visualization with buy/sell signals",
    ]
)

#
# Inputs
#

configure_yfinance_logging()


def validate_positive_integer(input_value):
    """Validate that the input is a positive integer."""
    try:
        value = int(input_value)
        if value > 0:
            return True
    except:
        return False


def validate_positive_float(input_value):
    """Validate that the input is a positive float."""
    try:
        value = float(input_value)
        if value > 0:
            return True
    except:
        return False


start_date = get_start_date_input()

# Get asset ticker and validate
asset = get_asset_tickers_input(start_date, single_asset=True)
asset_ticker = list(asset.keys())[0]  # Get the single asset ticker from the dictionary
asset_data = asset[asset_ticker][asset_ticker]

# Get Bollinger Bands window (number of days)
bb_window = None
while bb_window is None:
    bb_window_input = input("Specify the Bollinger Bands window period (in days, e.g., 20, 40): ")
    if validate_positive_integer(bb_window_input):
        bb_window = int(bb_window_input)
    else:
        print("Invalid input. Please enter a positive integer for the window period.")
        bb_window = None

# Get standard deviation multiplier
bb_std_dev = None
while bb_std_dev is None:
    bb_std_dev_input = input("Specify the standard deviation multiplier (e.g., 1.0, 2.0): ")
    if validate_positive_float(bb_std_dev_input):
        bb_std_dev = float(bb_std_dev_input)
    else:
        print("Invalid input. Please enter a positive number for the standard deviation multiplier.")
        bb_std_dev = None

#
# Calculate Bollinger Bands
#

# Convert the index to datetime and sort the data by date in ascending order
asset_data.index = pd.to_datetime(asset_data.index)
asset_data = asset_data.sort_index(ascending=True)

# Middle band: Simple Moving Average
middle_band = asset_data.rolling(window=bb_window).mean()

# Standard deviation
rolling_std = asset_data.rolling(window=bb_window).std()

# Upper and lower bands
upper_band = middle_band + (rolling_std * bb_std_dev)
lower_band = middle_band - (rolling_std * bb_std_dev)

#
# Generate Trading Signals
#

# Create a DataFrame to store signals
signals = pd.DataFrame(index=asset_data.index)
signals["Price"] = asset_data
signals["Middle Band"] = middle_band
signals["Upper Band"] = upper_band
signals["Lower Band"] = lower_band

# Drop rows with NaN values (due to rolling calculations)
signals.dropna(inplace=True)

# Generate initial signals
# 1 when price crosses below lower band (long signal)
# -1 when price crosses above upper band (short signal)
# NaN otherwise (no new signal)
raw_signal = pd.Series(index=signals.index, dtype=float)
raw_signal.loc[signals["Price"] < signals["Lower Band"]] = 1
raw_signal.loc[signals["Price"] > signals["Upper Band"]] = -1

# Create positions by forward-filling signals
signals["Position"] = raw_signal.ffill().fillna(0)

# Signal column tracks position changes for visualization (Buy/Sell markers)
signals["Signal"] = signals["Position"].diff().replace({2: 1, -2: -1, np.nan: 0})

#
# Calculate Returns
#

# Find the first actual trading signal (first non-zero position)
first_signal_idx = signals[signals["Position"] != 0].index[0]

# Slice data to start from first signal
signals_from_first = signals.loc[first_signal_idx:]

# Calculate daily returns aligned with signals (starting from first actual signal)
asset_returns = asset_data.pct_change().loc[signals_from_first.index]

# Calculate strategy returns (position can be +1 for long, -1 for short, 0 for no position)
strategy_returns = asset_returns * signals_from_first["Position"].shift(1)

# Calculate cumulative returns (both starting from the same point)
buy_hold_cumulative = (1 + asset_returns).cumprod() - 1
strategy_cumulative = (1 + strategy_returns).cumprod() - 1

#
# Create Results DataFrame
#

results = pd.DataFrame(index=signals_from_first.index)
results["Buy and Hold"] = buy_hold_cumulative
results["Bollinger Bands Strategy"] = strategy_cumulative
results.replace(np.nan, 0, inplace=True)

#
# Graphs
#

apply_mpl_style()

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))

# Subplot 1: Performance Comparison
ax1.plot(results["Buy and Hold"], label="Buy and Hold", linewidth=2)
ax1.plot(results["Bollinger Bands Strategy"], label="Bollinger Bands Strategy", linewidth=2)

ax1.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
ax1.set_xlabel("Time")
ax1.set_ylabel("Performance")
ax1.set_title("Performance Comparison: Bollinger Bands Strategy vs. Buy and Hold")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Subplot 2: Bollinger Bands with Price and Signals
ax2.plot(asset_data, label="Price", linewidth=2)
ax2.plot(middle_band, label="Middle Band (SMA)", linewidth=1, linestyle="--")
ax2.plot(upper_band, label="Upper Band", linewidth=1, linestyle="--")
ax2.plot(lower_band, label="Lower Band", linewidth=1, linestyle="--")

# Mark long signals (price crosses below lower band)
long_signals = signals[signals["Signal"] == 1]
ax2.scatter(long_signals.index, long_signals["Price"], marker="^", s=100, label="Long Signal", zorder=5)

# Mark short signals (price crosses above upper band)
short_signals = signals[signals["Signal"] == -1]
ax2.scatter(short_signals.index, short_signals["Price"], marker="v", s=100, label="Short Signal", zorder=5)

ax2.set_xlabel("Time")
ax2.set_ylabel("Price")
ax2.set_title(f"Bollinger Bands for {asset_ticker} (Window: {bb_window}, Std Dev: {bb_std_dev})")
ax2.legend()
ax2.grid(True, alpha=0.3)

setup_mplcursors()

plt.show()
