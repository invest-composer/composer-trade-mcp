import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import axios from 'axios';
import { z } from 'zod';

import { 
  SymphonyScore, 
  validateSymphonyScore,
  AccountResponse,
  AccountHoldingResponse,
  PortfolioStatsResponse,
  BacktestResponse
} from './types/index.js';
import { getOptionalHeaders, getRequiredHeaders } from './utils/auth.js';
import { parseBacktestOutput, truncateText, epochMsToDate } from './utils/parsers.js';

const BASE_URL = "https://public-api-gateway-599937284915.us-central1.run.app";
// const BASE_URL = "https://api.composer.trade";

// Create an MCP server
const server = new McpServer({
  name: "Composer MCP Server",
  version: "1.0.0"
});

// Register tools using the proper MCP SDK pattern
server.registerTool(
  "backtest_symphony_by_id",
  {
    title: "Backtest Symphony by ID",
    description: "Backtest a symphony given its ID. Use `include_daily_values=False` to reduce the response size (default is True). Daily values are cumulative returns since the first day of the backtest (i.e., 19 means 19% cumulative return since the first day). If start_date is not provided, the backtest will start from the earliest backtestable date. You should default to backtesting from the first day of the year in order to reduce the response size. If end_date is not provided, the backtest will end on the last day with data. After calling this tool, visualize the results. daily_values can be easily loaded into a pandas dataframe for plotting.",
    inputSchema: {
      symphony_id: z.string(),
      start_date: z.string().optional(),
      end_date: z.string().optional(),
      include_daily_values: z.boolean().default(true),
      apply_reg_fee: z.boolean().default(true),
      apply_taf_fee: z.boolean().default(true),
      broker: z.string().default("ALPACA_WHITE_LABEL"),
      capital: z.number().default(10000),
      slippage_percent: z.number().default(0.0001),
      spread_markup: z.number().default(0.002),
      benchmark_tickers: z.array(z.string()).default(["SPY"])
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/symphonies/${params.symphony_id}/backtest`;
    const requestParams: any = {
      apply_reg_fee: params.apply_reg_fee,
      apply_taf_fee: params.apply_taf_fee,
      broker: params.broker,
      capital: params.capital,
      slippage_percent: params.slippage_percent,
      spread_markup: params.spread_markup,
      benchmark_tickers: params.benchmark_tickers,
    };

    if (params.start_date) requestParams.start_date = params.start_date;
    if (params.end_date) requestParams.end_date = params.end_date;

    try {
      const response = await axios.post(url, requestParams, {
        headers: getOptionalHeaders()
      });
      
      const output = response.data;
      output.capital = params.capital;

      if (output.stats) {
        return {
          content: [{
            type: "text",
            text: JSON.stringify(parseBacktestOutput(output as BacktestResponse, params.include_daily_values, output.capital))
          }]
        };
      } else {
        return {
          content: [{
            type: "text",
            text: JSON.stringify(output)
          }]
        };
      }
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "backtest_symphony",
  {
    title: "Backtest Symphony",
    description: "Backtest a symphony given its score. Use `include_daily_values=False` to reduce the response size (default is True). Daily values are cumulative returns since the first day of the backtest (i.e., 19 means 19% cumulative return since the first day). If start_date is not provided, the backtest will start from the earliest backtestable date. You should default to backtesting from the first day of the year in order to reduce the response size. If end_date is not provided, the backtest will end on the last day with data. After calling this tool, visualize the results. daily_values can be easily loaded into a pandas dataframe for plotting.",
    inputSchema: {
      symphony_score: z.any(), // We'll validate this manually
      start_date: z.string().optional(),
      end_date: z.string().optional(),
      include_daily_values: z.boolean().default(true),
      apply_reg_fee: z.boolean().default(true),
      apply_taf_fee: z.boolean().default(true),
      broker: z.string().default("ALPACA_WHITE_LABEL"),
      capital: z.number().default(10000),
      slippage_percent: z.number().default(0.0001),
      spread_markup: z.number().default(0.002),
      benchmark_tickers: z.array(z.string()).default(["SPY"])
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/backtest`;
    const validatedScore = validateSymphonyScore(params.symphony_score);
    const requestParams: any = {
      symphony: { raw_value: validatedScore },
      apply_reg_fee: params.apply_reg_fee,
      apply_taf_fee: params.apply_taf_fee,
      broker: params.broker,
      capital: params.capital,
      slippage_percent: params.slippage_percent,
      spread_markup: params.spread_markup,
      benchmark_tickers: params.benchmark_tickers,
    };

    if (params.start_date) requestParams.start_date = params.start_date;
    if (params.end_date) requestParams.end_date = params.end_date;

    try {
      const response = await axios.post(url, requestParams, {
        headers: getOptionalHeaders()
      });
      
      const output = response.data;
      output.capital = params.capital;

      if (output.stats) {
        return {
          content: [{
            type: "text",
            text: JSON.stringify(parseBacktestOutput(output as BacktestResponse, params.include_daily_values, output.capital))
          }]
        };
      } else {
        return {
          content: [{
            type: "text",
            text: JSON.stringify(output)
          }]
        };
      }
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "create_symphony",
  {
    title: "Create Symphony",
    description: "Create a symphony from a symphony score",
    inputSchema: {
      symphony_score: z.any() // We'll validate this manually
    }
  },
  async (params) => {
    const validatedScore = validateSymphonyScore(params.symphony_score);
    return {
      content: [{
        type: "text",
        text: JSON.stringify(validatedScore)
      }]
    };
  }
);

server.registerTool(
  "list_accounts",
  {
    title: "List Accounts",
    description: "List all accounts for the authenticated user",
    inputSchema: {}
  },
  async () => {
    const url = `${BASE_URL}/api/v0.1/accounts/list`;
    
    try {
      const response = await axios.get(url, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data.accounts)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "get_account_holdings",
  {
    title: "Get Account Holdings",
    description: "Get holdings for a specific account",
    inputSchema: {
      account_uuid: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/accounts/${params.account_uuid}/holdings`;
    
    try {
      const response = await axios.get(url, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "get_aggregate_portfolio_stats",
  {
    title: "Get Aggregate Portfolio Stats",
    description: "Get aggregate portfolio statistics for an account",
    inputSchema: {
      account_uuid: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/portfolio/accounts/${params.account_uuid}/total-stats`;
    
    try {
      const response = await axios.get(url, {
        headers: getRequiredHeaders()
      });
      
      const data = response.data;
      if (data.time_weighted_return) {
        delete data.time_weighted_return;
      }
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "get_aggregate_symphony_stats",
  {
    title: "Get Aggregate Symphony Stats",
    description: "Get aggregate symphony statistics for an account",
    inputSchema: {
      account_uuid: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/portfolio/accounts/${params.account_uuid}/symphony-stats-meta`;
    
    try {
      const response = await axios.get(url, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "get_symphony_daily_performance",
  {
    title: "Get Symphony Daily Performance",
    description: "Get daily performance data for a specific symphony in an account",
    inputSchema: {
      account_uuid: z.string(),
      symphony_id: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/portfolio/accounts/${params.account_uuid}/symphonies/${params.symphony_id}`;
    
    try {
      const response = await axios.get(url, {
        headers: getRequiredHeaders()
      });
      
      const data = response.data;
      data.dates = data.epoch_ms.map((epoch: number) => epochMsToDate(epoch));
      delete data.epoch_ms;
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "get_portfolio_daily_performance",
  {
    title: "Get Portfolio Daily Performance",
    description: "Get daily performance data for an entire portfolio",
    inputSchema: {
      account_uuid: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/portfolio/accounts/${params.account_uuid}/portfolio-history`;
    
    try {
      const response = await axios.get(url, {
        headers: getRequiredHeaders()
      });
      
      const data = response.data;
      data.dates = data.epoch_ms.map((epoch: number) => epochMsToDate(epoch));
      delete data.epoch_ms;
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "save_symphony",
  {
    title: "Save Symphony",
    description: "Save a symphony to the user's account",
    inputSchema: {
      symphony_score: z.any(), // We'll validate this manually
      color: z.string(),
      hashtag: z.string(),
      asset_class: z.string().optional()
    }
  },
  async (params) => {
    const validatedScore = validateSymphonyScore(params.symphony_score);
    const symphony = validatedScore;

    const url = `${BASE_URL}/api/v0.1/symphonies/`;
    const payload = {
      name: symphony.name,
      asset_class: params.asset_class ?? "EQUITIES",
      description: symphony.description,
      color: params.color,
      hashtag: params.hashtag,
      symphony: { raw_value: symphony }
    };

    try {
      const response = await axios.post(url, payload, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      const payloadWithoutSymphony = Object.fromEntries(
        Object.entries(payload).filter(([k]) => k !== "symphony")
      );
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            payload: payloadWithoutSymphony
          })
        }]
      };
    }
  }
);

server.registerTool(
  "update_saved_symphony",
  {
    title: "Update Saved Symphony",
    description: "Update an existing saved symphony",
    inputSchema: {
      symphony_id: z.string(),
      symphony_score: z.any(), // We'll validate this manually
      color: z.string(),
      hashtag: z.string(),
      asset_class: z.string().optional()
    }
  },
  async (params) => {
    const validatedScore = validateSymphonyScore(params.symphony_score);
    const symphony = validatedScore;

    const url = `${BASE_URL}/api/v0.1/symphonies/${params.symphony_id}`;
    const payload = {
      name: symphony.name,
      asset_class: params.asset_class ?? "EQUITIES",
      description: symphony.description,
      color: params.color,
      hashtag: params.hashtag,
      symphony: { raw_value: symphony }
    };

    try {
      const response = await axios.put(url, payload, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      const payloadWithoutSymphony = Object.fromEntries(
        Object.entries(payload).filter(([k]) => k !== "symphony")
      );
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            payload: payloadWithoutSymphony
          })
        }]
      };
    }
  }
);

server.registerTool(
  "get_saved_symphony",
  {
    title: "Get Saved Symphony",
    description: "Get a saved symphony by ID",
    inputSchema: {
      symphony_id: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/symphonies/${params.symphony_id}/score`;
    
    try {
      const response = await axios.get(url, {
        headers: getOptionalHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "get_market_hours",
  {
    title: "Get Market Hours",
    description: "Get current market hours information",
    inputSchema: {}
  },
  async () => {
    const url = `${BASE_URL}/api/v0.1/deploy/market-hours`;
    
    try {
      const response = await axios.get(url, {
        headers: getOptionalHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "invest_in_symphony",
  {
    title: "Invest in Symphony",
    description: "Invest money in a symphony",
    inputSchema: {
      account_uuid: z.string(),
      symphony_id: z.string(),
      amount: z.number()
    }
  },
  async (params) => {
    if (params.amount <= 0) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({ error: "Amount must be greater than 0" })
        }]
      };
    }

    const url = `${BASE_URL}/api/v0.1/deploy/accounts/${params.account_uuid}/symphonies/${params.symphony_id}/invest`;
    
    try {
      const response = await axios.post(url, { amount: params.amount }, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "withdraw_from_symphony",
  {
    title: "Withdraw from Symphony",
    description: "Withdraw money from a symphony",
    inputSchema: {
      account_uuid: z.string(),
      symphony_id: z.string(),
      amount: z.number()
    }
  },
  async (params) => {
    if (params.amount >= 0) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({ error: "Amount must be less than 0" })
        }]
      };
    }

    const url = `${BASE_URL}/api/v0.1/deploy/accounts/${params.account_uuid}/symphonies/${params.symphony_id}/withdraw`;
    
    try {
      const response = await axios.post(url, { amount: params.amount }, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "cancel_invest_or_withdraw",
  {
    title: "Cancel Invest or Withdraw",
    description: "Cancel a pending invest or withdraw request",
    inputSchema: {
      account_uuid: z.string(),
      deploy_id: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/deploy/accounts/${params.account_uuid}/deploys/${params.deploy_id}`;
    
    try {
      const response = await axios.delete(url, {
        headers: getRequiredHeaders()
      });
      
      if (response.status === 204) {
        return {
          content: [{
            type: "text",
            text: "Successfully canceled invest or withdraw request"
          }]
        };
      } else {
        return {
          content: [{
            type: "text",
            text: JSON.stringify(response.data)
          }]
        };
      }
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "skip_automated_rebalance_for_symphony",
  {
    title: "Skip Automated Rebalance for Symphony",
    description: "Skip the next automated rebalance for a symphony",
    inputSchema: {
      account_uuid: z.string(),
      symphony_id: z.string(),
      skip: z.boolean().optional()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/deploy/accounts/${params.account_uuid}/symphonies/${params.symphony_id}/skip-automated-rebalance`;
    
    try {
      const response = await axios.post(url, { skip: params.skip ?? true }, {
        headers: getRequiredHeaders()
      });
      
      if (response.status === 204) {
        return {
          content: [{
            type: "text",
            text: "Successfully skipped next automated rebalance"
          }]
        };
      } else {
        return {
          content: [{
            type: "text",
            text: JSON.stringify(response.data)
          }]
        };
      }
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "go_to_cash_for_symphony",
  {
    title: "Go to Cash for Symphony",
    description: "Move all holdings in a symphony to cash",
    inputSchema: {
      account_uuid: z.string(),
      symphony_id: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/deploy/accounts/${params.account_uuid}/symphonies/${params.symphony_id}/go-to-cash`;
    
    try {
      const response = await axios.post(url, {}, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "rebalance_symphony_now",
  {
    title: "Rebalance Symphony Now",
    description: "Rebalance a symphony immediately",
    inputSchema: {
      account_uuid: z.string(),
      symphony_id: z.string(),
      rebalance_request_uuid: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/deploy/accounts/${params.account_uuid}/symphonies/${params.symphony_id}/rebalance`;
    
    try {
      const response = await axios.post(url, { 
        rebalance_request_uuid: params.rebalance_request_uuid 
      }, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "liquidate_symphony",
  {
    title: "Liquidate Symphony",
    description: "Liquidate all holdings in a symphony",
    inputSchema: {
      account_uuid: z.string(),
      symphony_id: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/deploy/accounts/${params.account_uuid}/symphonies/${params.symphony_id}/liquidate`;
    
    try {
      const response = await axios.post(url, {}, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "preview_rebalance_for_user",
  {
    title: "Preview Rebalance for User",
    description: "Preview rebalance for all user accounts",
    inputSchema: {}
  },
  async () => {
    const url = `${BASE_URL}/api/v0.1/dry-run`;
    
    try {
      const response = await axios.post(url, {}, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "preview_rebalance_for_symphony",
  {
    title: "Preview Rebalance for Symphony",
    description: "Preview rebalance for a specific symphony",
    inputSchema: {
      account_uuid: z.string(),
      symphony_id: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/dry-run/trade-preview/${params.symphony_id}`;
    
    try {
      const response = await axios.post(url, { 
        broker_account_uuid: params.account_uuid 
      }, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "execute_single_trade",
  {
    title: "Execute Single Trade",
    description: "Execute a single trade order",
    inputSchema: {
      account_uuid: z.string(),
      type: z.string(),
      symbol: z.string(),
      time_in_force: z.string(),
      notional: z.number().optional(),
      quantity: z.number().optional()
    }
  },
  async (params) => {
    if (!params.notional && !params.quantity) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({ error: "One of notional or quantity must be provided" })
        }]
      };
    }

    const url = `${BASE_URL}/api/v0.1/trading/accounts/${params.account_uuid}/order-requests`;
    const payload: any = {
      type: params.type,
      symbol: params.symbol,
      time_in_force: params.time_in_force
    };

    if (params.notional !== undefined) payload.notional = params.notional;
    if (params.quantity !== undefined) payload.quantity = params.quantity;

    try {
      const response = await axios.post(url, payload, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

server.registerTool(
  "cancel_single_trade",
  {
    title: "Cancel Single Trade",
    description: "Cancel a single trade order",
    inputSchema: {
      account_uuid: z.string(),
      order_request_id: z.string()
    }
  },
  async (params) => {
    const url = `${BASE_URL}/api/v0.1/trading/accounts/${params.account_uuid}/order-requests/${params.order_request_id}`;
    
    try {
      const response = await axios.delete(url, {
        headers: getRequiredHeaders()
      });
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.data)
        }]
      };
    } catch (error: any) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: truncateText(error.message, 1000),
            response: truncateText(error.response?.data || '', 1000)
          })
        }]
      };
    }
  }
);

// Main function
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error); 