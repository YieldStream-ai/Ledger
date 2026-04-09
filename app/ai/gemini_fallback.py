"""Gemini API fallback for low-confidence classification and unrecognized bank formats.

When a bank has no dedicated template, Gemini extracts both summary fields AND
transactions. The full extraction (with raw text sample) is stored as a bank
profile sample for future template generation.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from app.config import settings
from app.models.responses import ClassificationResult

logger = logging.getLogger(__name__)

# Approximate cost per token for gemini-2.0-flash-lite (free tier has limits)
_COST_PER_INPUT_TOKEN = 0.0  # Free tier — update when on paid plan
_COST_PER_OUTPUT_TOKEN = 0.0


@dataclass
class GeminiUsage:
    """Token usage from a Gemini API call."""
    tokens_used: int = 0
    cost_estimate: float = 0.0


# Module-level accumulator for per-request Gemini usage
_request_usage = GeminiUsage()


def reset_usage() -> None:
    """Reset per-request usage counters. Call at start of each /parse request."""
    global _request_usage
    _request_usage = GeminiUsage()


def get_usage() -> GeminiUsage:
    """Get accumulated Gemini usage for the current request."""
    return _request_usage


def _track_usage(response) -> None:
    """Extract and accumulate token usage from a Gemini response."""
    global _request_usage
    try:
        usage = response.usage_metadata
        if usage:
            tokens = (usage.prompt_token_count or 0) + (usage.candidates_token_count or 0)
            _request_usage.tokens_used += tokens
            _request_usage.cost_estimate += (
                (usage.prompt_token_count or 0) * _COST_PER_INPUT_TOKEN
                + (usage.candidates_token_count or 0) * _COST_PER_OUTPUT_TOKEN
            )
    except Exception:
        pass  # usage_metadata may not be available


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from Gemini response."""
    text = text.strip()
    if text.startswith("```"):
        # Remove first line (```json or ```)
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def classify_document(text: str) -> ClassificationResult | None:
    """Use Gemini to classify a document when keyword matching fails.

    Returns None if Gemini is unavailable or fails.
    """
    if not settings.google_ai_api_key:
        logger.debug("Gemini API key not configured — skipping fallback classification")
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.google_ai_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")

        prompt = f"""Classify this document into exactly one of these types:
- bank_statement
- business_tax_return (subtypes: 1120, 1120S, 1065, schedule_c)
- personal_tax_return (subtype: 1040)
- drivers_license
- voided_check
- mca_application
- cc_processing_statement
- lease_agreement
- articles_of_incorporation
- ucc_filing
- unknown

Respond with JSON only, no markdown fences:
{{"document_type": "...", "subtype": "..." or null, "confidence": 0.0-1.0}}

Document text (first 3000 chars):
{text[:3000]}"""

        response = model.generate_content(prompt)
        _track_usage(response)
        raw = _strip_markdown_fences(response.text)
        data = json.loads(raw)

        return ClassificationResult(
            document_type=data.get("document_type", "unknown"),
            subtype=data.get("subtype"),
            confidence=float(data.get("confidence", 0.5)),
            method="gemini",
        )

    except Exception as e:
        logger.warning("Gemini classification failed: %s", e)
        return None


def extract_approval_letter_gemini(text: str) -> dict | None:
    """Use Gemini to extract offer terms from an MCA approval letter.

    Returns a dict matching ApprovalLetterData field names, or None on failure.
    """
    if not settings.google_ai_api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.google_ai_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")

        prompt = f"""Extract structured offer terms from this MCA (Merchant Cash Advance) approval letter. Return JSON only, no markdown fences.

Required JSON structure:
{{
  "lender_name": "string — the funding company name from the letterhead",
  "approved_amount": number or null — the approved advance/funding amount in dollars,
  "factor_rate": number or null — the factor rate (e.g. 1.25, 1.35),
  "buy_rate": number or null — the buy/broker rate if different from factor rate,
  "term_days": number or null — repayment term in DAYS (convert months to days by multiplying by 30, weeks by 7),
  "payment_frequency": "Daily" or "Weekly" or "Bi-Weekly" or "Monthly" or null,
  "payment_amount": number or null — the periodic payment/remittance amount in dollars,
  "total_payback": number or null — total repayment/purchase price in dollars,
  "net_funding": number or null — net proceeds to the merchant after fees,
  "commission_points": number or null — broker commission as percentage points (e.g. 10 for 10%),
  "stipulations": ["list of conditions/stipulations as strings"] or [],
  "expiration_date": "YYYY-MM-DD" or null — when the offer expires
}}

Important:
- All dollar amounts should be plain numbers (no $ sign, no commas)
- Factor rates are typically between 1.10 and 1.99
- If a field is not mentioned in the document, use null
- For stipulations, extract each condition as a separate string in the array

Document text (first 8000 chars):
{text[:8000]}"""

        response = model.generate_content(prompt)
        _track_usage(response)
        raw = _strip_markdown_fences(response.text)
        return json.loads(raw)

    except Exception as e:
        logger.warning("Gemini approval letter extraction failed: %s", e)
        return None


def extract_bank_statement_gemini(text: str) -> dict | None:
    """Use Gemini to extract FULL bank statement data including transactions.

    Returns a dict with summary fields + transactions array, or None on failure.
    This is the enhanced version that extracts everything needed to build
    bank profiles for future template generation.
    """
    if not settings.google_ai_api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.google_ai_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")

        prompt = f"""Extract ALL structured data from this bank statement. Return JSON only, no markdown fences.

You must extract both summary fields AND every transaction. Be thorough.

Required JSON structure:
{{
  "bank_name": "string — the bank or credit union name",
  "account_holder": "string or null — the account owner name",
  "account_number_last4": "string or null — last 4 digits only",
  "period_start": "YYYY-MM-DD or null",
  "period_end": "YYYY-MM-DD or null",
  "beginning_balance": number or null,
  "ending_balance": number or null,
  "total_deposits": number or null,
  "total_withdrawals": number or null,
  "nsf_count": number (0 if none found),
  "average_daily_balance": number or null,
  "deposit_count": number or null,
  "transactions": [
    {{
      "date": "YYYY-MM-DD",
      "description": "transaction description",
      "amount": number (positive),
      "type": "credit" or "debit",
      "running_balance": number or null
    }}
  ],
  "observed_patterns": {{
    "date_format": "describe the date format used, e.g. MM-DD, MM/DD/YYYY",
    "amount_format": "describe how amounts are formatted, e.g. trailing_minus, parentheses, signed",
    "summary_location": "where is the account summary, e.g. top_table, header_section",
    "transaction_section_header": "the text that starts the transaction list",
    "has_running_balance": true or false
  }}
}}

Extract up to 100 transactions. If there are more, extract the first 50 and last 50.

Bank statement text (first 15000 chars):
{text[:15000]}"""

        response = model.generate_content(prompt)
        _track_usage(response)
        raw = _strip_markdown_fences(response.text)
        return json.loads(raw)

    except Exception as e:
        logger.warning("Gemini bank statement extraction failed: %s", e)
        return None
