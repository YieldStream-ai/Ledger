"""Date parsing utilities for bank statements and financial documents."""

from __future__ import annotations

import re
from datetime import datetime


# Common date formats found in bank statements
_DATE_FORMATS = [
    "%m/%d/%Y",      # 03/15/2026
    "%m/%d/%y",      # 03/15/26
    "%m-%d-%Y",      # 03-15-2026
    "%m-%d-%y",      # 03-15-26
    "%B %d, %Y",     # March 15, 2026
    "%b %d, %Y",     # Mar 15, 2026
    "%B %d %Y",      # March 15 2026
    "%b %d %Y",      # Mar 15 2026
    "%Y-%m-%d",      # 2026-03-15
    "%d %B %Y",      # 15 March 2026
    "%d %b %Y",      # 15 Mar 2026
]


def parse_date(text: str) -> str | None:
    """Parse a date string into ISO format (YYYY-MM-DD). Returns None if unparsable."""
    if not text:
        return None

    text = text.strip()

    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def find_date_range(text: str) -> tuple[str | None, str | None]:
    """Find a statement period date range in text.

    Looks for patterns like:
    - "Statement Period: March 1, 2026 - March 31, 2026"
    - "03/01/2026 through 03/31/2026"
    - "Period: 03/01/26 to 03/31/26"
    """
    # Pattern: two dates separated by a connector
    connectors = r"(?:\s*[-–—]\s*|\s+(?:to|through|thru)\s+)"
    date_pat = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    month_date_pat = r"([A-Z][a-z]+ \d{1,2},?\s*\d{4})"

    # Try numeric date range
    match = re.search(
        rf"(?:statement\s+period|period|date)[:\s]*{date_pat}{connectors}{date_pat}",
        text,
        re.IGNORECASE,
    )
    if match:
        return parse_date(match.group(1)), parse_date(match.group(2))

    # Try month name date range
    match = re.search(
        rf"(?:statement\s+period|period|date)[:\s]*{month_date_pat}{connectors}{month_date_pat}",
        text,
        re.IGNORECASE,
    )
    if match:
        return parse_date(match.group(1)), parse_date(match.group(2))

    # Try standalone numeric date range (no label)
    match = re.search(rf"{date_pat}{connectors}{date_pat}", text)
    if match:
        start = parse_date(match.group(1))
        end = parse_date(match.group(2))
        if start and end:
            return start, end

    return None, None
