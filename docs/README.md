# 📈 Financial Market Python

A comprehensive suite of Python-based financial analysis tools for portfolio management, risk assessment, strategy backtesting, and market data analysis. Provides practical implementations of modern portfolio theory, risk metrics, and quantitative trading strategies, designed for both learning and real-world application.

## Getting Started

To get started, ensure you have Python and [uv](https://docs.astral.sh/uv/) installed on your system. Once both are set up, follow these steps to configure the project:

### Running

Clone this repository to your local machine:

```bash
git clone https://github.com/gabrielpalassi/FinancialMarketPython.git
```

Navigate to the repository folder:

```bash
cd FinancialMarketPython
```

Install dependencies using uv:

```bash
uv sync
```

Now you're ready to use the programs!

```bash
uv run main.py
```

## Programs Overview

Below are the financial analysis tools available in this repository. Each program provides detailed instructions when executed.

### Portfolio Backtest

Backtest a weighted portfolio to evaluate historical performance. This tool calculates cumulative returns for your entire portfolio and compares it against individual asset performance, providing insights into how your asset allocation performed over time.

<img src="./images/portfolio-backtest.png" width=612.5>

### Markowitz Portfolio Optimization

Optimize portfolio asset allocation using Modern Portfolio Theory. Visualize the efficient frontier and find optimal portfolio weights based on three strategies: maximizing the Sharpe ratio for best risk-adjusted returns, targeting a specific expected return with minimal risk, or maximizing returns within a defined risk tolerance.

<img src="./images/markowitz-optimization.png" width=612.5>

### Drawdown Calculator

Analyze drawdown patterns to understand potential losses from peak values. This tool calculates and visualizes the maximum drawdown for individual assets or entire portfolios, helping you assess historical downside risk.

<img src="./images/drawdown.png" width=612.5>

### Value at Risk (VaR) Calculator

Calculate Value at Risk using historical simulation methodology. Estimate potential losses at customizable confidence levels (e.g., 95%, 99%) for individual assets or portfolios across daily, monthly, and yearly periods, providing a comprehensive risk assessment.

<img src="./images/value-at-risk.png" width=612.5>

### Brazilian Central Bank Historical Data

Access and analyze historical economic data from the Brazilian Central Bank (Banco Central do Brasil). Query various indicators including interest rates (SELIC), inflation metrics (IPCA, IGP-M), and exchange rates to support macroeconomic analysis.

<img src="./images/bcb-historical-data.png" width=612.5>

### Brazilian Central Bank Market Expectations

Retrieve market expectations data compiled by the Brazilian Central Bank through its FOCUS survey. Analyze consensus forecasts for key economic indicators such as interest rates, inflation, exchange rates, and GDP growth to inform investment decisions.

<img src="./images/bcb-market-expectations.png" width=612.5>

### Last Month Performance Method Backtest

Evaluate a momentum-based investment strategy that allocates capital based on prior month performance. This model invests in IBOV (Brazilian stock index) when it outperformed CDI (Brazilian risk-free rate) in the previous month, and switches to CDI otherwise.

<img src="./images/lmp-method-backtest.png" width=612.5>

### Moving Average Method Backtest

Test a trend-following strategy using moving averages as entry and exit signals. This model invests in IBOV when the previous month's closing price exceeds the moving average, indicating an uptrend, and allocates to CDI during downtrends for capital preservation.

<img src="./images/ma-method-backtest.png" width=612.5>

## Contributing

We welcome contributions to this repository. If you have ideas for new programs, bug fixes, or improvements, please open an issue or submit a pull request.
