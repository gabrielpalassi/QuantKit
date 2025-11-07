import numpy as np
import sys
import os

# Add the src directory to the path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import configure_yfinance_logging, get_start_date_input, get_asset_tickers_input, get_portfolio_weights, print_with_separator

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
    for ticker, asset_data in assets.items():
        var_results.append(f"{ticker}:")

        # Daily VaR
        daily_returns = asset_data.pct_change().dropna()
        ordered_daily_returns = np.sort(daily_returns[ticker].values)
        alpha_daily_position = int((1 - confidence_level) * len(ordered_daily_returns))
        daily_var = abs(ordered_daily_returns[alpha_daily_position] * 100)
        var_results.append(f"   Daily VaR ({confidence_level * 100}%): {daily_var:.2f}%")

        # Monthly VaR
        monthly_returns = asset_data.resample("ME").last().pct_change().dropna()
        ordered_monthly_returns = np.sort(monthly_returns[ticker].values)
        alpha_monthly_position = int((1 - confidence_level) * len(ordered_monthly_returns))
        monthly_var = abs(ordered_monthly_returns[alpha_monthly_position] * 100)
        var_results.append(f"   Monthly VaR ({confidence_level * 100}%): {monthly_var:.2f}%")

        # Yearly VaR
        yearly_returns = asset_data.resample("YE").last().pct_change().dropna()
        ordered_yearly_returns = np.sort(yearly_returns[ticker].values)
        alpha_yearly_position = int((1 - confidence_level) * len(ordered_yearly_returns))
        yearly_var = abs(ordered_yearly_returns[alpha_yearly_position] * 100)
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
    ordered_daily_returns = np.sort(daily_returns.values)
    alpha_daily_position = int((1 - confidence_level) * len(ordered_daily_returns))
    daily_var = abs(ordered_daily_returns[alpha_daily_position] * 100)
    var_results.append(f"   Daily VaR ({confidence_level * 100}%): {daily_var:.2f}%")

    # Monthly VaR
    monthly_returns = combined_asset_data.resample("ME").last().pct_change().dropna()
    ordered_monthly_returns = np.sort(monthly_returns.values)
    alpha_monthly_position = int((1 - confidence_level) * len(ordered_monthly_returns))
    monthly_var = abs(ordered_monthly_returns[alpha_monthly_position] * 100)
    var_results.append(f"   Monthly VaR ({confidence_level * 100}%): {monthly_var:.2f}%")

    # Yearly VaR
    yearly_returns = combined_asset_data.resample("YE").last().pct_change().dropna()
    ordered_yearly_returns = np.sort(yearly_returns.values)
    alpha_yearly_position = int((1 - confidence_level) * len(ordered_yearly_returns))
    yearly_var = abs(ordered_yearly_returns[alpha_yearly_position] * 100)
    var_results.append(f"   Yearly VaR ({confidence_level * 100}%): {yearly_var:.2f}%")

    print_with_separator(var_results)
