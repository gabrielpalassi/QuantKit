from bcb import sgs
from dateutil.relativedelta import relativedelta
from bcb import currency
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import sys
import os
from datetime import datetime, date

# Add the src directory to the path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import get_start_date_input, setup_mplcursors, brl_formatter, apply_mpl_style, print_with_separator

#
# Overview
#

print_with_separator(
    [
        "Brazilian Central Bank (BCB) - Historical Data Visualization",
        "",
        "This program retrieves and visualizes key economic indicators from the BCB.",
        "",
        "Interest Rates",
        "- Selic: Brazil's benchmark interest rate",
        "Exchange Rates",
        "- USD/BRL: US Dollar to Brazilian Real exchange rate",
        "- EUR/BRL: Euro to Brazilian Real exchange rate",
        "Inflation Indices",
        "- IPCA: Official consumer price inflation index",
        "- IGP-M: General market price inflation index",
    ]
)

#
# Inputs
#

start_date = get_start_date_input(1825)  # Limit to the last 5 years (1825 days)

#
# Data
#

print("Downloading data...")

# Get data
selic = sgs.get({"Selic": 432}, start=start_date)
currencies = currency.get(["USD", "EUR"], start=start_date, end=date.today(), side="ask")
ipca = sgs.get({"IPCA": 433}, start=start_date)
igpm = sgs.get({"IGP-M": 189}, start=start_date)

# Convert the start_date to a datetime object and subtract 11 months from the date
inflation_12m_start_date = datetime.strptime(start_date, "%Y-%m-%d")
inflation_12m_start_date = inflation_12m_start_date - relativedelta(months=11)
# Calculate the 12-month rolling inflation rates using a moving window approach and the previousl calculated inflation_12m_start_date.
ipca_12m = sgs.get({"IPCA": 433}, start=inflation_12m_start_date)
ipca_12m = ipca_12m.rolling(12).apply(lambda x: (1 + x / 100).prod() - 1).dropna() * 100
igpm_12m = sgs.get({"IGP-M": 189}, start=inflation_12m_start_date)
igpm_12m = igpm_12m.rolling(12).apply(lambda x: (1 + x / 100).prod() - 1).dropna() * 100

#
# Graph
#

apply_mpl_style()

graphs, axes = plt.subplots(4, figsize=(14, 8), sharex="col")

axes[0].plot(selic, label="Selic")
axes[0].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[0].set_ylabel("Selic")
axes[0].legend(title=f'Current Selic: {selic["Selic"].iloc[-1]}')

axes[1].plot(currencies["USD"], label="USD")
axes[1].plot(currencies["EUR"], label="EUR")
axes[1].yaxis.set_major_formatter(brl_formatter)
axes[1].set_ylabel("Currencies")
axes[1].legend(title=f'Last USD: R$ {currencies["USD"].iloc[-1]:.2f}\nLast EUR: R$ {currencies["EUR"].iloc[-1]:.2f}')

axes[2].plot(ipca, label="IPCA")
axes[2].plot(igpm, label="IGP-M")
axes[2].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[2].set_ylabel("Monthly Inflation")
axes[2].legend(title=f'Last IPCA: {ipca["IPCA"].iloc[-1]:.2f}\nLast IGP-M: {igpm["IGP-M"].iloc[-1]:.2f}')

axes[3].plot(ipca_12m, label="IPCA")
axes[3].plot(igpm_12m, label="IGP-M")
axes[3].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[3].set_ylabel("12-month Rolling Inflation")
axes[3].legend(title=f'Last IPCA: {ipca_12m["IPCA"].iloc[-1]:.2f}\nLast IGP-M: {igpm_12m["IGP-M"].iloc[-1]:.2f}')

# Add interactive annotations with cursor functionality
setup_mplcursors()

plt.show()
