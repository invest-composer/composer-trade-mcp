"""
Main MCP server implementation for Composer.
"""
from typing import List, Dict, Any
import httpx
import os

from fastmcp import FastMCP
from .schemas import SymphonyScore, validate_symphony_score, AccountResponse, AccountHoldingResponse, DvmCapital, Legend, BacktestResponse
from .utils import parse_backtest_output

BASE_URL = "https://public-api-gateway-599937284915.us-central1.run.app"
# BASE_URL = "https://api.composer.trade"

# Create a server instance
mcp = FastMCP(name="Composer MCP Server")

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

def main():
    """Main entry point for the composer-mcp-server."""
    mcp.run() 