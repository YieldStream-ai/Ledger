"""Classification-only endpoint."""

from __future__ import annotations

import tempfile
from pathlib import Path

import httpx
from fastapi import APIRouter

from app.classification.classifier import classify
from app.extraction.orchestrator import extract
from app.models.requests import ClassifyRequest
from app.models.responses import ClassifyResponse

router = APIRouter()


@router.post("/classify", response_model=ClassifyResponse)
async def classify_document(request: ClassifyRequest):
    """Download PDF, extract text, and classify the document type."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(request.file_url)
        resp.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(resp.content)
        tmp_path = Path(tmp.name)

    try:
        extraction = extract(tmp_path)
        result = classify(extraction.text)

        return ClassifyResponse(
            document_type=result.document_type,
            subtype=result.subtype,
            confidence=result.confidence,
            method=result.method,
        )
    finally:
        tmp_path.unlink(missing_ok=True)
