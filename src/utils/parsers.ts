import { BacktestResponse, DvmCapital, Legend } from '../types/index.js';

export function truncateText(text: string, maxLength: number): string {
  return text.length > maxLength ? text.substring(0, maxLength) : text;
}

export function epochToDate(epoch: number): string {
  const date = new Date(epoch * 86400 * 1000);
  return date.toISOString().split('T')[0];
}

export function epochMsToDate(epochMs: number): string {
  const date = new Date(epochMs);
  return date.toISOString().split('T')[0];
}

export function parseStats(stats: Record<string, any>): Record<string, any> {
  const parsedStats: Record<string, any> = {
    annualized_rate_of_return: `${(stats.annualized_rate_of_return || 0) * 100}%`,
    benchmarks: Object.fromEntries(
      Object.entries((stats.benchmarks as Record<string, any>) || {}).map(([benchmark, benchmarkStats]) => [
        benchmark,
        parseStats(benchmarkStats as Record<string, any>)
      ])
    ),
    calmar_ratio: Math.round((stats.calmar_ratio || 0) * 10000) / 10000,
    sharpe_ratio: Math.round((stats.sharpe_ratio || 0) * 10000) / 10000,
    cumulative_return: `${(stats.cumulative_return || 0) * 100}%`,
    trailing_one_year_return: `${(stats.trailing_one_year_return || 0) * 100}%`,
    trailing_one_month_return: `${(stats.trailing_one_month_return || 0) * 100}%`,
    trailing_three_month_return: `${(stats.trailing_three_month_return || 0) * 100}%`,
    max_drawdown: `${(stats.max_drawdown || 0) * 100}%`,
    standard_deviation: `${(stats.standard_deviation || 0) * 100}%`,
  };

  // Process alpha and beta from percent section
  const percentStats = stats.percent as Record<string, any> || {};
  if (Object.keys(percentStats).length > 0) {
    parsedStats.alpha = Math.round((percentStats.alpha || 0) * 10000) / 10000;
    parsedStats.beta = Math.round((percentStats.beta || 0) * 10000) / 10000;
    parsedStats.r_square = Math.round((percentStats.r_square || 0) * 10000) / 10000;
    parsedStats.pearson_r = Math.round((percentStats.pearson_r || 0) * 10000) / 10000;
  }

  return parsedStats;
}

export function parseDvmCapital(dvmCapital: DvmCapital, legend: Legend): Record<string, any[]> {
  const parsedDailyValues: Record<string, any[]> = {};

  // Collect all unique dates first
  const allDates = new Set<string>();
  for (const values of Object.values(dvmCapital as Record<string, Record<string, number>>)) {
    for (const dayNum of Object.keys(values as Record<string, number>)) {
      const dateStr = epochToDate(parseInt(dayNum));
      allDates.add(dateStr);
    }
  }

  // Sort dates
  const sortedDates = Array.from(allDates).sort();

  // Create list of dictionaries for dataframe-friendly structure
  parsedDailyValues.cumulative_return_date = sortedDates;
  const firstDayValues: Record<string, number> = {};

  for (const date of sortedDates) {
    for (const [key, values] of Object.entries(dvmCapital as Record<string, Record<string, number>>)) {
      // Replace key with legend name if it exists
      const legendEntry = legend[key];
      const displayKey = legendEntry?.name || key;
      
      if (!parsedDailyValues[displayKey]) {
        parsedDailyValues[displayKey] = [];
      }

      // Find the corresponding value for this date
      let value: number | undefined;
      for (const [dayNum, val] of Object.entries(values as Record<string, number>)) {
        const dateStr = epochToDate(parseInt(dayNum));
        if (dateStr === date) {
          value = val as number;
          break;
        }
      }

      // Calculate cumulative return since first day
      if (value !== undefined && !(displayKey in firstDayValues)) {
        // Set the first value as the base for cumulative returns
        firstDayValues[displayKey] = value;
      }
      
      if (value !== undefined && displayKey in firstDayValues) {
        // Calculate cumulative return since first day
        const firstDayValue = firstDayValues[displayKey];
        const cumulativeReturn = ((value - firstDayValue) / firstDayValue) * 100;
        parsedDailyValues[displayKey].push(Math.round(cumulativeReturn * 100) / 100);
      } else {
        parsedDailyValues[displayKey].push(null);
      }
    }
  }

  return parsedDailyValues;
}

export function parseBacktestOutput(backtest: BacktestResponse, includeDailyValues = false, capital?: number): Record<string, any> {
  const output: Record<string, any> = {
    data_warnings: backtest.data_warnings,
    first_day: backtest.first_day ? epochToDate(backtest.first_day) : null,
    first_day_value: capital ? `$${capital.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : null,
    last_market_day: backtest.last_market_day ? epochToDate(backtest.last_market_day) : null,
    last_market_days_shares: Object.fromEntries(
      Object.entries(backtest.last_market_days_holdings || {})
        .filter(([k, v]) => k !== '$USD' && v !== 0.0)
    ),
    last_market_days_value: backtest.last_market_days_value 
      ? `$${backtest.last_market_days_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` 
      : null,
    stats: parseStats(backtest.stats || {}),
  };

  if (includeDailyValues && backtest.dvm_capital && backtest.legend) {
    output.daily_values = parseDvmCapital(backtest.dvm_capital, backtest.legend);
  }

  return output;
} 