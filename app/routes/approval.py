"""Approval letter extraction endpoint.

Accepts an MCA approval letter (PDF or image), extracts text via the
cascading orchestrator, then parses structured offer terms using
regex patterns with Gemini fallback for low-confidence results.
"""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path

import httpx
from fastapi import APIRouter, File, Form, UploadFile

from app.ai.gemini_fallback import (
    extract_approval_letter_gemini,
    get_usage,
    reset_usage,
)
from app.extraction.orchestrator import extract
from app.models.approval_letter import (
    ApprovalExtractionResponse,
    ApprovalLetterData,
    FieldExtraction,
)
from app.parsers.approval_letter import parse_approval_letter

logger = logging.getLogger(__name__)

router = APIRouter()

# Gemini fallback threshold — if regex parser overall confidence is below this,
# we call Gemini to attempt a full extraction.
_GEMINI_THRESHOLD = 0.3


@router.post("/extract-approval", response_model=ApprovalExtractionResponse)
async def extract_approval(
    file: UploadFile = File(...),
):
    """Accept an approval letter as multipart upload, extract offer terms."""
    start = time.time()
    reset_usage()

    pdf_bytes = await file.read()

    # Write to temp file (extractors need a file path)
    suffix = Path(file.filename or "doc.pdf").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = Path(tmp.name)

    try:
        # 1. Extract text via cascading pipeline
        extraction = extract(tmp_path)

        tier_logs = [
            {
                "tier": a.tier,
                "tier_order": a.tier_order,
                "status": a.status,
                "failure_reason": a.failure_reason,
                "text_char_count": a.text_char_count,
                "confidence_score": a.confidence_score,
                "processing_time_ms": a.processing_time_ms,
            }
            for a in extraction.tier_attempts
        ]

        if extraction.method == "failed" or extraction.char_count < 10:
            return ApprovalExtractionResponse(
                status="error",
                error="Failed to extract text from document — all extraction methods returned empty",
                processing_time_ms=_elapsed(start),
                tier_logs=tier_logs,
            )

        # 2. Parse with regex patterns
        data = parse_approval_letter(extraction.text)

        # 3. Gemini fallback if confidence is too low
        gemini_used = False
        if data.overall_confidence < _GEMINI_THRESHOLD:
            gemini_data = extract_approval_letter_gemini(extraction.text)
            if gemini_data:
                gemini_used = True
                data = _merge_gemini(data, gemini_data)
                tier_logs.append({
                    "tier": "gemini",
                    "tier_order": len(tier_logs) + 1,
                    "status": "success",
                    "text_char_count": 0,
                    "confidence_score": data.overall_confidence,
                    "processing_time_ms": 0,
                })

        method = extraction.method
        if gemini_used:
            method = f"{method}+gemini"

        return ApprovalExtractionResponse(
            status="success",
            data=data,
            extraction_method=method,
            processing_time_ms=_elapsed(start),
            tier_logs=tier_logs,
        )

    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/extract-approval/url", response_model=ApprovalExtractionResponse)
async def extract_approval_from_url(
    file_url: str = Form(...),
):
    """Download an approval letter from URL, then extract offer terms."""
    start = time.time()
    reset_usage()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(file_url)
            resp.raise_for_status()
            pdf_bytes = resp.content
    except Exception as e:
        return ApprovalExtractionResponse(
            status="error",
            error=f"Failed to download file: {e}",
            processing_time_ms=_elapsed(start),
        )

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = Path(tmp.name)

    try:
        extraction = extract(tmp_path)

        tier_logs = [
            {
                "tier": a.tier,
                "tier_order": a.tier_order,
                "status": a.status,
                "failure_reason": a.failure_reason,
                "text_char_count": a.text_char_count,
                "confidence_score": a.confidence_score,
                "processing_time_ms": a.processing_time_ms,
            }
            for a in extraction.tier_attempts
        ]

        if extraction.method == "failed" or extraction.char_count < 10:
            return ApprovalExtractionResponse(
                status="error",
                error="Failed to extract text from document",
                processing_time_ms=_elapsed(start),
                tier_logs=tier_logs,
            )

        data = parse_approval_letter(extraction.text)

        gemini_used = False
        if data.overall_confidence < _GEMINI_THRESHOLD:
            gemini_data = extract_approval_letter_gemini(extraction.text)
            if gemini_data:
                gemini_used = True
                data = _merge_gemini(data, gemini_data)
                tier_logs.append({
                    "tier": "gemini",
                    "tier_order": len(tier_logs) + 1,
                    "status": "success",
                    "text_char_count": 0,
                    "confidence_score": data.overall_confidence,
                    "processing_time_ms": 0,
                })

        method = extraction.method
        if gemini_used:
            method = f"{method}+gemini"

        return ApprovalExtractionResponse(
            status="success",
            data=data,
            extraction_method=method,
            processing_time_ms=_elapsed(start),
            tier_logs=tier_logs,
        )

    finally:
        tmp_path.unlink(missing_ok=True)


def _merge_gemini(existing: ApprovalLetterData, gemini: dict) -> ApprovalLetterData:
    """Merge Gemini extraction into existing regex results.

    Gemini fills in fields that regex missed. If regex already extracted a
    field, keep the regex value (it's keyword-anchored and more reliable).
    """
    field_map = {
        "lender_name": "lender_name",
        "approved_amount": "approved_amount",
        "factor_rate": "factor_rate",
        "buy_rate": "buy_rate",
        "term_days": "term_days",
        "payment_frequency": "payment_frequency",
        "payment_amount": "payment_amount",
        "total_payback": "total_payback",
        "net_funding": "net_funding",
        "commission_points": "commission_points",
        "expiration_date": "expiration_date",
    }

    for gemini_key, model_key in field_map.items():
        current = getattr(existing, model_key)
        gemini_val = gemini.get(gemini_key)
        if current is None and gemini_val is not None:
            setattr(existing, model_key, FieldExtraction(
                value=gemini_val,
                confidence=0.65,  # Gemini extractions get moderate confidence
            ))

    # Merge stipulations
    if existing.stipulations is None and gemini.get("stipulations"):
        stips = gemini["stipulations"]
        if isinstance(stips, list) and len(stips) > 0:
            existing.stipulations = FieldExtraction(value=stips, confidence=0.60)

    # Recompute overall confidence
    fields = [
        existing.approved_amount, existing.factor_rate, existing.term_days,
        existing.payment_frequency, existing.payment_amount,
        existing.total_payback, existing.net_funding,
    ]
    extracted = [f for f in fields if f is not None]
    if extracted:
        overall = sum(f.confidence for f in extracted) / len(extracted)
        key_count = sum(
            1 for f in [existing.approved_amount, existing.factor_rate, existing.term_days]
            if f is not None
        )
        overall = min(1.0, overall + (key_count * 0.05))
        existing.overall_confidence = round(overall, 2)

    return existing


def _elapsed(start: float) -> int:
    return int((time.time() - start) * 1000)
