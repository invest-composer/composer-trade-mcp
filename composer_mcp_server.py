"""
Main entry point for the composer-mcp-server application.
"""
from typing import List, Dict
from src.schemas.symphony_score_schema import SymphonyScore, validate_symphony_score
from src.schemas.asset_classes_schema import AssetClasses
from src.schemas.api import AccountResponse, AccountHoldingResponse
from fastmcp import FastMCP
import httpx
import os

# BASE_URL = "https://public-api-gateway-599937284915.us-central1.run.app"
BASE_URL = "https://api.composer.trade"

# Create a server instance
mcp = FastMCP(name="Composer MCP Server")


# TODO: Use Tool Transformation to adapt the OpenAPI spec to the MCP server.

@mcp.tool
def backtest_symphony(symphony_score: SymphonyScore) -> Dict:
    """
    Backtest a symphony that was created with `create_symphony`.
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
