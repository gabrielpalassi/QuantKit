#
# Imports
#

import sys
import subprocess
from pathlib import Path
import os

# Local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from utils import print_with_separator

#
# Functions
#


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def display_menu():
    clear_screen()
    print_with_separator(
        [
            "Portfolio Analysis",
            "   1. Portfolio Backtest",
            "   2. Markowitz Portfolio Optimization",
            "   3. Drawdown Calculator",
            "   4. Value at Risk (VaR) Calculator",
            "Market Data",
            "   5. Brazilian Central Bank Historical Data",
            "   6. Brazilian Central Bank Market Expectations",
            "Strategies",
            "   7. Relative Momentum Allocation Backtest",
            "   8. Moving Average Allocation Backtest",
            "   9. Bollinger Bands Backtest",
            "Other",
            "   0. Exit",
        ]
    )


def run_script(script_path: Path):
    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
    except KeyboardInterrupt:
        print("Script interrupted by user.")


def get_script_path(category: str, script_name: str) -> Path:
    base_path = Path(__file__).parent / "src" / category
    return base_path / script_name


#
# Main
#


def main():
    scripts = {
        "1": ("portfolio_analysis", "portfolio_backtest.py", "Portfolio Backtest"),
        "2": ("portfolio_analysis", "markowitz_optimization.py", "Markowitz Optimization"),
        "3": ("portfolio_analysis", "drawdown.py", "Drawdown Calculator"),
        "4": ("portfolio_analysis", "value_at_risk.py", "Value at Risk"),
        "5": ("market_data", "bcb_historical_data.py", "BCB Historical Data"),
        "6": ("market_data", "bcb_market_expectations.py", "BCB Market Expectations"),
        "7": ("strategies", "relative_momentum.py", "Relative Momentum Allocation Backtest"),
        "8": ("strategies", "moving_average.py", "Moving Average Allocation Backtest"),
        "9": ("strategies", "bollinger.py", "Bollinger Bands Backtest"),
    }

    while True:
        display_menu()
        choice = input("Select an option (0-9): ").strip()

        if choice == "0":
            clear_screen()
            sys.exit(0)

        if choice in scripts:
            category, script_name, display_name = scripts[choice]
            script_path = get_script_path(category, script_name)

            if not script_path.exists():
                print(f"Script not found at {script_path}")
                input("Press Enter to continue...")
                continue

            clear_screen()
            print(f"Running {display_name}...")

            run_script(script_path)
            input("Press Enter to return to menu...")
        else:
            print("Invalid option. Please select a number between 0 and 9.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        sys.exit(0)
