"""Fallback PDF text extraction using PyMuPDF (fitz)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF

from app.extraction.normalizer import normalize_text

logger = logging.getLogger(__name__)


@dataclass
class PageResult:
    page_num: int
    text: str
    char_count: int


@dataclass
class PyMuPDFResult:
    pages: list[PageResult] = field(default_factory=list)
    full_text: str = ""
    page_count: int = 0
    total_chars: int = 0


def extract(file_path: str | Path) -> PyMuPDFResult:
    """Extract text from PDF using PyMuPDF. Handles some edge cases pdfplumber cannot."""
    result = PyMuPDFResult()

    try:
        doc = fitz.open(str(file_path))
        result.page_count = len(doc)

        for i, page in enumerate(doc):
            raw = page.get_text("text") or ""
            cleaned = normalize_text(raw)
            char_count = len(cleaned)

            result.pages.append(PageResult(
                page_num=i + 1,
                text=cleaned,
                char_count=char_count,
            ))

        doc.close()

        result.full_text = "\n\n".join(p.text for p in result.pages if p.text)
        result.total_chars = sum(p.char_count for p in result.pages)

    except Exception as e:
        logger.warning("PyMuPDF extraction failed: %s", e)

    return result
