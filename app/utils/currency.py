"""Currency string parsing utilities."""

from __future__ import annotations

import re


def parse_amount(text: str) -> float | None:
    """Parse a currency string into a float.

    Handles: $1,234.56  (1,234.56)  -$1,234.56  1234.56  $1234
    Parenthesized amounts are treated as negative.
    """
    if not text:
        return None

    text = text.strip()

    # Detect negative: leading minus or parentheses
    is_negative = False
    if text.startswith("(") and text.endswith(")"):
        is_negative = True
        text = text[1:-1]
    elif text.startswith("-"):
        is_negative = True
        text = text[1:]

    # Strip currency symbols and whitespace
    text = re.sub(r"[$ \t]", "", text)

    # Remove commas
    text = text.replace(",", "")

    # Handle trailing minus (some bank formats: "1,234.56-")
    if text.endswith("-"):
        is_negative = True
        text = text[:-1]

    if not text:
        return None

    try:
        value = float(text)
        return -value if is_negative else value
    except ValueError:
        return None


def find_amount(text: str, patterns: list[str]) -> float | None:
    """Search text for the first matching pattern and extract the amount.

    Each pattern should have one capture group for the amount string.
    """
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1)
            amount = parse_amount(raw)
            if amount is not None:
                return amount
    return None
