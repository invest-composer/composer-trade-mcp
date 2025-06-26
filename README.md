
<div class="title-block" style="text-align: center;" align="center">

  [![Twitter](https://img.shields.io/badge/Twitter-@ComposerTrade-000000.svg?style=for-the-badge&logo=x&labelColor=000)](https://x.com/composertrade)
  [![PyPI](https://img.shields.io/badge/PyPI-composer--mcp-000000.svg?style=for-the-badge&logo=pypi&labelColor=000)](https://pypi.org/project/composer-mcp-server)
  [![Reddit Community](https://img.shields.io/badge/reddit-r/ComposerTrade-000000.svg?style=for-the-badge&logo=reddit&labelColor=000)](https://www.reddit.com/r/ComposerTrade)

</div>


<p align="center">
  Official <a href="https://www.composer.trade">Composer</a> Model Context Protocol (MCP) server that allows MCP-enabled LLMs like Claude Desktop, Cursor, OpenAI Agents and others to validate investment ideas via backtests and even trade multiple strategies (called "symphonies") in parallel to compare their live performance.
</p>

## Features
- **Create automated investing strategies**
  - Use indicators like Relative Strength Index (RSI), Moving Average (MA), and Exponential Moving Average (EMA) with a diverse range of equity and crypto offerings to build your ideal portfolio.
  - Don't just make one-off trades. Composer symphonies constantly monitor the market and rebalance accordingly.
  - Try asking Claude: "_Build me a crypto strategy with a maximum drawdown of 30% or less._"
- **Backtest your ideas**
  - Our Backtesting API provides a fast feedback loop for AI to iterate and validate its hypotheses.
  - Try asking Claude: "_Compare the strategy's performance against the S&P 500. Plot the results._"
- **Monitor performance** (requires [API Key](https://github.com/invest-composer/composer-mcp-server?tab=readme-ov-file#getting-your-api-key))
  - View performance statistics for your overall account as well as for individual symphonies.
  - Try asking Claude: "_Identify my best-performing symphonies. Analyze why they are working._"
- **Control your investments** (requires API Key + [Composer subscription](https://www.composer.trade/pricing))
  - Ask AI to analyze your investments and adjust your exposure accordingly!
  - Try asking Claude: "_Research the latest trends and news. Analyze my symphonies and determine whether I should increase / decrease my investments._"

## Quickstart with Claude Desktop
1. Install `uv` (Python package manager) with `curl -LsSf https://astral.sh/uv/install.sh | sh` or see the `uv` [repo](https://github.com/astral-sh/uv) for additional install methods.
1. Go to Claude > Settings > Developer > Edit Config > claude_desktop_config.json to include the following:

```
{
  "mcpServers": {
    "composer": {
      "command": "uvx",
      "args": [
        "--refresh",
        "--default-index", "https://test.pypi.org/simple/",
        "--index", "https://pypi.org/simple/",
        "--index-strategy", "unsafe-best-match",
        "composer-mcp-server@latest"
      ]
    }
  }
}
```
3. If this doesn't work, check the "[Spawn uvx ENOENT](https://github.com/invest-composer/composer-mcp-server?tab=readme-ov-file#mcp-composer-spawn-uvx-enoent)" section below.

If you're using Windows, you will have to enable "Developer Mode" in Claude Desktop to use the MCP server. Click "Help" in the hamburger menu at the top left and select "Enable Developer Mode".

## (WIP) Other MCP clients

For other clients like Cursor, run:
TODO

That's it. Your MCP client can now interact with Composer!

## Getting your API Key

An API key will be necessary to interact with your Composer account. For example, saving a Composer Symphony for later or viewing statistics about your Composer portfolio.

Trading a symphony will require a paid subscription, although you can always liquidate a position regardless of your subscription status. Composer also includes a 14-day free trial so you can try without any commitment.

Get your API key from [Composer](https://app.composer.trade) by following these steps:

1. If you haven't already done so, [create an account](https://app.composer.trade/register).
1. Open your "Accounts & Funding" page
   ![CleanShot 2025-06-25 at 14 28 12@2x](https://github.com/user-attachments/assets/7821f9f8-07ad-4fa9-87e0-24b29e6bbd87)
1. Request an API key
   <div align="center">
     <img src="https://github.com/user-attachments/assets/df6d8f23-de5a-44fb-a1c7-0bffa7e3173f" alt="CleanShot 2025-06-25 at 14 35 15@2x" width="500">
   </div>
1. Save your API key and secret
   <div align="center">
     <img src="https://github.com/user-attachments/assets/dd4d2828-6bfd-4db5-9fe0-6a78694f87c6" alt="CleanShot 2025-06-25 at 14 35 15@2x" width="500">
   </div>
1. Modify your `claude_desktop_config.json` to include your API key and secret:
```
{
  "mcpServers": {
    "composer": {
      "command": "uvx",
      "args": [
        "--refresh",
        "--default-index", "https://test.pypi.org/simple/",
        "--index", "https://pypi.org/simple/",
        "--index-strategy", "unsafe-best-match",
        "composer-mcp-server@latest"
      ],
      "env": {
        "COMPOSER_API_KEY": "<insert-your-api-key-here>"
        "COMPOSER_SECRET_KEY": "<insert-your-api-secret-here>"
      }
    }
  }
}
```

## Troubleshooting

Logs when running with Claude Desktop can be found at:

- **Windows**: `%APPDATA%\Claude\logs\mcp-server-composer.log`
- **macOS**: `~/Library/Logs/Claude/mcp-server-composer.log`

### MCP Composer: spawn uvx ENOENT

If you encounter the error "MCP Composer: spawn uvx ENOENT", confirm its absolute path by running this command in your terminal:

```bash
which uvx
```

Once you obtain the absolute path (e.g., `/usr/local/bin/uvx`), update your configuration to use that path (e.g., `"command": "/usr/local/bin/uvx"`). This ensures that the correct executable is referenced.
