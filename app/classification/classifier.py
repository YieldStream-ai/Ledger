"""Document classifier — keyword + structural matching, Gemini fallback."""

from __future__ import annotations

import logging

from app.classification.patterns import PATTERNS
from app.models.responses import ClassificationResult

logger = logging.getLogger(__name__)

# Minimum confidence to accept keyword-based classification
CONFIDENCE_THRESHOLD = 0.5


def classify(text: str) -> ClassificationResult:
    """Classify document type from extracted text.

    Uses keyword matching first. Falls back to Gemini if confidence < threshold.
    """
    if not text:
        return ClassificationResult(
            document_type="unknown",
            confidence=0.0,
            method="none",
        )

    text_lower = text.lower()
    best_score = 0.0
    best_type = "unknown"
    best_subtype: str | None = None

    for pattern in PATTERNS:
        score = 0.0

        # Primary signals: 0.3 each
        for keyword in pattern.primary:
            if keyword.lower() in text_lower:
                score += 0.3

        # Secondary signals: 0.1 each
        for keyword in pattern.secondary:
            if keyword.lower() in text_lower:
                score += 0.1

        # Cap at 1.0
        score = min(score, 1.0)

        if score > best_score:
            best_score = score
            best_type = pattern.doc_type
            best_subtype = pattern.subtype

    method = "keyword"

    # If low confidence, try Gemini fallback
    if best_score < CONFIDENCE_THRESHOLD:
        gemini_result = _try_gemini_classification(text)
        if gemini_result:
            return gemini_result
        method = "keyword_low_confidence"

    return ClassificationResult(
        document_type=best_type,
        subtype=best_subtype,
        confidence=round(best_score, 2),
        method=method,
    )


def _try_gemini_classification(text: str) -> ClassificationResult | None:
    """Attempt classification via Gemini API. Returns None if unavailable."""
    try:
        from app.ai.gemini_fallback import classify_document
        result = classify_document(text[:3000])
        if result:
            return result
    except Exception as e:
        logger.warning("Gemini classification fallback failed: %s", e)

    return None
