"""
Main entry point for the composer-mcp-server application.
"""
from typing import List, Dict, Any
from src.schemas.symphony_score_schema import SymphonyScore, validate_symphony_score
from src.schemas.asset_classes_schema import AssetClasses
from src.schemas.api import AccountResponse, AccountHoldingResponse
from src.schemas.backtest_api import DvmCapital, Legend, BacktestResponse
from fastmcp import FastMCP
import httpx
import os
from datetime import datetime

BASE_URL = "https://public-api-gateway-599937284915.us-central1.run.app"
# BASE_URL = "https://api.composer.trade"

# Create a server instance
mcp = FastMCP(name="Composer MCP Server")

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

@mcp.tool
def backtest_symphony_by_id(symphony_id: str,
                            start_date: str = None,
                            end_date: str = None,
                            include_daily_values: bool = True,
                            apply_reg_fee: bool = True,
                            apply_taf_fee: bool = True,
                            broker: str = "ALPACA_WHITE_LABEL",
                            capital: float = 10000,
                            slippage_percent: float = 0.0001,
                            spread_markup: float = 0.002,
                            benchmark_tickers: List[str] = ["SPY"]) -> Dict:
    """
    Backtest a symphony given its ID.
    Use `include_daily_values=False` to reduce the response size (default is True).
    Daily values are cumulative returns since the first day of the backtest (i.e., 19 means 19% cumulative return since the first day).
    If start_date is not provided, the backtest will start from the earliest backtestable date.
    You should default to backtesting from the first day of the year in order to reduce the response size.
    If end_date is not provided, the backtest will end on the last day with data.

    After calling this tool, visualize the results. daily_values can be easily loaded into a pandas dataframe for plotting.
    """
    url = f"{BASE_URL}/api/v0.1/symphonies/{symphony_id}/backtest"
    params = {
        "apply_reg_fee": apply_reg_fee,
        "apply_taf_fee": apply_taf_fee,
        "broker": broker,
        "capital": capital,
        "slippage_percent": slippage_percent,
        "spread_markup": spread_markup,
        "benchmark_tickers": benchmark_tickers,
    }
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    response = httpx.post(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        },
        json=params
    )
    output = response.json()
    try:
        if output.get("stats"):
            return parse_backtest_output(BacktestResponse(**output), include_daily_values)
        else:
            return output
    except Exception as e:
        return {"error": str(e)} # temporary
        # return response.text

@mcp.tool
def backtest_symphony(symphony_score: SymphonyScore,
                            start_date: str = None,
                            end_date: str = None,
                            include_daily_values: bool = True,
                            apply_reg_fee: bool = True,
                            apply_taf_fee: bool = True,
                            broker: str = "ALPACA_WHITE_LABEL",
                            capital: float = 10000,
                            slippage_percent: float = 0.0001,
                            spread_markup: float = 0.002,
                            benchmark_tickers: List[str] = ["SPY"]) -> Dict:
    """
    Backtest a symphony that was created with `create_symphony`.
    Use `include_daily_values=False` to reduce the response size (default is True).
    Daily values are cumulative returns since the first day of the backtest (i.e., 19 means 19% cumulative return since the first day).
    If start_date is not provided, the backtest will start from the earliest backtestable date.
    You should default to backtesting from the first day of the year in order to reduce the response size.
    If end_date is not provided, the backtest will end on the last day with data.

    After calling this tool, visualize the results. daily_values can be easily loaded into a pandas dataframe for plotting.
    """
    url = f"{BASE_URL}/api/v0.1/backtest"
    validated_score= validate_symphony_score(symphony_score)
    params = {
        "symphony": {"raw_value": validated_score.model_dump()},
        "apply_reg_fee": apply_reg_fee,
        "apply_taf_fee": apply_taf_fee,
        "broker": broker,
        "capital": capital,
        "slippage_percent": slippage_percent,
        "spread_markup": spread_markup,
        "benchmark_tickers": benchmark_tickers,
    }
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    response = httpx.post(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        },
        json=params
    )
    try:
        output = response.json()
        if output.get("stats"):
            return parse_backtest_output(BacktestResponse(**output), include_daily_values)
        else:
            return output
    except Exception as e:
        return {"error": str(e)} # temporary
        # return response.text

@mcp.tool
def create_symphony(symphony_score: SymphonyScore) -> SymphonyScore:
    """
    Composer is a DSL for constructing automated trading strategies. It can only enter long positions and cannot stay in cash.

    ### Available Data
    - US Equity Adjusted Close prices and Crypto prices (daily granularity at 4PM ET)

    Before creating a symphony, check with the user for the asset classes they want to use.
    Assume equities are the default asset class.
    Note that symphonies with both equities and crypto must use daily or threshold (rebalance=None) rebalancing.

    After calling this tool, attempt to visualize the symphony using any other functionality at your disposal.
    If you can't visualize the symphony, resort to a mermaid diagram.
    """
    validated_score= validate_symphony_score(symphony_score)
    return validated_score.model_dump_json()

# Could be a resource but Claude Desktop doesn't autonomously call resources yet.
@mcp.tool
def list_accounts() -> List[AccountResponse]:
    """
    List all brokerage accounts available to the Composer user.
    Account-related tools need to be called with the account_uuid of the account you want to use.
    This tool returns a list of accounts and their UUIDs.
    """
    url = f"{BASE_URL}/api/v0.1/accounts/list"
    response = httpx.get(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        }
    )
    return response.json()["accounts"]

@mcp.tool
def get_account_holdings(account_uuid: str) -> List[AccountHoldingResponse]:
    """
    Get the holdings of a brokerage account.
    """
    url = f"{BASE_URL}/api/v0.1/accounts/{account_uuid}/holdings"
    response = httpx.get(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        }
    )
    return response.json()

if __name__ == "__main__":
    mcp.run()
