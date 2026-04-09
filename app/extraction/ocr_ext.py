"""OCR fallback using pytesseract + pdf2image for scanned PDFs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.extraction.normalizer import normalize_text

logger = logging.getLogger(__name__)


@dataclass
class PageResult:
    page_num: int
    text: str
    char_count: int


@dataclass
class OCRResult:
    pages: list[PageResult] = field(default_factory=list)
    full_text: str = ""
    page_count: int = 0
    total_chars: int = 0


def extract(file_path: str | Path) -> OCRResult:
    """Convert PDF pages to images, then OCR each page with Tesseract."""
    result = OCRResult()

    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as e:
        logger.error("OCR dependencies missing: %s", e)
        return result

    try:
        images = convert_from_path(str(file_path), dpi=300)
        result.page_count = len(images)

        for i, img in enumerate(images):
            raw = pytesseract.image_to_string(img) or ""
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
        logger.warning("OCR extraction failed: %s", e)

    return result
