from __future__ import annotations

from pydantic import BaseModel


class ExtractedTable(BaseModel):
    page: int
    headers: list[str]
    rows: list[list[str]]


class ClassificationResult(BaseModel):
    document_type: str
    subtype: str | None = None
    confidence: float
    method: str  # "keyword", "structural", "gemini"


class ConfidenceDetail(BaseModel):
    overall: float
    text_quality: float
    table_extraction: float
    template_match: float
    needs_human_review: bool


class TierLog(BaseModel):
    """Log entry for a single extraction tier attempt."""
    tier: str           # "pdfplumber", "pymupdf", "ocr", "llamaparse_free", "gemini"
    tier_order: int     # 1-5, which attempt number
    status: str         # "success", "failed", "skipped"
    failure_reason: str | None = None
    text_char_count: int = 0
    table_count: int = 0
    confidence_score: float = 0.0
    processing_time_ms: int = 0


class ParseMetadata(BaseModel):
    """Aggregate metadata about the full parse pipeline run."""
    winning_tier: str | None = None
    tiers_attempted: int = 0
    total_processing_time_ms: int = 0
    bank_detected: str | None = None
    template_used: str | None = None
    template_match_confidence: float = 0.0
    document_type_classified: str | None = None
    classification_confidence: float = 0.0
    classification_method: str | None = None
    fields_extracted_count: int = 0
    fields_missing: list[str] = []
    needs_human_review: bool = False
    gemini_tokens_used: int | None = None
    gemini_cost_estimate: float | None = None


class BankProfileSample(BaseModel):
    """A sample extraction to store in bank_profiles for future template building."""
    bank_name: str
    bank_slug: str
    period: str | None = None              # "2026-01 to 2026-02"
    raw_text_sample: str = ""              # First 3000 chars of extracted text
    gemini_extraction: dict | None = None  # Full Gemini response
    fields_missing: list[str] = []
    observed_patterns: dict = {}           # Date format, amount format, etc.
    has_template: bool = False             # Whether a dedicated template handled this


class QualityResult(BaseModel):
    """Pre-flight document quality assessment."""
    passed: bool
    overall_score: float  # 0-100
    processing_allowed: bool
    issues: list[str] = []
    rejection_reason: str | None = None
    recommendation: str | None = None


class ParseResponse(BaseModel):
    status: str  # "success" | "error"
    extraction_method: str | None = None
    page_count: int = 0
    text_content: str = ""
    tables: list[ExtractedTable] = []
    classification: ClassificationResult | None = None
    parsed_data: dict | None = None
    confidence: ConfidenceDetail | None = None
    processing_time_ms: int = 0
    error: str | None = None
    tier_logs: list[TierLog] = []
    metadata: ParseMetadata | None = None
    bank_profile_sample: BankProfileSample | None = None
    quality: QualityResult | None = None
    enrichment: dict | None = None  # BankIntelligenceResult when include_enrichment=True


class ClassifyResponse(BaseModel):
    document_type: str
    subtype: str | None = None
    confidence: float
    method: str
