#
# Imports
#

from bcb import Expectativas
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import sys
import os

# Local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from market_data.utils import format_expectations, format_selic_expectations
from utils import setup_mplcursors, brl_formatter, apply_mpl_style, print_with_separator


def main() -> None:
    #
    # Overview
    #

    print_with_separator(
        [
            "Brazilian Central Bank (BCB) - Market Expectations",
            "",
            "This program retrieves and visualizes forward-looking market consensus forecasts.",
            "",
            "Interest Rates",
            "- Selic: Expected future benchmark interest rate",
            "Exchange Rates",
            "- USD/BRL: Expected US Dollar to Brazilian Real exchange rate",
            "Inflation Indices",
            "- IPCA: Expected official consumer price inflation",
            "- IGP-M: Expected general market price inflation",
        ]
    )

    #
    # Data
    #

    print("Downloading data...")

    # Retrieve endpoints
    selic_expectations = Expectativas().get_endpoint("ExpectativasMercadoSelic")
    monthly_expectations = Expectativas().get_endpoint("ExpectativaMercadoMensais")
    anual_expectations = Expectativas().get_endpoint("ExpectativasMercadoAnuais")

    # Query and filter data
    selic = (
        selic_expectations.query()
        .filter(selic_expectations.baseCalculo == "1")
        .select(selic_expectations.Data, selic_expectations.Reuniao, selic_expectations.Mediana)
        .orderby(selic_expectations.Data.asc())
        .collect()
    )

    monthly_ipca = (
        monthly_expectations.query()
        .filter(monthly_expectations.Indicador == "IPCA", monthly_expectations.baseCalculo == "1")
        .select(monthly_expectations.Data, monthly_expectations.DataReferencia, monthly_expectations.Mediana)
        .orderby(monthly_expectations.Data.asc())
        .collect()
    )

    anual_ipca = (
        anual_expectations.query()
        .filter(anual_expectations.Indicador == "IPCA", anual_expectations.baseCalculo == "1")
        .select(anual_expectations.Data, anual_expectations.DataReferencia, anual_expectations.Mediana)
        .orderby(anual_expectations.Data.asc())
        .collect()
    )

    monthly_igpm = (
        monthly_expectations.query()
        .filter(monthly_expectations.Indicador == "IGP-M", monthly_expectations.baseCalculo == "1")
        .select(monthly_expectations.Data, monthly_expectations.DataReferencia, monthly_expectations.Mediana)
        .orderby(monthly_expectations.Data.asc())
        .collect()
    )

    anual_igpm = (
        anual_expectations.query()
        .filter(anual_expectations.Indicador == "IGP-M", anual_expectations.baseCalculo == "1")
        .select(anual_expectations.Data, anual_expectations.DataReferencia, anual_expectations.Mediana)
        .orderby(anual_expectations.Data.asc())
        .collect()
    )

    dollar = (
        monthly_expectations.query()
        .filter(monthly_expectations.Indicador == "Câmbio", monthly_expectations.baseCalculo == "1")
        .select(monthly_expectations.Data, monthly_expectations.DataReferencia, monthly_expectations.Mediana)
        .orderby(monthly_expectations.Data.asc())
        .collect()
    )

    selic = format_selic_expectations(selic)
    dollar = format_expectations(dollar, "monthly")
    monthly_ipca = format_expectations(monthly_ipca, "monthly")
    monthly_igpm = format_expectations(monthly_igpm, "monthly")
    anual_ipca = format_expectations(anual_ipca, "annual")
    anual_igpm = format_expectations(anual_igpm, "annual")

    #
    # Graph
    #

    apply_mpl_style()

    _, axes = plt.subplots(2, 2, figsize=(14, 8))

    axes[0][0].plot(selic, label="Selic")
    axes[0][0].yaxis.set_major_formatter(ticker.PercentFormatter())
    axes[0][0].set_ylabel("Selic")
    axes[0][0].xaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
    axes[0][0].legend()

    axes[0][1].plot(dollar, label="USD")
    axes[0][1].yaxis.set_major_formatter(brl_formatter)
    axes[0][1].set_ylabel("Dollar (USD)")
    axes[0][1].xaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
    axes[0][1].legend()

    axes[1][0].plot(monthly_ipca, label="IPCA")
    axes[1][0].plot(monthly_igpm, label="IGP-M")
    axes[1][0].yaxis.set_major_formatter(ticker.PercentFormatter(decimals=2))
    axes[1][0].set_ylabel("Monthly Inflation")
    axes[1][0].xaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
    axes[1][0].legend()

    # Convert the index of anual_ipca and anual_igpm to a list for plotting in bars
    years_ipca = anual_ipca.index.year.tolist()
    years_igpm = anual_igpm.index.year.tolist()

    # Define the bar width and an offset for the bars graph
    bar_width = 0.3
    bar_offset = bar_width / 2

    # Plot IPCA and IGP-M anual inflation data with offset to avoid bars overlapping
    axes[1][1].bar(np.array(years_ipca) - bar_offset, anual_ipca["Mediana"], width=bar_width, label="IPCA")
    axes[1][1].bar(np.array(years_igpm) + bar_offset, anual_igpm["Mediana"], width=bar_width, label="IGP-M")
    axes[1][1].yaxis.set_major_formatter(ticker.PercentFormatter(decimals=2))
    axes[1][1].set_ylabel("Annual Inflation")
    axes[1][1].legend()

    # Enable cursor interaction with the graphs
    setup_mplcursors()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
