import { z } from 'zod';

// Base types
export const WeightSchema = z.object({
  num: z.string(),
  den: z.number()
});

export const AssetSchema = z.object({
  ticker: z.string(),
  exchange: z.string().optional(),
  name: z.string(),
  step: z.literal('asset'),
  weight: WeightSchema.optional()
});

export const FilterSchema: z.ZodType<any> = z.object({
  step: z.literal('filter'),
  'sort-by-fn': z.string().optional(),
  'sort-by-fn-params': z.record(z.any()).optional(),
  'select-fn': z.string().optional(),
  'select-n': z.string().optional(),
  children: z.array(z.union([AssetSchema, z.lazy(() => FilterSchema)]))
});

export const WeightCashEqualSchema: z.ZodType<any> = z.object({
  step: z.literal('wt-cash-equal'),
  children: z.array(z.union([
    AssetSchema,
    FilterSchema,
    z.lazy(() => WeightCashEqualSchema),
    z.lazy(() => WeightCashSpecifiedSchema),
    z.lazy(() => IfSchema)
  ]))
});

export const WeightCashSpecifiedSchema: z.ZodType<any> = z.object({
  step: z.literal('wt-cash-specified'),
  children: z.array(z.union([
    AssetSchema,
    FilterSchema,
    z.lazy(() => WeightCashEqualSchema),
    z.lazy(() => WeightCashSpecifiedSchema),
    z.lazy(() => IfSchema)
  ]))
});

export const GroupSchema: z.ZodType<any> = z.object({
  step: z.literal('group'),
  name: z.string(),
  children: z.array(z.union([
    AssetSchema,
    FilterSchema,
    WeightCashEqualSchema,
    WeightCashSpecifiedSchema,
    z.lazy(() => GroupSchema),
    z.lazy(() => IfSchema)
  ]))
});

export const IfChildSchema: z.ZodType<any> = z.object({
  step: z.literal('if-child'),
  'is-else-condition?': z.boolean(),
  'lhs-fn': z.string().optional(),
  'lhs-fn-params': z.record(z.any()).optional(),
  'lhs-val': z.string().optional(),
  'rhs-fn': z.string().optional(),
  'rhs-fn-params': z.record(z.any()).optional(),
  'rhs-val': z.string().optional(),
  comparator: z.string().optional(),
  children: z.array(z.union([
    AssetSchema,
    FilterSchema,
    WeightCashEqualSchema,
    WeightCashSpecifiedSchema,
    GroupSchema,
    z.lazy(() => IfChildSchema)
  ]))
});

export const IfSchema = z.object({
  step: z.literal('if'),
  children: z.array(IfChildSchema)
});

export const RootSchema = z.object({
  step: z.literal('root'),
  name: z.string(),
  description: z.string(),
  rebalance: z.string().optional(),
  children: z.array(z.union([
    WeightCashEqualSchema,
    WeightCashSpecifiedSchema,
    GroupSchema,
    IfSchema
  ]))
});

export const SymphonyScoreSchema = RootSchema;

// API Response types
export const AccountHoldingResponseSchema = z.object({
  ticker: z.string(),
  quantity: z.number()
});

export const AccountResponseSchema = z.object({
  account_uuid: z.string(),
  account_foreign_id: z.string(),
  account_type: z.string(),
  asset_classes: z.array(z.string()),
  account_number: z.string(),
  status: z.string(),
  broker: z.string(),
  created_at: z.string(),
  first_deposit_at: z.string().nullable(),
  first_incoming_acats_transfer_at: z.string().nullable(),
  first_deploy_at: z.string().nullable(),
  first_position_created_at: z.string().nullable(),
  has_queued_deploy: z.boolean(),
  has_active_position: z.boolean()
});

export const PortfolioStatsResponseSchema = z.object({
  portfolio_value: z.number(),
  total_cash: z.number(),
  pending_deploys_cash: z.number(),
  total_unallocated_cash: z.number(),
  net_deposits: z.number(),
  simple_return: z.number(),
  todays_percent_change: z.number(),
  todays_dollar_change: z.number()
});

export const DvmCapitalSchema = z.record(z.record(z.number()));
export const LegendSchema = z.record(z.object({
  name: z.string()
}));

export const BacktestResponseSchema = z.object({
  data_warnings: z.array(z.string()).optional(),
  first_day: z.number().optional(),
  last_market_day: z.number().optional(),
  last_market_days_value: z.number().optional(),
  last_market_days_holdings: z.record(z.number()).optional(),
  stats: z.record(z.any()).optional(),
  dvm_capital: DvmCapitalSchema.optional(),
  legend: LegendSchema.optional()
});

// Export types
export type Weight = z.infer<typeof WeightSchema>;
export type Asset = z.infer<typeof AssetSchema>;
export type Filter = z.infer<typeof FilterSchema>;
export type WeightCashEqual = z.infer<typeof WeightCashEqualSchema>;
export type WeightCashSpecified = z.infer<typeof WeightCashSpecifiedSchema>;
export type Group = z.infer<typeof GroupSchema>;
export type IfChild = z.infer<typeof IfChildSchema>;
export type If = z.infer<typeof IfSchema>;
export type Root = z.infer<typeof RootSchema>;
export type SymphonyScore = z.infer<typeof SymphonyScoreSchema>;

export type AccountHoldingResponse = z.infer<typeof AccountHoldingResponseSchema>;
export type AccountResponse = z.infer<typeof AccountResponseSchema>;
export type PortfolioStatsResponse = z.infer<typeof PortfolioStatsResponseSchema>;
export type DvmCapital = z.infer<typeof DvmCapitalSchema>;
export type Legend = z.infer<typeof LegendSchema>;
export type BacktestResponse = z.infer<typeof BacktestResponseSchema>;

// Validation function
export function validateSymphonyScore(score: any): SymphonyScore {
  return SymphonyScoreSchema.parse(score);
} 