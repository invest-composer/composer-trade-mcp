import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { validateSymphonyScore } from './types/index.js';
import { getOptionalHeaders, getRequiredHeaders } from './utils/auth.js';
import { parseBacktestOutput, truncateText, epochMsToDate } from './utils/parsers.js';

// Test the validation function
const testSymphony = {
  step: "root",
  name: "Test Symphony",
  description: "A test symphony",
  rebalance: "daily",
  children: [
    {
      step: "wt-cash-equal",
      children: [
        {
          ticker: "SPY",
          exchange: "XNAS",
          name: "SPDR S&P 500 ETF Trust",
          step: "asset"
        }
      ]
    }
  ]
};

async function testValidation() {
  try {
    const validated = validateSymphonyScore(testSymphony);
    console.log("✅ Symphony validation works:", validated.name);
  } catch (error) {
    console.error("❌ Symphony validation failed:", error);
  }
}

async function testUtilityFunctions() {
  console.log("✅ Truncate text:", truncateText("This is a long text", 10));
  console.log("✅ Epoch to date:", epochMsToDate(Date.now()));
}

async function testHeaders() {
  try {
    const optionalHeaders = getOptionalHeaders();
    console.log("✅ Optional headers:", optionalHeaders);
  } catch (error) {
    console.log("✅ Optional headers (no env vars):", {});
  }
}

async function testMCPClient() {
  const transport = new StdioClientTransport({
    command: "node",
    args: ["dist/index.js"]
  });

  const client = new Client({
    name: "composer-mcp-test-client",
    version: "1.0.0"
  });

  try {
    await client.connect(transport);
    console.log("✅ Connected to MCP server");

    // Test list_accounts tool
    console.log("Testing list_accounts tool...");
    const accountsResult = await client.callTool({
      name: "list_accounts",
      arguments: {}
    });
    console.log("✅ List accounts result:", accountsResult);

    // Test backtest_symphony_by_id tool
    console.log("Testing backtest_symphony_by_id tool...");
    const backtestResult = await client.callTool({
      name: "backtest_symphony_by_id",
      arguments: {
        symphony_id: "czfd4djei67NNWccuLx1",
        start_date: "2025-06-10",
        include_daily_values: true,
        capital: 100000
      }
    });
    console.log("✅ Backtest result:", backtestResult);

    // Test get_market_hours tool
    console.log("Testing get_market_hours tool...");
    const marketHoursResult = await client.callTool({
      name: "get_market_hours",
      arguments: {}
    });
    console.log("✅ Market hours result:", marketHoursResult);

    // Test create_symphony tool with a simple symphony
    console.log("Testing create_symphony tool...");
    const createSymphonyResult = await client.callTool({
      name: "create_symphony",
      arguments: {
        symphony_score: {
          step: "root",
          name: "Simple Test Symphony",
          description: "A simple test symphony for MCP testing",
          rebalance: "daily",
          children: [
            {
              step: "wt-cash-equal",
              children: [
                {
                  ticker: "SPY",
                  exchange: "XNAS",
                  name: "SPDR S&P 500 ETF Trust",
                  step: "asset"
                }
              ]
            }
          ]
        }
      }
    });
    console.log("✅ Create symphony result:", createSymphonyResult);

  } catch (error) {
    console.error("❌ MCP client test failed:", error);
  } finally {
    await client.close();
    console.log("✅ MCP client connection closed");
  }
}

async function runAllTests() {
  console.log("🧪 Running all tests...\n");
  
  await testValidation();
  await testUtilityFunctions();
  await testHeaders();
  await testMCPClient();
  
  console.log("\n✅ All tests completed!");
}

// Run the tests
runAllTests().catch(console.error); 