"""Template registry — matches bank statements to the best parser."""

from __future__ import annotations

import logging

from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate

logger = logging.getLogger(__name__)

# Minimum confidence to use a specific bank template instead of generic
MATCH_THRESHOLD = 0.5


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
                return best_template, best_score

        # Fallback to generic
        from app.parsers.bank.generic import GenericBankParser
        fallback = GenericBankParser()
        return fallback, 0.0

    @classmethod
    def list_templates(cls) -> list[str]:
        if not cls._templates:
            _ensure_loaded()
        return [t.template_id for t in cls._templates]


def _ensure_loaded() -> None:
    """Import all bank template modules to trigger self-registration."""
    # fmt: off
    from app.parsers.bank import (  # noqa: F401
        chase, bofa, wells_fargo, td, pnc, us_bank,
        capital_one, regions, truist, citizens, fifth_third, bmo_harris,
        nfcu,
    )
    # fmt: on
