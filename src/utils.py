"""
Utility functions for the Financial Market Python project.

This module contains common functionality used across multiple scripts,
including input validation, data retrieval, and plotting utilities.
"""

import logging
from datetime import datetime, date
import yfinance as yf
import matplotlib.pyplot as plt
import mplcursors
import os


def configure_yfinance_logging():
    """
    Set the logging level for yfinance to CRITICAL to reduce noise.
    """
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def validate_date(input_date, max_days_from_today=None):
    """
    Validate that a date string is in the correct format (YYYY-MM-DD) and is before today.
    Optionally, check if the date is within a maximum number of days from today.

    Args:
        input_date (str): The date string to validate in YYYY-MM-DD format.
        max_days_from_today (int, optional): Maximum allowed days between input_date and today. If None, no limit.

    Returns:
        bool: True if the date is valid and before today (and within max_days_from_today if specified), False otherwise.
    """
    try:
        parsed_date = datetime.strptime(input_date, "%Y-%m-%d")
        year, month, day = map(str, input_date.split("-"))
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
            if parsed_date.date() < date.today():
                if max_days_from_today is not None:
                    delta = (date.today() - parsed_date.date()).days
                    if delta > max_days_from_today:
                        print(f"The date should not be more than {max_days_from_today} days before today.")
                        return False
                return True
            else:
                print("The start date should be before today's date.")
                return False
        else:
            print("Invalid date format. Please use YYYY-MM-DD format.")
            return False
    except Exception:
        print("Invalid date format. Please use YYYY-MM-DD format.")
        return False


def get_start_date_input(max_days_from_today=None):
    """
    Prompt the user for a start date and validate it.

    Returns:
        str: A valid start date in YYYY-MM-DD format.
    """
    start_date = None
    while start_date is None:
        start_date = input("Please input the analysis start date (YYYY-MM-DD): ")
        if not validate_date(start_date, max_days_from_today):
            start_date = None
    return start_date


def validate_assets(asset_inputs, start_date):
    """
    Validate and download asset data from yfinance.

    Args:
        asset_inputs (str): Comma-separated asset ticker symbols.
        start_date (str): The start date for downloading data in YYYY-MM-DD format.

    Returns:
        dict: A dictionary with ticker symbols as keys and downloaded data as values.
    """
    assets = {}
    asset_tickers = asset_inputs.split(",")
    for ticker in asset_tickers:
        # Remove leading/trailing spaces
        ticker = ticker.strip()
        # Download asset data using yfinance
        downloaded_data = yf.download(ticker, start_date, auto_adjust=True)
        if downloaded_data is None or downloaded_data.empty:
            raise ValueError(f"No data found for ticker '{ticker}'.")
        asset_data = downloaded_data["Close"]
        if len(asset_data) > 0:
            # Store asset data if successfully downloaded
            assets[ticker] = asset_data
    return assets


def get_asset_tickers_input(start_date):
    """
    Prompt the user for asset ticker symbols and validate them.

    Args:
        start_date (str): The start date for downloading data in YYYY-MM-DD format.

    Returns:
        dict: A dictionary with valid ticker symbols as keys and downloaded data as values.
    """
    asset_tickers = None
    while asset_tickers is None:
        asset_tickers = input("Specify the asset ticker symbols (comma-separated): ")
        assets = validate_assets(asset_tickers, start_date)
        if not assets:
            print("No valid assets found. Please enter at least one valid asset ticker symbol.")
            asset_tickers = None
    return assets


def get_portfolio_weights(assets):
    """
    Prompt the user for portfolio weights and validate that they sum to 100%.

    Args:
        assets (dict): A dictionary of asset ticker symbols.

    Returns:
        dict: A dictionary with ticker symbols as keys and weights (as percentages) as values.
    """
    asset_weights = {}
    while True:
        total_weight = 0
        for ticker in assets.keys():
            while True:
                try:
                    weight = float(input(f"Enter the weight (as a percentage) of asset {ticker} in the portfolio: "))
                    if weight < 0 or weight > 100:
                        print("Invalid weight. Please enter a value between 0 and 100.")
                    else:
                        asset_weights[ticker] = weight
                        total_weight += weight
                        break
                except ValueError:
                    print("Invalid input. Please enter a valid number.")

        if total_weight != 100:
            print(f"Total weight is {total_weight}, but it should be 100. Please re-enter the weights.")
            asset_weights.clear()
        else:
            break

    return asset_weights


def setup_mplcursors():
    """
    Set up interactive cursor annotations for matplotlib plots.

    Returns:
        mplcursors.Cursor: The configured cursor object.
    """
    cursor = mplcursors.cursor()

    @cursor.connect("add")
    def on_add(sel):
        sel.annotation.get_bbox_patch().set(fc="gray", alpha=0.8)
        sel.annotation.get_bbox_patch().set_edgecolor("gray")
        sel.annotation.arrow_patch.set_color("white")
        sel.annotation.arrow_patch.set_arrowstyle("-")

    return cursor


def brl_formatter(x, _):
    """
    Format tick labels as Brazilian Real (BRL) currency.

    Args:
        x (float): The tick value.
        pos (int): The tick position.

    Returns:
        str: The formatted string with BRL currency symbol.
    """
    return f"R${x:.2f}"


def apply_mpl_style():
    """
    Apply the custom financial graphs matplotlib style.
    """
    style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "financialgraphs.mplstyle")
    plt.style.use(style_path)


def print_with_separator(message):
    """
    Print a message or list of messages surrounded by separator lines for better readability.

    Args:
        message (str or list of str): The message(s) to print.
    """
    print("\n" + "=" * 100 + "\n")
    if isinstance(message, list):
        for msg in message:
            print(msg)
    else:
        print(message)
    print("\n" + "=" * 100 + "\n")
