export interface ExtractedTable {
  page: number;
  headers: string[];
  rows: string[][];
}

export interface ClassificationResult {
  document_type: string;
  subtype: string | null;
  confidence: number;
  method: string;
}

export interface ByCategory {
  cash_flow: number;
  revenue: number;
  debt: number;
  expenses: number;
  identity: number;
}

export interface ConfidenceDetail {
  overall: number;
  text_quality: number;
  table_extraction: number;
  template_match: number;
  by_category: ByCategory;
  needs_human_review: boolean;
}

export interface TierLog {
  tier: string;
  tier_order: number;
  status: string;
  failure_reason: string | null;
  text_char_count: number;
  table_count: number;
  confidence_score: number;
  processing_time_ms: number;
}

export interface ParseMetadata {
  winning_tier: string | null;
  tiers_attempted: number;
  total_processing_time_ms: number;
  bank_detected: string | null;
  template_used: string | null;
  template_match_confidence: number;
  document_type_classified: string | null;
  classification_confidence: number;
  classification_method: string | null;
  fields_extracted_count: number;
  fields_missing: string[];
  needs_human_review: boolean;
  gemini_tokens_used: number | null;
  gemini_cost_estimate: number | null;
}

export interface QualityResult {
  passed: boolean;
  overall_score: number;
  processing_allowed: boolean;
  issues: string[];
  rejection_reason: string | null;
  recommendation: string | null;
}

export interface ReviewItem {
  id: string;
  timestamp: string;
  file_name: string;
  bank_detected: string | null;
  discrepancy: number;
  expected_ending: number;
  actual_ending: number;
  parsed_data_snapshot: Record<string, unknown>;
}

export interface TemplateMatchSignal {
  category: string;
  description: string;
}

export interface TemplateMatchAlternative {
  id: string;
  bank_name: string;
  confidence: number;
}

export interface TemplateMatchResult {
  id: string;
  bank_name: string;
  confidence: number;
  fallback_used: boolean;
  signals: TemplateMatchSignal[];
  alternatives: TemplateMatchAlternative[];
}

export interface TemplateDetail {
  id: string;
  bank_name: string;
  signal_count: number;
  signals: TemplateMatchSignal[];
  match_count_30d: number;
}

// ─── Underwriter-focused namespaces ──────────────────────────────────────────

export interface Document {
  type: string | null;
  subtype: string | null;
  page_count: number;
  extraction_method: string | null;
  template_used: string | null;
}

export interface Identity {
  account_holder_name: string | null;
  account_number_last4: string | null;
  business_name: string | null;
  address: string | null;
  ein: string | null;
  consistency_check: string | null;
}

export interface Period {
  start: string | null;
  end: string | null;
}

export interface OverdraftEvent {
  date: string;
  amount: number;
}

export interface SuspiciousTransfer {
  description: string;
  amount: number;
}

export interface CashFlow {
  starting_balance: number | null;
  ending_balance: number | null;
  total_inflows: number | null;
  total_outflows: number | null;
  net_change: number | null;
  daily_balances: Record<string, number>;
  min_balance: number | null;
  min_balance_date: string | null;
  average_daily_balance: number | null;
  ending_balance_trend: "growing" | "flat" | "depleting" | null;
  days_below_threshold: number | null;
  negative_balance_days: number | null;
  nsf_count: number | null;
  nsf_count_30d: number | null;
  nsf_count_60d: number | null;
  nsf_count_90d: number | null;
  overdraft_events: OverdraftEvent[];
  suspicious_transfers: SuspiciousTransfer[];
  anomalies: string[];
}

export interface ProcessorDeposit {
  processor: string;
  total: number;
  transaction_count: number;
}

export interface Chargebacks {
  count: number | null;
  total: number | null;
  percent_of_revenue: number | null;
}

export interface Concentration {
  top_counterparty_percent: number | null;
  top_5_percent: number | null;
}

export interface Revenue {
  gross_deposits: number | null;
  deposit_count: number | null;
  monthly_average: number | null;
  trend: "growing" | "stable" | "declining" | null;
  volatility: number | null;
  best_month: number | null;
  worst_month: number | null;
  avg_transaction_size: number | null;
  processor_deposits: ProcessorDeposit[];
  non_processor_inflows: number | null;
  recurring_revenue_estimate: number | null;
  chargebacks: Chargebacks;
  concentration: Concentration;
  seasonality_signal: string | null;
  anomalies: string[];
}

export interface ActivePosition {
  type: string | null;
  lender_name: string | null;
  daily_debit: number | null;
  monthly_payment: number | null;
  estimated_balance: number | null;
  first_seen: string | null;
}

export interface Debt {
  active_positions: ActivePosition[];
  total_daily_debt_service: number | null;
  total_monthly_debt_service: number | null;
  stacking_burden_pct: number | null;
  dscr: number | null;
  lien_flags: string[];
  anomalies: string[];
}

export interface Summary {
  narrative: string | null;
  key_concerns: string[];
  strengths: string[];
}

export interface ExpenseLine {
  monthly_total: number | null;
  counterparty: string | null;
  provider: string | null;
  frequency: string | null;
}

export interface TaxPayments {
  federal: number | null;
  state: number | null;
  last_seen: string | null;
}

export interface Expenses {
  payroll: ExpenseLine;
  rent: ExpenseLine;
  utilities: ExpenseLine;
  insurance: ExpenseLine;
  software_subscriptions: ExpenseLine;
  tax_payments: TaxPayments;
}

export interface Validation {
  balance_check: "passed" | "failed" | "skipped" | null;
  expected_ending: number | null;
  actual_ending: number | null;
  discrepancy: number | null;
}

export interface ParseResponse {
  status: "succeeded" | "error";
  error: string | null;

  // Underwriter-facing namespaces (bank statements)
  document: Document | null;
  identity: Identity | null;
  period: Period | null;
  cash_flow: CashFlow | null;
  revenue: Revenue | null;
  debt: Debt | null;
  expenses: Expenses | null;
  validation: Validation | null;
  summary: Summary | null;
  confidence: ConfidenceDetail | null;

  // Operational / observability
  extraction_method: string | null;
  page_count: number;
  text_content: string;
  tables: ExtractedTable[];
  classification: ClassificationResult | null;
  processing_time_ms: number;
  tier_logs: TierLog[];
  metadata: ParseMetadata | null;
  quality: QualityResult | null;
  template_match: TemplateMatchResult | null;

  // Legacy: tax returns / MCA applications until they get namespaced shapes
  parsed_data: Record<string, unknown> | null;
}

export interface ParseConfig {
  documentTypeHint: string;
  pageRange: string;
  crossCheckBalances: boolean;
  confidenceThreshold: number;
  flagDuplicates: boolean;
  includeEnrichment: boolean;
  anonymizationMode: string;
  currencyNormalization: boolean;
  businessName: string;
  industry: string;
}

export type FileStatus = "queued" | "uploading" | "success" | "error";

export interface FileEntry {
  id: string;
  file: File;
  status: FileStatus;
  progress: number;
  result: ParseResponse | null;
  error: string | null;
}
