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

export interface ConfidenceDetail {
  overall: number;
  text_quality: number;
  table_extraction: number;
  template_match: number;
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

export interface ArithmeticValidation {
  balance_check: "passed" | "failed" | "skipped";
  expected_ending: number;
  actual_ending: number;
  discrepancy: number;
  confidence: number;
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

export interface ParseResponse {
  status: "success" | "error";
  extraction_method: string | null;
  page_count: number;
  text_content: string;
  tables: ExtractedTable[];
  classification: ClassificationResult | null;
  parsed_data: Record<string, unknown> | null;
  confidence: ConfidenceDetail | null;
  processing_time_ms: number;
  error: string | null;
  tier_logs: TierLog[];
  metadata: ParseMetadata | null;
  quality: QualityResult | null;
  enrichment: Record<string, unknown> | null;
  validation: ArithmeticValidation | null;
  template_match: TemplateMatchResult | null;
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
