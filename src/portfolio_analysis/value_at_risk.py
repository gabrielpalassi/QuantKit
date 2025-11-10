import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add the src directory to the path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import (
    configure_yfinance_logging,
    get_start_date_input,
    get_asset_tickers_input,
    get_portfolio_weights,
    print_with_separator,
    setup_mplcursors,
    apply_mpl_style,
)

#
# Overview
#

print_with_separator(
    [
        "Value at Risk (VaR) Analysis",
        "",
        "This program calculates VaR using historical simulation methodology.",
        "",
        "Methodology",
        "- Historical Simulation: Uses actual historical returns to estimate risk",
        "- Calculates VaR for daily, monthly, and yearly periods",
        "Analysis Options",
        "- Individual Assets: Calculate VaR for each asset separately",
        "- Portfolio: Calculate VaR for weighted portfolio",
        "Output",
        "- Daily, Monthly, and Yearly VaR values at the specified confidence level",
    ]
)

#
# Inputs
#

configure_yfinance_logging()

start_date = get_start_date_input()

confidence_level = None
while confidence_level is None:
    try:
        confidence_level = float(input("Please enter the confidence level (e.g., 95 for 95%): ")) / 100.0
        if confidence_level <= 0 or confidence_level >= 1:
            print("Invalid confidence level. Please enter a value between 1 and 99.")
            confidence_level = None
    except ValueError:
        print("Invalid input. Please enter a number between 1 and 99.")

calculation_type = input("Do you want to calculate VaR for individual assets or for a portfolio? (assets/portfolio): ")
while calculation_type not in ["assets", "portfolio"]:
    calculation_type = input('Invalid input. Please enter "assets" or "portfolio": ')

assets = get_asset_tickers_input(start_date)

# If calculating VaR for a portfolio, gather asset weights
asset_weights = {}
if calculation_type == "portfolio":
    asset_weights = get_portfolio_weights(assets)

#
# Assets
#

# Calculate the VaR for each asset if assets was selected
if calculation_type == "assets":
    var_results = []

    # Store returns and VaR values for plotting
    asset_daily_returns = {}
    asset_monthly_returns = {}
    asset_yearly_returns = {}
    asset_daily_var = {}
    asset_monthly_var = {}
    asset_yearly_var = {}

    for ticker, asset_data in assets.items():
        var_results.append(f"{ticker}:")

        # Daily VaR
        daily_returns = asset_data.pct_change().dropna()
        asset_daily_returns[ticker] = daily_returns[ticker].values  # Store for plotting
        ordered_daily_returns = np.sort(daily_returns[ticker].values)
        alpha_daily_position = int((1 - confidence_level) * len(ordered_daily_returns))
        daily_var = abs(ordered_daily_returns[alpha_daily_position] * 100)
        asset_daily_var[ticker] = daily_var
        var_results.append(f"   Daily VaR ({confidence_level * 100}%): {daily_var:.2f}%")

        # Monthly VaR
        monthly_returns = asset_data.resample("ME").last().pct_change().dropna()
        asset_monthly_returns[ticker] = monthly_returns[ticker].values  # Store for plotting
        ordered_monthly_returns = np.sort(monthly_returns[ticker].values)
        alpha_monthly_position = int((1 - confidence_level) * len(ordered_monthly_returns))
        monthly_var = abs(ordered_monthly_returns[alpha_monthly_position] * 100)
        asset_monthly_var[ticker] = monthly_var
        var_results.append(f"   Monthly VaR ({confidence_level * 100}%): {monthly_var:.2f}%")

        # Yearly VaR
        yearly_returns = asset_data.resample("YE").last().pct_change().dropna()
        asset_yearly_returns[ticker] = yearly_returns[ticker].values  # Store for plotting
        ordered_yearly_returns = np.sort(yearly_returns[ticker].values)
        alpha_yearly_position = int((1 - confidence_level) * len(ordered_yearly_returns))
        yearly_var = abs(ordered_yearly_returns[alpha_yearly_position] * 100)
        asset_yearly_var[ticker] = yearly_var
        var_results.append(f"   Yearly VaR ({confidence_level * 100}%): {yearly_var:.2f}%")

    print_with_separator(var_results)

#
# Portfolio
#

# Calculate the VaR for the given portfolio if portfolio was selected
if calculation_type == "portfolio":
    combined_asset_data = None
    for ticker, asset_data in assets.items():
        weighted_asset_data = asset_data[ticker] * asset_weights[ticker]
        if combined_asset_data is None:
            combined_asset_data = weighted_asset_data
        else:
            combined_asset_data += weighted_asset_data

    var_results = ["Portfolio VaR:"]

    # Daily VaR
    daily_returns = combined_asset_data.pct_change().dropna()
    portfolio_daily_returns = daily_returns.values  # Store for plotting
    ordered_daily_returns = np.sort(daily_returns.values)
    alpha_daily_position = int((1 - confidence_level) * len(ordered_daily_returns))
    daily_var = abs(ordered_daily_returns[alpha_daily_position] * 100)
    var_results.append(f"   Daily VaR ({confidence_level * 100}%): {daily_var:.2f}%")

    # Monthly VaR
    monthly_returns = combined_asset_data.resample("ME").last().pct_change().dropna()
    portfolio_monthly_returns = monthly_returns.values  # Store for plotting
    ordered_monthly_returns = np.sort(monthly_returns.values)
    alpha_monthly_position = int((1 - confidence_level) * len(ordered_monthly_returns))
    monthly_var = abs(ordered_monthly_returns[alpha_monthly_position] * 100)
    var_results.append(f"   Monthly VaR ({confidence_level * 100}%): {monthly_var:.2f}%")

    # Yearly VaR
    yearly_returns = combined_asset_data.resample("YE").last().pct_change().dropna()
    portfolio_yearly_returns = yearly_returns.values  # Store for plotting
    ordered_yearly_returns = np.sort(yearly_returns.values)
    alpha_yearly_position = int((1 - confidence_level) * len(ordered_yearly_returns))
    yearly_var = abs(ordered_yearly_returns[alpha_yearly_position] * 100)
    var_results.append(f"   Yearly VaR ({confidence_level * 100}%): {yearly_var:.2f}%")

    print_with_separator(var_results)

#
# Graph
#

apply_mpl_style()

if calculation_type == "assets":
    # Create three separate plots (one for each time period) with all assets overlaid
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Get colors from the style's color cycle
    prop_cycle = plt.rcParams["axes.prop_cycle"]
    colors = prop_cycle.by_key()["color"]

    # Daily Returns
    for idx, ticker in enumerate(assets.keys()):
        daily_rets = asset_daily_returns[ticker] * 100
        color = colors[idx % len(colors)]  # Cycle through colors if more assets than colors
        axes[0].hist(daily_rets, bins=30, alpha=0.5, color=color, edgecolor="black", label=f"{ticker} (VaR: {asset_daily_var[ticker]:.2f}%)")
        axes[0].axvline(x=-asset_daily_var[ticker], color=color, linestyle="--", linewidth=2, alpha=0.8)
    axes[0].set_xlabel("Daily Returns (%)")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("Daily Returns Distribution")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Monthly Returns
    for idx, ticker in enumerate(assets.keys()):
        monthly_rets = asset_monthly_returns[ticker] * 100
        color = colors[idx % len(colors)]  # Cycle through colors if more assets than colors
        axes[1].hist(monthly_rets, bins=30, alpha=0.5, color=color, edgecolor="black", label=f"{ticker} (VaR: {asset_monthly_var[ticker]:.2f}%)")
        axes[1].axvline(x=-asset_monthly_var[ticker], color=color, linestyle="--", linewidth=2, alpha=0.8)
    axes[1].set_xlabel("Monthly Returns (%)")
    axes[1].set_ylabel("Frequency")
    axes[1].set_title("Monthly Returns Distribution")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Yearly Returns
    for idx, ticker in enumerate(assets.keys()):
        yearly_rets = asset_yearly_returns[ticker] * 100
        color = colors[idx % len(colors)]  # Cycle through colors if more assets than colors
        axes[2].hist(yearly_rets, bins=30, alpha=0.5, color=color, edgecolor="black", label=f"{ticker} (VaR: {asset_yearly_var[ticker]:.2f}%)")
        axes[2].axvline(x=-asset_yearly_var[ticker], color=color, linestyle="--", linewidth=2, alpha=0.8)
    axes[2].set_xlabel("Yearly Returns (%)")
    axes[2].set_ylabel("Frequency")
    axes[2].set_title("Yearly Returns Distribution")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()

elif calculation_type == "portfolio":
    # Create three subplots for portfolio (daily, monthly, yearly)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Get colors from the style's color cycle
    prop_cycle = plt.rcParams["axes.prop_cycle"]
    colors = prop_cycle.by_key()["color"]

    # Daily Returns
    daily_rets = portfolio_daily_returns * 100
    axes[0].hist(daily_rets, bins=30, alpha=0.7, color=colors[0], edgecolor="black")
    axes[0].axvline(x=-daily_var, color=colors[4], linestyle="--", linewidth=2, label=f"VaR: {daily_var:.2f}%")
    axes[0].set_xlabel("Daily Returns (%)")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("Portfolio - Daily Returns Distribution")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Monthly Returns
    monthly_rets = portfolio_monthly_returns * 100
    axes[1].hist(monthly_rets, bins=30, alpha=0.7, color=colors[1], edgecolor="black")
    axes[1].axvline(x=-monthly_var, color=colors[4], linestyle="--", linewidth=2, label=f"VaR: {monthly_var:.2f}%")
    axes[1].set_xlabel("Monthly Returns (%)")
    axes[1].set_ylabel("Frequency")
    axes[1].set_title("Portfolio - Monthly Returns Distribution")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Yearly Returns
    yearly_rets = portfolio_yearly_returns * 100
    axes[2].hist(yearly_rets, bins=30, alpha=0.7, color=colors[2], edgecolor="black")
    axes[2].axvline(x=-yearly_var, color=colors[4], linestyle="--", linewidth=2, label=f"VaR: {yearly_var:.2f}%")
    axes[2].set_xlabel("Yearly Returns (%)")
    axes[2].set_ylabel("Frequency")
    axes[2].set_title("Portfolio - Yearly Returns Distribution")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()

setup_mplcursors()

plt.show()
