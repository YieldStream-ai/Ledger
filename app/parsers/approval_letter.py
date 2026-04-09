"""Regex-based parser for MCA approval / offer letters.

Extracts structured offer terms from free-text approval letters using
keyword-proximity pattern matching. Falls back to Gemini when overall
confidence is low (handled by the route, not here).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime

from app.models.approval_letter import ApprovalLetterData, FieldExtraction

logger = logging.getLogger(__name__)

# ── Currency / number helpers ────────────────────────────────────────────────

_CURRENCY_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d{1,2})?)"
)

_NUMBER_RE = re.compile(
    r"([\d,]+(?:\.\d{1,4})?)"
)

_FACTOR_RE = re.compile(
    r"(\d\.\d{1,4})"
)

_DATE_PATTERNS = [
    re.compile(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"),
    re.compile(r"(\w+ \d{1,2},?\s*\d{4})"),  # "April 15, 2026"
    re.compile(r"(\d{4}-\d{2}-\d{2})"),        # ISO
]


def _parse_currency(text: str) -> float | None:
    """Extract first dollar amount from text."""
    m = _CURRENCY_RE.search(text)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _parse_number(text: str) -> float | None:
    """Extract first bare number from text."""
    m = _NUMBER_RE.search(text)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _parse_factor(text: str) -> float | None:
    """Extract a factor rate (e.g. 1.25, 1.4) from text."""
    m = _FACTOR_RE.search(text)
    if m:
        val = float(m.group(1))
        if 1.0 <= val <= 2.0:
            return val
    return None


def _parse_date(text: str) -> str | None:
    """Extract first recognisable date string."""
    for pat in _DATE_PATTERNS:
        m = pat.search(text)
        if m:
            raw = m.group(1)
            # Try to normalise to ISO
            for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
                        "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y",
                        "%Y-%m-%d"):
                try:
                    return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return raw  # return raw if we can't normalise
    return None


# ── Keyword-proximity extraction ─────────────────────────────────────────────

def _find_context(text: str, keywords: list[str], window: int = 120) -> list[tuple[str, int]]:
    """Find all text windows around keyword occurrences.

    Returns list of (context_string, char_position) tuples.
    """
    hits: list[tuple[str, int]] = []
    lower = text.lower()
    for kw in keywords:
        start = 0
        while True:
            idx = lower.find(kw, start)
            if idx == -1:
                break
            ctx_start = max(0, idx - 20)
            ctx_end = min(len(text), idx + len(kw) + window)
            hits.append((text[ctx_start:ctx_end], idx))
            start = idx + 1
    return hits


def _extract_amount(text: str, keywords: list[str]) -> FieldExtraction | None:
    """Extract a dollar amount near the given keywords."""
    contexts = _find_context(text, keywords)
    if not contexts:
        return None
    for ctx, _ in contexts:
        val = _parse_currency(ctx)
        if val and val >= 1000:  # MCA amounts are typically $1k+
            return FieldExtraction(value=val, confidence=0.85)
    return None


def _extract_factor(text: str, keywords: list[str]) -> FieldExtraction | None:
    """Extract a factor rate near the given keywords."""
    contexts = _find_context(text, keywords)
    for ctx, _ in contexts:
        val = _parse_factor(ctx)
        if val:
            return FieldExtraction(value=val, confidence=0.85)
    return None


def _extract_term(text: str) -> FieldExtraction | None:
    """Extract term length and normalise to days."""
    contexts = _find_context(text, ["term", "repayment period", "duration", "payback period"])
    for ctx, _ in contexts:
        lower = ctx.lower()
        num = _parse_number(ctx)
        if num is None:
            continue
        num_int = int(num)
        if "month" in lower:
            return FieldExtraction(value=num_int * 30, confidence=0.80)
        if "week" in lower:
            return FieldExtraction(value=num_int * 7, confidence=0.80)
        if "day" in lower or "business day" in lower:
            return FieldExtraction(value=num_int, confidence=0.85)
        # Bare number near "term" — guess days if > 30, months if <= 24
        if num_int > 30:
            return FieldExtraction(value=num_int, confidence=0.60)
        if num_int <= 24:
            return FieldExtraction(value=num_int * 30, confidence=0.55)
    return None


def _extract_frequency(text: str) -> FieldExtraction | None:
    """Detect payment frequency keywords."""
    lower = text.lower()
    freq_map = [
        (["daily remittance", "daily payment", "daily debit", "daily ach"], "Daily"),
        (["weekly remittance", "weekly payment", "weekly debit", "weekly ach"], "Weekly"),
        (["bi-weekly", "biweekly", "bi weekly"], "Bi-Weekly"),
        (["monthly payment", "monthly remittance", "monthly debit"], "Monthly"),
    ]
    for keywords, label in freq_map:
        for kw in keywords:
            if kw in lower:
                return FieldExtraction(value=label, confidence=0.90)
    # Broader single-word fallback (lower confidence)
    broad = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]
    for kw, label in broad:
        # Match word boundary to avoid false positives
        if re.search(rf"\b{kw}\b", lower):
            return FieldExtraction(value=label, confidence=0.60)
    return None


def _extract_stipulations(text: str) -> FieldExtraction | None:
    """Extract stipulations / conditions as a list of strings."""
    contexts = _find_context(
        text,
        ["stipulation", "condition", "requirement", "contingent upon",
         "subject to", "prior to funding", "conditions to close"],
        window=500,
    )
    stips: list[str] = []
    for ctx, _ in contexts:
        # Look for bullet / numbered lists
        lines = ctx.split("\n")
        for line in lines:
            stripped = line.strip()
            # Match lines starting with bullet, dash, number, or letter prefix
            if re.match(r"^[\-\u2022\u25cf\u25cb*]\s+", stripped):
                item = re.sub(r"^[\-\u2022\u25cf\u25cb*]\s+", "", stripped).strip()
                if item and len(item) > 5:
                    stips.append(item)
            elif re.match(r"^\d+[.)]\s+", stripped):
                item = re.sub(r"^\d+[.)]\s+", "", stripped).strip()
                if item and len(item) > 5:
                    stips.append(item)
            elif re.match(r"^[a-zA-Z][.)]\s+", stripped):
                item = re.sub(r"^[a-zA-Z][.)]\s+", "", stripped).strip()
                if item and len(item) > 5:
                    stips.append(item)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for s in stips:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)

    if unique:
        return FieldExtraction(value=unique, confidence=0.70)
    return None


def _extract_expiration(text: str) -> FieldExtraction | None:
    """Extract offer expiration date."""
    contexts = _find_context(
        text,
        ["expir", "valid until", "valid through", "offer valid",
         "must be accepted by", "acceptance deadline"],
    )
    for ctx, _ in contexts:
        date_str = _parse_date(ctx)
        if date_str:
            return FieldExtraction(value=date_str, confidence=0.80)
    return None


def _extract_lender_name(text: str) -> FieldExtraction | None:
    """Attempt to extract lender name from letterhead (first few lines)."""
    lines = text[:800].split("\n")
    # Heuristic: first non-empty line that looks like a company name
    # (contains "capital", "funding", "finance", "advance", "merchant", etc.)
    name_keywords = [
        "capital", "funding", "finance", "financial", "advance",
        "merchant", "lending", "credit", "solutions", "partners",
        "group", "corp", "inc", "llc",
    ]
    for line in lines[:10]:
        stripped = line.strip()
        if not stripped or len(stripped) < 3 or len(stripped) > 80:
            continue
        lower = stripped.lower()
        if any(kw in lower for kw in name_keywords):
            # Clean up common noise
            cleaned = re.sub(r"\s+", " ", stripped).strip()
            return FieldExtraction(value=cleaned, confidence=0.65)
    return None


# ── Main parser entry point ──────────────────────────────────────────────────

def parse_approval_letter(text: str) -> ApprovalLetterData:
    """Extract structured offer terms from approval letter text.

    Returns an ApprovalLetterData with per-field confidence scores.
    """
    lender_name = _extract_lender_name(text)

    approved_amount = _extract_amount(
        text,
        ["approved amount", "funding amount", "advance amount",
         "purchase amount", "approved for", "amount approved",
         "merchant advance"],
    )

    factor_rate = _extract_factor(
        text,
        ["factor rate", "factor", "purchase price rate", "specified rate"],
    )

    buy_rate = _extract_factor(
        text,
        ["buy rate", "broker rate", "cost rate"],
    )

    term_days = _extract_term(text)

    payment_frequency = _extract_frequency(text)

    payment_amount = _extract_amount(
        text,
        ["payment amount", "remittance", "daily payment", "weekly payment",
         "daily debit", "ach amount", "debit amount"],
    )

    total_payback = _extract_amount(
        text,
        ["total payback", "total repayment", "purchase price",
         "total amount", "payback amount", "total purchased amount"],
    )

    net_funding = _extract_amount(
        text,
        ["net funding", "net proceeds", "net advance", "net amount",
         "amount to merchant", "disbursement amount"],
    )

    commission_points = None
    comm_contexts = _find_context(
        text,
        ["commission", "points", "broker fee", "origination fee", "comp"],
    )
    for ctx, _ in comm_contexts:
        # Look for percentage (e.g. "10%", "10 points")
        pct_match = re.search(r"(\d{1,2}(?:\.\d{1,2})?)\s*(?:%|percent|points|pts)", ctx.lower())
        if pct_match:
            commission_points = FieldExtraction(
                value=float(pct_match.group(1)),
                confidence=0.80,
            )
            break
        # Look for dollar amount
        val = _parse_currency(ctx)
        if val and val < 100000:  # Commission shouldn't exceed advance
            commission_points = FieldExtraction(value=val, confidence=0.65)
            break

    stipulations = _extract_stipulations(text)
    expiration_date = _extract_expiration(text)

    # Compute overall confidence — weighted average of extracted fields
    fields = [
        approved_amount, factor_rate, term_days, payment_frequency,
        payment_amount, total_payback, net_funding,
    ]
    extracted = [f for f in fields if f is not None]
    if extracted:
        overall = sum(f.confidence for f in extracted) / len(extracted)
        # Boost if we got the key fields (amount + factor + term)
        key_count = sum(1 for f in [approved_amount, factor_rate, term_days] if f is not None)
        overall = min(1.0, overall + (key_count * 0.05))
    else:
        overall = 0.0

    return ApprovalLetterData(
        lender_name=lender_name,
        approved_amount=approved_amount,
        factor_rate=factor_rate,
        buy_rate=buy_rate,
        term_days=term_days,
        payment_frequency=payment_frequency,
        payment_amount=payment_amount,
        total_payback=total_payback,
        net_funding=net_funding,
        commission_points=commission_points,
        stipulations=stipulations,
        expiration_date=expiration_date,
        overall_confidence=round(overall, 2),
    )
