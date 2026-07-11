#
# Imports
#

import yfinance as yf
import pandas as pd
import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import sys
import os

# Local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import configure_yfinance_logging, get_start_date_input, setup_mplcursors, apply_mpl_style, print_with_separator

#
# Main
#


def main() -> None:
    #
    # Overview
    #

    print_with_separator(
        [
            "Markowitz Portfolio Optimization",
            "",
            "This program determines optimal portfolio asset allocation using Modern Portfolio Theory.",
            "",
            "Optimization Objectives",
            "- Maximize Sharpe Ratio: find the portfolio with the best risk-adjusted return",
            "- Target Return: Achieve a specific expected return while minimizing risk",
            "- Target Risk: Maximize return while keeping volatility at or below a specified level",
            "Output",
            "- Optimal portfolio weights for each asset",
            "- Efficient frontier visualization",
            "- Portfolio metrics (return, risk, Sharpe ratio)",
        ]
    )

    #
    # Inputs
    #

    configure_yfinance_logging()

    def validate_assets(asset_inputs, start_date):
        assets = {}
        asset_tickers = asset_inputs.split(",")

        # Check if the input is more than one asset
        if len(asset_tickers) == 1:
            print("Error: Please enter at least two valid asset ticker symbols.")
            return pd.DataFrame()

        for ticker in asset_tickers:
            # Remove leading/trailing spaces
            ticker = ticker.strip()
            # Download asset data using yfinance
            asset_data = yf.download(ticker, start_date, auto_adjust=True)["Close"]
            if not asset_data.empty:
                # Convert DataFrame to Series
                assets[ticker] = asset_data.squeeze()
            else:
                print(f"Error: No data found for ticker '{ticker}'.")
                return pd.DataFrame()

        if not assets:
            print("Error: No valid assets found. Please enter at least two valid asset ticker symbol.")
            return pd.DataFrame()

        # Convert the dictionary to a DataFrame
        assets_df = pd.DataFrame(assets)

        # Drop rows with missing values to ensure data for all dates
        assets_df.dropna(inplace=True)

        if assets_df.empty:
            print("Error: No overlapping data found for the selected assets. Please choose different tickers or a different date range.")
            return pd.DataFrame()

        return assets_df

    start_date = get_start_date_input()

    asset_tickers = None
    while asset_tickers is None:
        asset_tickers = input("Specify the asset ticker symbols (comma-separated): ")
        assets = validate_assets(asset_tickers, start_date)
        if assets.empty:
            asset_tickers = None

    log_returns = np.log(assets / assets.shift(1))

    # Calculate the annualized mean of log returns and its covariance matrix
    log_mean = log_returns.mean() * 252
    covariance = log_returns.cov() * 252

    # Define the bounds for portfolio weights (between 0 and 1)
    bounds = [(0, 1)] * len(assets.columns)

    # Define an initial guess for portfolio weights (equal weights)
    initial_guess = [1 / len(assets.columns)] * len(assets.columns)

    # Define an initial constraint that ensures the sum of weights equals 1
    constraints = [{"type": "eq", "fun": lambda weights: np.sum(weights) - 1}]

    def metrics(weights):
        weights = np.array(weights)
        returns = log_mean.dot(weights)
        volatility = np.sqrt(weights.T.dot(covariance.dot(weights)))
        sharpe_ratio = returns / volatility
        return [returns, volatility, sharpe_ratio]

    # Calculate weights and returns for the optimizations and input filtering
    maximum_return_weights = optimize.minimize(
        lambda weights: metrics(weights)[0] * -1, initial_guess, method="SLSQP", bounds=bounds, constraints=constraints
    ).x
    maximum_return = metrics(maximum_return_weights)[0]

    minimum_risk_weights = optimize.minimize(lambda weights: metrics(weights)[1], initial_guess, method="SLSQP", bounds=bounds, constraints=constraints).x
    minimum_risk = metrics(minimum_risk_weights)[1]
    minimum_risk_return = metrics(minimum_risk_weights)[0]

    maximum_risk_weights = optimize.minimize(lambda weights: metrics(weights)[1] * -1, initial_guess, method="SLSQP", bounds=bounds, constraints=constraints).x
    maximum_risk = metrics(maximum_risk_weights)[1]

    calculation_type = input('Choose the optimization goal ("sharpe", "risk" or "return"): ')
    while calculation_type not in ["sharpe", "risk", "return"]:
        calculation_type = input('Invalid input. Please enter either "sharpe", "risk" or "return": ')

    if calculation_type == "risk":
        while True:
            try:
                risk_tolerance = float(input(f"Enter your desired risk level (e.g., 0.10 for 10%) (between {minimum_risk:.2f} and {maximum_risk:.2f}): "))
                if minimum_risk <= risk_tolerance <= maximum_risk:
                    break
                else:
                    print(f"Risk tolerance must be between {minimum_risk:.2f} and {maximum_risk:.2f}.")
            except ValueError:
                print("Invalid input. Please enter a valid number for risk.")

    if calculation_type == "return":
        while True:
            try:
                expected_return = float(
                    input(f"Enter your desired expected return (e.g., 0.10 for 10%) (between {minimum_risk_return:.2f} and {maximum_return:.2f}): ")
                )
                if minimum_risk_return <= expected_return <= maximum_return:
                    break
                else:
                    print(f"Expected return must be between {minimum_risk_return:.2f} and {maximum_return:.2f}.")
            except ValueError:
                print("Invalid input. Please enter a valid number for return.")

    #
    # Optimization
    #

    # Use the minimize function to find optimal weights that maximize Sharpe ratio (minimize sharpe_ratio * -1)
    sharpe_ratio_optimal_weights = optimize.minimize(
        lambda weights: metrics(weights)[2] * -1, initial_guess, method="SLSQP", bounds=bounds, constraints=constraints
    ).x

    if calculation_type == "risk":
        # Find optimal weights that maximize return (minimize return * -1)
        constraints.append({"type": "ineq", "fun": lambda weights: risk_tolerance - metrics(weights)[1]})
        optimal_weights = optimize.minimize(lambda weights: metrics(weights)[0] * -1, initial_guess, method="SLSQP", bounds=bounds, constraints=constraints).x

    elif calculation_type == "return":
        # Find optimal weights that minimize risk
        constraints.append({"type": "eq", "fun": lambda weights: metrics(weights)[0] - expected_return})
        optimal_weights = optimize.minimize(lambda weights: metrics(weights)[1], initial_guess, method="SLSQP", bounds=bounds, constraints=constraints).x

    #
    # Efficient Frontier
    #

    # Generate a range of target returns
    target_returns = np.linspace(minimum_risk_return, maximum_return, 100)

    efficient_frontier_volatility = []
    efficient_frontier_return = []

    # Calculate the efficient frontier
    for target_return in target_returns:
        # Optimize for minimum volatility given the target return
        constraints = [{"type": "eq", "fun": lambda weights: np.sum(weights) - 1}, {"type": "eq", "fun": lambda weights: metrics(weights)[0] - target_return}]
        result = optimize.minimize(lambda weights: metrics(weights)[1], initial_guess, method="SLSQP", bounds=bounds, constraints=constraints)

        efficient_frontier_volatility.append(result.fun)
        efficient_frontier_return.append(target_return)

    #
    # Graph
    #

    apply_mpl_style()

    _, axes = plt.subplots(figsize=(14, 8))

    axes.plot(efficient_frontier_volatility, efficient_frontier_return, label="Efficient Frontier")

    if calculation_type == "sharpe":
        optimal_weights = sharpe_ratio_optimal_weights
        axes.scatter(metrics(optimal_weights)[1], metrics(optimal_weights)[0], marker="o", label="Optimal Portfolio")
    else:
        axes.scatter(metrics(sharpe_ratio_optimal_weights)[1], metrics(sharpe_ratio_optimal_weights)[0], marker="o", label="Max. Sharpe Ratio")
        axes.scatter(metrics(optimal_weights)[1], metrics(optimal_weights)[0], marker="o", label="Optimal Portfolio")

    axes.xaxis.set_major_formatter(mplticker.PercentFormatter(1.0))
    axes.yaxis.set_major_formatter(mplticker.PercentFormatter(1.0))
    plt.xlabel("Volatility")
    plt.ylabel("Return")
    axes.set_title("Anual Expected Return x Volatility")

    legend_text = (
        "\n".join([f"{metric}: {metrics(optimal_weights)[i]:.2%}" for i, metric in enumerate(["Expected Return", "Volatility", "Sharpe Ratio"])]) + "\n\n"
    )
    legend_text = legend_text + "\n".join([f"{asset}'s weight: {i:.2%}" for asset, i in zip(assets.columns.tolist(), optimal_weights)]) + "\n"
    plt.legend(title=f"{legend_text}")

    setup_mplcursors()

    plt.show()


if __name__ == "__main__":
    main()
