"""
Main MCP server implementation for Composer.
"""
from typing import List, Dict, Any, Literal
import httpx
import os

from pydantic import Field

from fastmcp import FastMCP
from .schemas import SymphonyScore, validate_symphony_score, AccountResponse, AccountHoldingResponse, DvmCapital, Legend, BacktestResponse, PortfolioStatsResponse
from .utils import parse_backtest_output, truncate_text, epoch_ms_to_date

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
        return {"error": truncate_text(str(e), 1000), "response": truncate_text(response.text, 1000)}

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
        return {"error": truncate_text(str(e), 1000), "response": truncate_text(response.text, 1000)}

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
    If this returns an empty list, the user needs to complete their Composer onboarding on app.composer.trade.
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

@mcp.tool
def get_aggregate_portfolio_stats(account_uuid: str) -> PortfolioStatsResponse:
    """
    Get the aggregate portfolio statistics of a brokerage account.

    This is useful because each brokerage account in Composer can invest in multiple symphonies, each with their own stats.
    Output is a JSON object with the following fields:
    - portfolio_value: float. The total value of the portfolio (stocks + cash).
    - total_cash: float. The total cash in the account.
    - pending_deploys_cash: float. The cash that is pending investment into a symphony (investments don't occur until the trading period near market close)
    - total_unallocated_cash: float. The amount of cash that is not held in a symphony. This is the cash that is available for investment.
    - net_deposits: float. The sum of deposits into the account. Used to calculate naive cumulative return.
    - simple_return: float. The naive cumulative return of the portfolio. Equivalent to (portfolio_value - net_deposits) / net_deposits.
    - todays_dollar_change: float. The dollar difference between the portfolio value today and yesterday. IMPORTANT: This will include the effect of depositing/withdrawing funds. EX: If you had $1000 yesterday and deposited $100 today, todays_dollar_change will be $100, holding the share value constant.
    - todays_percent_change: float. The percent change of the portfolio today. Calculated as todays_dollar_change / portfolio_value.
    """
    url = f"{BASE_URL}/api/v0.1/portfolio/accounts/{account_uuid}/total-stats"
    response = httpx.get(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        }
    )
    data = response.json()
    if 'time_weighted_return' in data:
        del data['time_weighted_return']
    return data

@mcp.tool
def get_aggregate_symphony_stats(account_uuid: str) -> Dict:
    """
    Get stats for every symphony in a brokerage account.
    Contains aggregate stats such as the naive cumulative return ("simple_return"), time-weighted return, sharpe ratio, current holdings, etc.

    "deposit_adjusted_value" refers to the time-weighted value of the symphony.
    """
    url = f"{BASE_URL}/api/v0.1/portfolio/accounts/{account_uuid}/symphony-stats-meta"
    response = httpx.get(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        }
    )
    return response.json()

@mcp.tool
def get_symphony_daily_performance(account_uuid: str, symphony_id: str) -> Dict:
    """
    Get daily performance for a specific symphony in a brokerage account.
    Outputs a JSON object with the following fields:
    - dates: List[str]. The dates for which performance is available.
    - series: List[float]. The total value of the symphony on the given date.
    - deposit_adjusted_series: List[float]. The value of the symphony on the given date, adjusted for deposits and withdrawals. (AKA daily time-weighted value)
    """
    url = f"{BASE_URL}/api/v0.1/portfolio/accounts/{account_uuid}/symphonies/{symphony_id}"
    response = httpx.get(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        }
    )
    data = response.json()
    data['dates'] = [epoch_ms_to_date(d) for d in data['epoch_ms']]
    del data['epoch_ms']
    return data

@mcp.tool
def get_portfolio_daily_performance(account_uuid: str) -> Dict:
    """
    Get the daily performance for a brokerage account.
    Returns the value of the account portfolio over time.
    Outputs a JSON object with the following fields:
    - dates: List[str]. The dates for which performance is available.
    - series: List[float]. The total value of the portfolio on the given date.
    """
    url = f"{BASE_URL}/api/v0.1/portfolio/accounts/{account_uuid}/portfolio-history"
    response = httpx.get(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        }
    )
    data = response.json()
    data['dates'] = [epoch_ms_to_date(d) for d in data['epoch_ms']]
    del data['epoch_ms']
    return data

# FIXME: This tool is not working.
# Error message is:  "Expecting value: line 1 column 2 (char 1)" which is pretty vague.
@mcp.tool
def save_symphony(
    symphony_score: SymphonyScore,
    color: Literal["#AEC3C6", "#E3BC99", "#49D1E3", "#829DFF", "#FF6B6B", "#39D088", "#FC5100", "#FFBB38", "#FFB4ED", "#17BAFF", "#BA84FF"] ,
    hashtag: str = Field(description="Memorable hashtag for the symphony. Think of it like the ticker symbol of the symphony. (EX: '#BTD' for a symphony called 'Buy the Dip')"),
    asset_class: Literal["EQUITIES", "CRYPTO"] = "EQUITIES"
) -> Dict:
    """
    Save a symphony to the user's account. If successful, returns the symphony ID.
    """
    validated_score= validate_symphony_score(symphony_score)
    symphony = validated_score.model_dump()

    url = f"{BASE_URL}/api/v0.1/symphonies/"
    payload = {
        "name": symphony['name'],
        "asset_class": asset_class,
        "description": symphony['description'],
        "color": color,
        "hashtag": hashtag,
        "symphony": {"raw_value": symphony}
    }
    try:
        response = httpx.post(
            url,
            headers={
                "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
                "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
            },
            json=payload
        )
        return response.json()
    except Exception as e:
        payload_without_symphony = {k: v for k, v in payload.items() if k != "symphony"}
        return {"error": truncate_text(str(e), 1000), "payload": payload_without_symphony}

@mcp.tool
def update_saved_symphony(
    symphony_id: str,
    symphony_score: SymphonyScore,
    color: Literal["#AEC3C6", "#E3BC99", "#49D1E3", "#829DFF", "#FF6B6B", "#39D088", "#FC5100", "#FFBB38", "#FFB4ED", "#17BAFF", "#BA84FF"],
    hashtag: str = Field(description="Memorable hashtag for the symphony. Think of it like the ticker symbol of the symphony. (EX: '#BTD' for a symphony called 'Buy the Dip')"),
    asset_class: Literal["EQUITIES", "CRYPTO"] = "EQUITIES"
) -> Dict:
    """
    Update an existing symphony in the user's account. If successful, returns the updated symphony details.
    """
    validated_score = validate_symphony_score(symphony_score)
    symphony = validated_score.model_dump()

    url = f"{BASE_URL}/api/v0.1/symphonies/{symphony_id}"
    payload = {
        "name": symphony['name'],
        "asset_class": asset_class,
        "description": symphony['description'],
        "color": color,
        "hashtag": hashtag,
        "symphony": {"raw_value": symphony}
    }
    try:
        response = httpx.put(
            url,
            headers={
                "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
                "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
            },
            json=payload
        )
        return response.json()
    except Exception as e:
        payload_without_symphony = {k: v for k, v in payload.items() if k != "symphony"}
        return {"error": truncate_text(str(e), 1000), "payload": payload_without_symphony}

@mcp.tool
def get_saved_symphony(symphony_id: str) -> SymphonyScore:
    """
    Get a saved symphony.
    Useful when you are given a URL like "https://app.composer.trade/symphony/{<symphony_id>}/details"
    """
    url = f"{BASE_URL}/api/v0.1/symphonies/{symphony_id}/score"
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
