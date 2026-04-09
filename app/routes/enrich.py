"""Enrichment endpoint — AI-powered financial analysis of bank statement text."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.enrichment import BankIntelligenceResult, enrich_bank_statement

logger = logging.getLogger(__name__)

router = APIRouter()


class EnrichRequest(BaseModel):
    text_content: str
    business_name: str
    industry: str | None = None
    document_hint: str | None = None


@router.post("/v1/enrich", response_model=BankIntelligenceResult)
async def enrich(request: EnrichRequest):
    """Analyze bank statement text with Gemini and return structured financial intelligence.

    This endpoint takes raw OCR-extracted text (from a prior /parse call) and
    produces 25+ structured financial fields for MCA underwriting evaluation.

    Requires GOOGLE_AI_API_KEY to be set.
    """
    try:
        result = enrich_bank_statement(
            text_content=request.text_content,
            business_name=request.business_name,
            industry=request.industry,
            document_hint=request.document_hint,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Enrichment failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Enrichment failed: {e}")
