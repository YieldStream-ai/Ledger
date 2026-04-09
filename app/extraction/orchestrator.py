"""Extraction orchestrator — tries pdfplumber -> PyMuPDF -> OCR -> LlamaParse in order.

Each tier attempt is timed and logged for fallback analytics.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings
from app.extraction import pdfplumber_ext, pymupdf_ext, ocr_ext, llamaparse_ext
from app.extraction.table_extractor import extract_tables
from app.extraction.normalizer import add_page_boundaries
from app.models.responses import ExtractedTable

logger = logging.getLogger(__name__)


@dataclass
class TierAttempt:
    """Record of a single extraction tier attempt."""
    tier: str
    tier_order: int
    status: str = "failed"          # "success" | "failed"
    failure_reason: str | None = None
    text_char_count: int = 0
    table_count: int = 0
    confidence_score: float = 0.0
    processing_time_ms: int = 0


@dataclass
class ExtractionResult:
    text: str = ""
    pages: list[str] = field(default_factory=list)
    page_count: int = 0
    tables: list[ExtractedTable] = field(default_factory=list)
    method: str = "none"
    text_quality: float = 0.0  # 0-1 confidence in text quality
    char_count: int = 0
    tier_attempts: list[TierAttempt] = field(default_factory=list)


def _compute_text_quality(text: str, page_count: int) -> float:
    """Heuristic text quality score based on character density and content signals."""
    if not text or page_count == 0:
        return 0.0

    chars_per_page = len(text) / page_count

    # Very low chars/page suggests poor extraction
    if chars_per_page < 50:
        return 0.2
    if chars_per_page < 200:
        return 0.5
    if chars_per_page < 500:
        return 0.7

    # Check for encoding artifacts (lots of replacement chars)
    artifact_ratio = text.count("\ufffd") / max(len(text), 1)
    if artifact_ratio > 0.05:
        return 0.5

    return 0.9


def _elapsed_ms(start: float) -> int:
    return int((time.time() - start) * 1000)


def extract(file_path: str | Path) -> ExtractionResult:
    """Try extractors in order until one produces sufficient text.

    Cascade: pdfplumber → PyMuPDF → OCR → LlamaParse (cloud fallback)
    Each tier attempt is recorded in result.tier_attempts for logging.
    """
    threshold = settings.min_text_threshold
    result = ExtractionResult()
    tier_order = 0

    # ── Tier 1: pdfplumber (primary — best for tables) ──────────────────────
    tier_order += 1
    tier_start = time.time()
    attempt = TierAttempt(tier="pdfplumber", tier_order=tier_order)

    try:
        logger.info("Trying pdfplumber extraction...")
        plumber = pdfplumber_ext.extract(file_path)
        attempt.text_char_count = plumber.total_chars
        attempt.processing_time_ms = _elapsed_ms(tier_start)

        if plumber.total_chars >= threshold:
            logger.info("pdfplumber succeeded: %d chars across %d pages", plumber.total_chars, plumber.page_count)
            result.text = add_page_boundaries([p.text for p in plumber.pages])
            result.pages = [p.text for p in plumber.pages]
            result.page_count = plumber.page_count
            result.method = "pdfplumber"
            result.char_count = plumber.total_chars
            result.text_quality = _compute_text_quality(result.text, result.page_count)
            result.tables = extract_tables(file_path)

            attempt.status = "success"
            attempt.table_count = len(result.tables)
            attempt.confidence_score = round(result.text_quality, 2)
            result.tier_attempts.append(attempt)
            return result
        else:
            attempt.status = "failed"
            attempt.failure_reason = f"extracted text below {threshold} char threshold ({plumber.total_chars} chars)"
    except Exception as e:
        attempt.status = "failed"
        attempt.failure_reason = str(e)
        attempt.processing_time_ms = _elapsed_ms(tier_start)
        logger.warning("pdfplumber extraction failed: %s", e)

    result.tier_attempts.append(attempt)

    # ── Tier 2: PyMuPDF (fallback — handles some corrupted/encrypted PDFs) ──
    tier_order += 1
    tier_start = time.time()
    attempt = TierAttempt(tier="pymupdf", tier_order=tier_order)

    try:
        logger.info("pdfplumber insufficient, trying PyMuPDF...")
        mupdf = pymupdf_ext.extract(file_path)
        attempt.text_char_count = mupdf.total_chars
        attempt.processing_time_ms = _elapsed_ms(tier_start)

        if mupdf.total_chars >= threshold:
            logger.info("PyMuPDF succeeded: %d chars across %d pages", mupdf.total_chars, mupdf.page_count)
            result.text = add_page_boundaries([p.text for p in mupdf.pages])
            result.pages = [p.text for p in mupdf.pages]
            result.page_count = mupdf.page_count
            result.method = "pymupdf"
            result.char_count = mupdf.total_chars
            result.text_quality = _compute_text_quality(result.text, result.page_count)
            result.tables = extract_tables(file_path)

            attempt.status = "success"
            attempt.table_count = len(result.tables)
            attempt.confidence_score = round(result.text_quality, 2)
            result.tier_attempts.append(attempt)
            return result
        else:
            attempt.status = "failed"
            attempt.failure_reason = f"extracted text below {threshold} char threshold ({mupdf.total_chars} chars)"
    except Exception as e:
        attempt.status = "failed"
        attempt.failure_reason = str(e)
        attempt.processing_time_ms = _elapsed_ms(tier_start)
        logger.warning("PyMuPDF extraction failed: %s", e)

    result.tier_attempts.append(attempt)

    # ── Tier 3: OCR (scanned PDFs — slow but handles images) ────────────────
    tier_order += 1
    tier_start = time.time()
    attempt = TierAttempt(tier="ocr", tier_order=tier_order)

    try:
        logger.info("PyMuPDF insufficient, trying OCR...")
        ocr = ocr_ext.extract(file_path)
        attempt.text_char_count = ocr.total_chars
        attempt.processing_time_ms = _elapsed_ms(tier_start)

        if ocr.total_chars >= threshold:
            logger.info("OCR succeeded: %d chars across %d pages", ocr.total_chars, ocr.page_count)
            result.text = add_page_boundaries([p.text for p in ocr.pages])
            result.pages = [p.text for p in ocr.pages]
            result.page_count = ocr.page_count
            result.method = "ocr"
            result.char_count = ocr.total_chars
            result.text_quality = _compute_text_quality(result.text, result.page_count) * 0.8

            attempt.status = "success"
            attempt.confidence_score = round(result.text_quality, 2)
            result.tier_attempts.append(attempt)
            return result
        else:
            attempt.status = "failed"
            attempt.failure_reason = f"extracted text below {threshold} char threshold ({ocr.total_chars} chars)"
    except Exception as e:
        attempt.status = "failed"
        attempt.failure_reason = str(e)
        attempt.processing_time_ms = _elapsed_ms(tier_start)
        logger.warning("OCR extraction failed: %s", e)

    result.tier_attempts.append(attempt)

    # ── Tier 4: LlamaParse (cloud fallback — upload/poll, ~30k free pages/mo) ─
    tier_order += 1
    tier_start = time.time()
    attempt = TierAttempt(tier="llamaparse_free", tier_order=tier_order)

    if not llamaparse_ext.is_available():
        attempt.status = "skipped"
        attempt.failure_reason = "LLAMA_CLOUD_API_KEY not configured"
        attempt.processing_time_ms = 0
        result.tier_attempts.append(attempt)
    else:
        try:
            logger.info("Local extractors insufficient, trying LlamaParse...")
            llama = llamaparse_ext.extract(file_path)
            attempt.text_char_count = llama.total_chars
            attempt.processing_time_ms = _elapsed_ms(tier_start)

            if llama.total_chars >= threshold:
                logger.info("LlamaParse succeeded: %d chars", llama.total_chars)
                result.text = llama.full_text
                result.pages = [p.text for p in llama.pages]
                result.page_count = llama.page_count
                result.method = "llamaparse_free"
                result.char_count = llama.total_chars
                # LlamaParse returns markdown, not raw text — slightly lower quality score
                result.text_quality = _compute_text_quality(result.text, max(result.page_count, 1)) * 0.85

                attempt.status = "success"
                attempt.confidence_score = round(result.text_quality, 2)
                result.tier_attempts.append(attempt)
                return result
            else:
                attempt.status = "failed"
                attempt.failure_reason = f"extracted text below {threshold} char threshold ({llama.total_chars} chars)"
        except Exception as e:
            attempt.status = "failed"
            attempt.failure_reason = str(e)
            attempt.processing_time_ms = _elapsed_ms(tier_start)
            logger.warning("LlamaParse extraction failed: %s", e)

        result.tier_attempts.append(attempt)

    # ── All methods failed ──────────────────────────────────────────────────
    logger.warning("All extraction methods failed for %s", file_path)

    # Return the best partial result we got from any tier
    all_results = [
        ("pdfplumber", plumber if "plumber" in dir() else None),
        ("pymupdf", mupdf if "mupdf" in dir() else None),
        ("ocr", ocr if "ocr" in dir() else None),
    ]
    valid = [(name, r) for name, r in all_results if r is not None and r.total_chars > 0]

    if valid:
        _, best = max(valid, key=lambda x: x[1].total_chars)
        result.text = best.full_text
        result.pages = [p.text for p in best.pages]
        result.page_count = best.page_count
        result.char_count = best.total_chars

    result.method = "failed"
    result.text_quality = 0.1
    return result
