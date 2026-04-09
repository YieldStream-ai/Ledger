"""Primary PDF text extraction using pdfplumber."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

from app.extraction.normalizer import normalize_text

logger = logging.getLogger(__name__)


@dataclass
class PageResult:
    page_num: int
    text: str
    char_count: int


@dataclass
class PdfplumberResult:
    pages: list[PageResult] = field(default_factory=list)
    full_text: str = ""
    page_count: int = 0
    total_chars: int = 0


def extract(file_path: str | Path) -> PdfplumberResult:
    """Extract text from PDF using pdfplumber. Returns per-page and full text."""
    result = PdfplumberResult()

    try:
        with pdfplumber.open(file_path) as pdf:
            result.page_count = len(pdf.pages)

            for i, page in enumerate(pdf.pages):
                raw = page.extract_text() or ""
                cleaned = normalize_text(raw)
                char_count = len(cleaned)

                result.pages.append(PageResult(
                    page_num=i + 1,
                    text=cleaned,
                    char_count=char_count,
                ))

            result.full_text = "\n\n".join(p.text for p in result.pages if p.text)
            result.total_chars = sum(p.char_count for p in result.pages)

    except Exception as e:
        logger.warning("pdfplumber extraction failed: %s", e)
        # Return empty result — orchestrator will try next method

    return result
