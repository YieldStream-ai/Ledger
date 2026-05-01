"""Response models — namespaced around what underwriters evaluate.

The top-level shape (document, identity, period, cash_flow, revenue, debt,
expenses, validation, confidence) is organized by underwriting concern, not
by extraction pipeline. A buyer who only cares about debt stacking can ignore
the rest of the response without parsing it.

Phase 0: bank statements populate the namespaces. Tax returns and MCA
applications still emit their data via the legacy `parsed_data` dict — they
get their own namespaced shapes in later phases.
"""

from __future__ import annotations

from pydantic import BaseModel


# ─── Operational / observability primitives (unchanged from prior shape) ────


class ExtractedTable(BaseModel):
    page: int
    headers: list[str]
    rows: list[list[str]]


class ClassificationResult(BaseModel):
    document_type: str
    subtype: str | None = None
    confidence: float
    method: str  # "keyword", "structural", "gemini", "hint"


class TierLog(BaseModel):
    """Log entry for a single extraction tier attempt."""
    tier: str           # "pdfplumber", "pymupdf", "ocr", "llamaparse_free", "gemini"
    tier_order: int
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


class QualityResult(BaseModel):
    """Pre-flight document quality assessment."""
    passed: bool
    overall_score: float
    processing_allowed: bool
    issues: list[str] = []
    rejection_reason: str | None = None
    recommendation: str | None = None


# ─── Underwriter-focused namespaces ─────────────────────────────────────────


class Document(BaseModel):
    type: str | None = None
    subtype: str | None = None
    page_count: int = 0
    extraction_method: str | None = None
    template_used: str | None = None


class Identity(BaseModel):
    account_holder_name: str | None = None
    account_number_last4: str | None = None
    business_name: str | None = None
    address: str | None = None
    ein: str | None = None
    consistency_check: str | None = None  # "passed" | "failed" | None when not yet implemented


class Period(BaseModel):
    start: str | None = None
    end: str | None = None


class OverdraftEvent(BaseModel):
    date: str
    amount: float


class CashFlow(BaseModel):
    starting_balance: float | None = None
    ending_balance: float | None = None
    total_inflows: float | None = None
    total_outflows: float | None = None
    net_change: float | None = None
    daily_balances: dict[str, float] = {}
    min_balance: float | None = None
    min_balance_date: str | None = None
    average_daily_balance: float | None = None
    negative_balance_days: int | None = None
    nsf_count: int | None = None
    overdraft_events: list[OverdraftEvent] = []


class ProcessorDeposit(BaseModel):
    processor: str
    total: float
    transaction_count: int


class Chargebacks(BaseModel):
    count: int | None = None
    total: float | None = None
    percent_of_revenue: float | None = None


class Concentration(BaseModel):
    top_counterparty_percent: float | None = None
    top_5_percent: float | None = None


class Revenue(BaseModel):
    gross_deposits: float | None = None
    deposit_count: int | None = None
    processor_deposits: list[ProcessorDeposit] = []
    non_processor_inflows: float | None = None
    recurring_revenue_estimate: float | None = None
    chargebacks: Chargebacks = Chargebacks()
    concentration: Concentration = Concentration()
    seasonality_signal: str | None = None  # "stable" | "seasonal" | "volatile" | None


class ActivePosition(BaseModel):
    type: str | None = None  # "mca" | "term_loan" | "line_of_credit" | None
    lender_name: str | None = None
    daily_debit: float | None = None
    monthly_payment: float | None = None
    estimated_balance: float | None = None
    first_seen: str | None = None


class Debt(BaseModel):
    active_positions: list[ActivePosition] = []
    total_daily_debt_service: float | None = None
    total_monthly_debt_service: float | None = None
    stacking_burden_pct: float | None = None
    dscr: float | None = None
    lien_flags: list[str] = []


class ExpenseLine(BaseModel):
    monthly_total: float | None = None
    counterparty: str | None = None
    provider: str | None = None
    frequency: str | None = None


class TaxPayments(BaseModel):
    federal: float | None = None
    state: float | None = None
    last_seen: str | None = None


class Expenses(BaseModel):
    payroll: ExpenseLine = ExpenseLine()
    rent: ExpenseLine = ExpenseLine()
    utilities: ExpenseLine = ExpenseLine()
    insurance: ExpenseLine = ExpenseLine()
    software_subscriptions: ExpenseLine = ExpenseLine()
    tax_payments: TaxPayments = TaxPayments()


class Validation(BaseModel):
    balance_check: str | None = None  # "passed" | "failed" | "skipped"
    expected_ending: float | None = None
    actual_ending: float | None = None
    discrepancy: float | None = None


class ByCategory(BaseModel):
    cash_flow: float = 0.0
    revenue: float = 0.0
    debt: float = 0.0
    expenses: float = 0.0
    identity: float = 0.0


class ConfidenceDetail(BaseModel):
    overall: float
    text_quality: float
    table_extraction: float
    template_match: float
    by_category: ByCategory = ByCategory()
    needs_human_review: bool = False


# ─── Top-level response ─────────────────────────────────────────────────────


class ParseResponse(BaseModel):
    """Underwriter-focused parse response.

    Bank statements populate the namespaces (`document`, `identity`, `period`,
    `cash_flow`, `revenue`, `debt`, `expenses`, `validation`, `confidence`).

    Tax returns and MCA applications currently emit data via the legacy
    `parsed_data` dict; they get namespaced shapes in later phases.
    """
    status: str  # "succeeded" | "error"
    error: str | None = None

    # Underwriter-facing namespaces (bank statements)
    document: Document | None = None
    identity: Identity | None = None
    period: Period | None = None
    cash_flow: CashFlow | None = None
    revenue: Revenue | None = None
    debt: Debt | None = None
    expenses: Expenses | None = None
    validation: Validation | None = None
    confidence: ConfidenceDetail | None = None

    # Operational / observability
    extraction_method: str | None = None
    page_count: int = 0
    text_content: str = ""
    tables: list[ExtractedTable] = []
    classification: ClassificationResult | None = None
    processing_time_ms: int = 0
    tier_logs: list[TierLog] = []
    metadata: ParseMetadata | None = None
    quality: QualityResult | None = None
    template_match: dict | None = None  # TemplateMatchResult; structure unchanged

    # Legacy: tax returns / MCA applications still use this until they get
    # their own namespaced shapes. For bank statements, this is None.
    parsed_data: dict | None = None


class ClassifyResponse(BaseModel):
    document_type: str
    subtype: str | None = None
    confidence: float
    method: str
