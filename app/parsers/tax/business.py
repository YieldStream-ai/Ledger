"""Business tax return parser (1120, 1120S, 1065, Schedule C)."""

from __future__ import annotations

import re

from app.models.tax_return import BusinessTaxReturn
from app.utils.currency import find_amount


def parse_business_tax_return(text: str) -> BusinessTaxReturn:
    """Extract key fields from a business tax return."""
    result = BusinessTaxReturn()

    text_upper = text.upper()

    # Determine filing type
    if "FORM 1120-S" in text_upper or "FORM 1120S" in text_upper:
        result.filing_type = "1120S"
    elif "FORM 1120" in text_upper:
        result.filing_type = "1120"
    elif "FORM 1065" in text_upper:
        result.filing_type = "1065"
    elif "SCHEDULE C" in text_upper:
        result.filing_type = "schedule_c"

    # Tax year
    year_match = re.search(r"(?:tax\s+year|for\s+(?:the\s+)?year)\s+(?:ending\s+)?(?:\d{1,2}/\d{1,2}/)?(\d{4})", text, re.IGNORECASE)
    if not year_match:
        year_match = re.search(r"20[12]\d", text)
    if year_match:
        result.tax_year = year_match.group(1) if year_match.lastindex else year_match.group(0)

    # Business name
    name_match = re.search(r"(?:Name\s+of\s+(?:corporation|partnership|business))[:\s]+(.+?)(?:\n|$)", text, re.IGNORECASE)
    if name_match:
        result.business_name = name_match.group(1).strip()

    # EIN
    ein_match = re.search(r"(?:Employer\s+[Ii]dentification\s+[Nn]umber|EIN)[:\s]*(\d{2}-?\d{7})", text)
    if ein_match:
        result.ein = ein_match.group(1)

    # Gross receipts — line numbers vary by form type
    result.gross_receipts = find_amount(text, [
        r"[Gg]ross\s+receipts\s+or\s+sales[:\s]*\$?([\d,]+\.?\d*)",
        r"[Gg]ross\s+receipts[:\s]*\$?([\d,]+\.?\d*)",
        r"[Ll]ine\s+1[ac]?[:\s]*\$?([\d,]+\.?\d*)",
    ])

    # Net income
    result.net_income = find_amount(text, [
        r"[Nn]et\s+(?:income|profit)\s*(?:\(loss\))?[:\s]*\$?(-?[\d,]+\.?\d*)",
        r"[Tt]axable\s+income[:\s]*\$?(-?[\d,]+\.?\d*)",
        r"[Oo]rdinary\s+business\s+income[:\s]*\$?(-?[\d,]+\.?\d*)",
    ])

    # Total assets
    result.total_assets = find_amount(text, [
        r"[Tt]otal\s+assets[:\s]*\$?([\d,]+\.?\d*)",
    ])

    return result
