"""
AI Enrichment — Gemini-powered financial analysis of bank statements.

Takes raw OCR-extracted text and produces structured financial intelligence
fields for MCA underwriting evaluation that go beyond what the deterministic
parsers extract (revenue trends, stacking detection, DSCR, risk flags).

Uses google-generativeai SDK (same dependency as gemini_fallback.py).
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


# ─── Rate Limiter (Token Bucket — 15 RPM) ────────────────────────────────────

_RATE_LIMIT = 15
_REFILL_INTERVAL_S = 60.0
_tokens = _RATE_LIMIT
_last_refill = time.time()


def _acquire_token() -> None:
    """Block until a rate limit token is available."""
    global _tokens, _last_refill
    now = time.time()
    elapsed = now - _last_refill
    if elapsed >= _REFILL_INTERVAL_S:
        _tokens = _RATE_LIMIT
        _last_refill = now

    if _tokens > 0:
        _tokens -= 1
        return

    wait = _REFILL_INTERVAL_S - elapsed + 0.1
    time.sleep(wait)
    _tokens = _RATE_LIMIT - 1
    _last_refill = time.time()


# ─── Types ────────────────────────────────────────────────────────────────────


class McaPosition(BaseModel):
    lender_name: str
    daily_debit: float
    estimated_balance: float


class TransferFlag(BaseModel):
    description: str
    amount: float


class BankIntelligenceResult(BaseModel):
    monthly_revenue_avg: float | None = None
    monthly_revenue_trend: str = "stable"  # growing | stable | declining
    revenue_volatility: float | None = None
    best_month_revenue: float | None = None
    worst_month_revenue: float | None = None
    lowest_daily_balance: float | None = None
    ending_daily_balance: float | None = None
    edb_trend: str = "flat"  # growing | flat | depleting
    days_below_threshold: int = 0
    nsf_count_30d: int = 0
    nsf_count_60d: int = 0
    nsf_count_90d: int = 0
    avg_transaction_size: float | None = None
    active_mca_positions: list[McaPosition] = []
    total_daily_debits: float = 0
    stacking_burden_pct: float = 0
    dscr: float | None = None
    lien_flags: list[str] = []
    transfer_flags: list[TransferFlag] = []
    flagged_anomalies: list[str] = []
    human_review_required: bool = False
    ocr_confidence: float = 0
    underwriting_summary: str = ""


# ─── JSON Parser ──────────────────────────────────────────────────────────────


def _parse_json_response(text: str) -> dict:
    """Strip markdown code fences if present and parse JSON."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    return json.loads(cleaned)


# ─── Enrichment Function ─────────────────────────────────────────────────────


def enrich_bank_statement(
    text_content: str,
    business_name: str,
    industry: str | None = None,
    document_hint: str | None = None,
) -> BankIntelligenceResult:
    """Analyze bank statement text with Gemini and return structured financial intelligence.

    This is the standalone equivalent of YieldStream's analyzeBankStatement().
    """
    if not settings.google_ai_api_key:
        raise ValueError("GOOGLE_AI_API_KEY is not set.")

    import google.generativeai as genai

    genai.configure(api_key=settings.google_ai_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    _acquire_token()

    hint_line = f"\nDOCUMENT HINT: {document_hint}" if document_hint else ""

    prompt = f"""You are analyzing bank statement data for an MCA (Merchant Cash Advance) underwriting evaluation.

MERCHANT: {business_name}
INDUSTRY: {industry or "Unknown"}{hint_line}

BANK STATEMENT DATA (OCR-extracted markdown):
{text_content[:15000]}

ANALYSIS TASKS:
1. Revenue: Calculate monthly averages, trend (growing/stable/declining), volatility (0-1 scale), best/worst months
2. Cash Flow: Lowest balance, ending daily balance (last day's closing balance), EDB trend over the period (growing/flat/depleting)
3. Red Flags: Count NSF fees in 30/60/90 day windows
4. Deposit Analysis: Calculate average deposit transaction size
5. Stacking/MCA: Identify recurring daily/weekly ACH debits to funding companies, extract lender names and amounts, calculate DSCR = monthly_revenue_avg / (total_daily_debits * 30)
6. Lien Flags: Scan withdrawal descriptions for keywords: "IRS", "State Tax", "Tax Lien", "Levy", "Garnishment" — return matching descriptions as array
7. Transfer Flags: Identify large transfers (>$10K) to personal accounts or labeled "inter-company", "transfer", "owner draw" — return {{description, amount}} objects
8. Anomalies: Flag large unexplained withdrawals, revenue drops >30%, unusual patterns
9. Confidence: Assess OCR quality and data completeness (0-1 scale), flag for human review if <0.80

RESPOND ONLY WITH VALID JSON (no markdown fences, no explanation):
{{
  "monthly_revenue_avg": number | null,
  "monthly_revenue_trend": "growing" | "stable" | "declining",
  "revenue_volatility": number | null,
  "best_month_revenue": number | null,
  "worst_month_revenue": number | null,
  "lowest_daily_balance": number | null,
  "ending_daily_balance": number | null,
  "edb_trend": "growing" | "flat" | "depleting",
  "days_below_threshold": number,
  "nsf_count_30d": number,
  "nsf_count_60d": number,
  "nsf_count_90d": number,
  "avg_transaction_size": number | null,
  "active_mca_positions": [{{"lender_name": string, "daily_debit": number, "estimated_balance": number}}],
  "total_daily_debits": number,
  "stacking_burden_pct": number,
  "dscr": number | null,
  "lien_flags": string[],
  "transfer_flags": [{{"description": string, "amount": number}}],
  "flagged_anomalies": string[],
  "human_review_required": boolean,
  "ocr_confidence": number,
  "underwriting_summary": string (3-4 sentences: lead with the headline risk/strength, then key financials that support it. Follow with 1-2 sentences of actionable guidance — how to leverage strengths in the bank statements or credit profile, or what to proactively address if there are weaknesses.)
}}

IMPORTANT: Do not predict lender decisions or approval outcomes. Do not use language like "will approve", "likely to fund", "will decline", or "approval unlikely". Frame all observations as deal profile analysis against documented criteria. Use language like "aligns with", "exceeds tolerance thresholds for", "consistent with", "outside documented buy-box for"."""

    result = model.generate_content(prompt)
    text = result.text
    parsed = _parse_json_response(text)

    return BankIntelligenceResult(**parsed)
