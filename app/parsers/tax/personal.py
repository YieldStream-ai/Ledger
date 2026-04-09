"""Personal tax return parser (1040)."""

from __future__ import annotations

import re

from app.models.tax_return import PersonalTaxReturn
from app.utils.currency import find_amount


def parse_personal_tax_return(text: str) -> PersonalTaxReturn:
    """Extract key fields from a 1040 personal tax return."""
    result = PersonalTaxReturn()

    # Tax year
    year_match = re.search(r"(?:tax\s+year|for\s+(?:the\s+)?year)\s+(?:ending\s+)?(?:\d{1,2}/\d{1,2}/)?(\d{4})", text, re.IGNORECASE)
    if not year_match:
        year_match = re.search(r"20[12]\d", text)
    if year_match:
        result.tax_year = year_match.group(1) if year_match.lastindex else year_match.group(0)

    # Name
    name_match = re.search(r"(?:Your\s+first\s+name|Name)[:\s]+(.+?)(?:\n|$)", text, re.IGNORECASE)
    if name_match:
        result.name = name_match.group(1).strip()

    # SSN last 4 (never store full SSN)
    ssn_match = re.search(r"(?:Social\s+[Ss]ecurity\s+[Nn]umber|SSN)[:\s]*\d{3}-?\d{2}-?(\d{4})", text)
    if not ssn_match:
        ssn_match = re.search(r"(?:SSN|Social\s+Security\s+Number)[:\s]*[*xX\d]{3}-?[*xX\d]{2}-?(\d{4})", text, re.IGNORECASE)
    if ssn_match:
        result.ssn_last4 = ssn_match.group(1)

    # Filing status
    for status in ["Married filing jointly", "Married filing separately", "Single", "Head of household", "Qualifying widow"]:
        if status.lower() in text.lower():
            result.filing_status = status
            break

    # Adjusted gross income (Line 11 on modern 1040)
    result.adjusted_gross_income = find_amount(text, [
        r"[Aa]djusted\s+[Gg]ross\s+[Ii]ncome[:\s]*\$?(-?[\d,]+\.?\d*)",
        r"AGI[:\s]*\$?(-?[\d,]+\.?\d*)",
    ])

    # Schedule C income
    result.schedule_c_income = find_amount(text, [
        r"[Ss]chedule\s+C[:\s]+(?:net\s+)?(?:profit|income)[:\s]*\$?(-?[\d,]+\.?\d*)",
        r"[Bb]usiness\s+income\s+or\s+\(loss\)[:\s]*\$?(-?[\d,]+\.?\d*)",
    ])

    return result
