"""
Utility functions for parsing Composer API responses.
"""
from typing import Dict, List, Any
from datetime import datetime
from ..schemas.backtest_api import DvmCapital, Legend, BacktestResponse

def parse_stats(stats: Dict) -> Dict:
    """
    Parse the stats of a symphony backtest.
    """
    parsed_stats = {
        "annualized_rate_of_return": f"{round(stats.get('annualized_rate_of_return', 0) * 100, 2)}%",
        "benchmarks": {
            benchmark: parse_stats(benchmark_stats) for benchmark, benchmark_stats in stats.get("benchmarks", {}).items()
        },
        "calmar_ratio": round(stats.get("calmar_ratio", 0), 4),
        "sharpe_ratio": round(stats.get("sharpe_ratio", 0), 4),
        "cumulative_return": f"{round(stats.get('cumulative_return', 0) * 100, 2)}%",
        "trailing_one_year_return": f"{round(stats.get('trailing_one_year_return', 0) * 100, 2)}%",
        "trailing_one_month_return": f"{round(stats.get('trailing_one_month_return', 0) * 100, 2)}%",
        "trailing_three_month_return": f"{round(stats.get('trailing_three_month_return', 0) * 100, 2)}%",
        "max_drawdown": f"{round(stats.get('max_drawdown', 0) * 100, 2)}%",
        "standard_deviation": f"{round(stats.get('standard_deviation', 0) * 100, 2)}%",
    }
    # Process alpha and beta from percent section
    percent_stats = stats.get("percent", {})
    if percent_stats:
        parsed_stats["alpha"] = round(percent_stats.get("alpha", 0), 4)
        parsed_stats["beta"] = round(percent_stats.get("beta", 0), 4)
        parsed_stats["r_square"] = round(percent_stats.get("r_square", 0), 4)
        parsed_stats["pearson_r"] = round(percent_stats.get("pearson_r", 0), 4)
    return parsed_stats

def epoch_to_date(epoch: int) -> str:
    """
    Convert an epoch timestamp to a date string.
    """
    return datetime.utcfromtimestamp(epoch * 86400).strftime("%Y-%m-%d")

def epoch_ms_to_date(epoch_ms: int) -> str:
    """
    Convert an epoch timestamp to a date string.
    """
    return datetime.utcfromtimestamp(epoch_ms / 1000).strftime("%Y-%m-%d")

def parse_dvm_capital(dvm_capital: DvmCapital, legend: Legend) -> Dict[str, List[Any]]:
    """
    Parse the daily values of a symphony backtest.
    Returns a list of dictionaries where each dictionary represents a daily value row
    with cumulative returns since the first day (all series start at 0%).
    Example output:
    {"cumulative_return_date": ["2024-01-01", "2024-01-02", ...],
     "Big Tech momentum": [0, 1, ...],
     "SPY": [0, -1, ...]}
    """
    parsed_daily_values = {}

    # Collect all unique dates first
    all_dates = set()
    for values in dvm_capital.values():
        for day_num in values.keys():
            # Use UTC timestamp to match Java LocalDate.ofEpochDay behavior
            date_str = epoch_to_date(int(day_num))
            all_dates.add(date_str)

    # Sort dates
    sorted_dates = sorted(all_dates)

    # Create list of dictionaries for dataframe-friendly structure
    parsed_daily_values = {"cumulative_return_date": sorted_dates}
    first_day_values = {}

    for date in sorted_dates:

        for key, values in dvm_capital.items():
            # Replace key with legend name if it exists
            legend_entry = legend.get(key)
            display_key = legend_entry.name if legend_entry else key
            if display_key not in parsed_daily_values:
                parsed_daily_values[display_key] = []

            # Find the corresponding value for this date
            value = None
            for day_num, val in values.items():
                date_str = epoch_to_date(int(day_num))
                if date_str == date:
                    value = val
                    break

            # Calculate cumulative return since first day
            if value is not None and display_key not in first_day_values:
                # Set the first value as the base for cumulative returns
                first_day_values[display_key] = value
            if value is not None and display_key in first_day_values:
                # Calculate cumulative return since first day
                first_day_value = first_day_values[display_key]
                cumulative_return = ((value - first_day_value) / first_day_value) * 100
                parsed_daily_values[display_key].append(round(cumulative_return, 2))
            else:
                parsed_daily_values[display_key].append(None)

    return parsed_daily_values

def parse_backtest_output(backtest: BacktestResponse, include_daily_values: bool = False) -> Dict:
    """
    Parse the output of a symphony backtest.
    """
    output = {
        "data_warnings": backtest.data_warnings,
        "first_day": epoch_to_date(backtest.first_day) if backtest.first_day else None,
        "first_day_value": f"${backtest.capital:,.2f}" if backtest.capital else None,
        "last_market_day": epoch_to_date(backtest.last_market_day) if backtest.last_market_day else None,
        "last_market_days_shares": {
            k: v for k, v in (backtest.last_market_days_holdings or {}).items()
            if k != "$USD" and v != 0.0
        },
        "last_market_days_value": f"${backtest.last_market_days_value:,.2f}" if backtest.last_market_days_value else None,
        "stats": parse_stats(backtest.stats or {}),
    }
    if include_daily_values and backtest.dvm_capital and backtest.legend:
        output["daily_values"] = parse_dvm_capital(backtest.dvm_capital, backtest.legend)
    return output 