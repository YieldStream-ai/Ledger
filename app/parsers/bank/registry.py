"""Template registry — matches bank statements to the best parser."""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import TypedDict

from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate

logger = logging.getLogger(__name__)

# Minimum confidence to use a specific bank template instead of generic
MATCH_THRESHOLD = 0.5


class TemplateMatchResult(TypedDict):
    id: str
    bank_name: str
    confidence: float
    fallback_used: bool
    signals: list[dict[str, str]]       # [{category, description}] for matched template
    alternatives: list[dict[str, object]]  # [{id, bank_name, confidence}] top runners-up


class _MatchEvent:
    __slots__ = ("template_id", "timestamp")

    def __init__(self, template_id: str) -> None:
        self.template_id = template_id
        self.timestamp = datetime.now(timezone.utc)


# In-memory match count tracking
_match_lock = threading.Lock()
_match_events: list[_MatchEvent] = []


def record_match(template_id: str) -> None:
    with _match_lock:
        _match_events.append(_MatchEvent(template_id))
        # Prune events older than 30 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        while _match_events and _match_events[0].timestamp < cutoff:
            _match_events.pop(0)


def get_match_counts() -> dict[str, int]:
    """Return {template_id: count} for the last 30 days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    counts: dict[str, int] = defaultdict(int)
    with _match_lock:
        for ev in _match_events:
            if ev.timestamp >= cutoff:
                counts[ev.template_id] += 1
    return dict(counts)


class TemplateRegistry:
    """Singleton registry. Bank templates self-register on import."""

    _templates: list[BankTemplate] = []

    @classmethod
    def register(cls, template: BankTemplate) -> None:
        cls._templates.append(template)
        logger.debug("Registered bank template: %s", template.template_id)

    @classmethod
    def match(cls, text: str, tables: list[ExtractedTable]) -> tuple[BankTemplate, float]:
        """Find the best matching bank template.

        Returns (template, confidence). Falls back to GenericBankParser
        if no template scores above threshold.
        """
        if not cls._templates:
            _ensure_loaded()

        scores = [(t, t.matches(text, tables)) for t in cls._templates]
        scores.sort(key=lambda x: x[1], reverse=True)

        if scores:
            best_template, best_score = scores[0]
            logger.info(
                "Best template match: %s (%.2f)",
                best_template.template_id,
                best_score,
            )
            if best_score >= MATCH_THRESHOLD:
                record_match(best_template.template_id)
                return best_template, best_score

        # Fallback to generic
        from app.parsers.bank.generic import GenericBankParser
        fallback = GenericBankParser()
        record_match("generic")
        return fallback, 0.0

    @classmethod
    def match_detailed(
        cls, text: str, tables: list[ExtractedTable],
    ) -> tuple[BankTemplate, float, TemplateMatchResult]:
        """Like match() but also returns rich match metadata for the API response."""
        if not cls._templates:
            _ensure_loaded()

        scores = [(t, t.matches(text, tables)) for t in cls._templates]
        scores.sort(key=lambda x: x[1], reverse=True)

        fallback_used = True
        if scores and scores[0][1] >= MATCH_THRESHOLD:
            best_template, best_score = scores[0]
            fallback_used = False
            record_match(best_template.template_id)
        else:
            from app.parsers.bank.generic import GenericBankParser
            best_template = GenericBankParser()
            best_score = 0.0
            record_match("generic")

        # Build signal descriptions for the winning template
        signals = [
            {"category": cat, "description": desc}
            for cat, desc in best_template.match_signal_defs
        ]

        # Top alternatives (excluding the winner, score > 0)
        alternatives = []
        for t, s in scores:
            if t.template_id != best_template.template_id and s > 0:
                alternatives.append({
                    "id": t.template_id,
                    "bank_name": t.bank_name,
                    "confidence": round(s, 2),
                })
            if len(alternatives) >= 3:
                break

        result = TemplateMatchResult(
            id=best_template.template_id,
            bank_name=best_template.bank_name,
            confidence=round(best_score, 2),
            fallback_used=fallback_used,
            signals=signals,
            alternatives=alternatives,
        )

        return best_template, best_score, result

    @classmethod
    def list_templates(cls) -> list[str]:
        if not cls._templates:
            _ensure_loaded()
        return [t.template_id for t in cls._templates]

    @classmethod
    def get_template_details(cls) -> list[dict[str, object]]:
        """Return details for all registered templates (for browse UI)."""
        if not cls._templates:
            _ensure_loaded()
        counts = get_match_counts()
        return [
            {
                "id": t.template_id,
                "bank_name": t.bank_name,
                "signal_count": len(t.match_signal_defs),
                "signals": [
                    {"category": cat, "description": desc}
                    for cat, desc in t.match_signal_defs
                ],
                "match_count_30d": counts.get(t.template_id, 0),
            }
            for t in cls._templates
        ]


def _ensure_loaded() -> None:
    """Import all bank template modules to trigger self-registration."""
    # fmt: off
    from app.parsers.bank import (  # noqa: F401
        chase, bofa, wells_fargo, td, pnc, us_bank,
        capital_one, regions, truist, citizens, fifth_third, bmo_harris,
        nfcu,
    )
    # fmt: on
