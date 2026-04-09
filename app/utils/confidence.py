"""Confidence scoring helpers."""

from __future__ import annotations


def compute_field_confidence(fields: dict, required_keys: list[str]) -> float:
    """Compute confidence based on how many required fields were successfully extracted.

    Returns 0-1 score.
    """
    if not required_keys:
        return 1.0

    found = sum(1 for k in required_keys if fields.get(k) is not None)
    return found / len(required_keys)
