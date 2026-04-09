"""Pydantic models for MCA approval letter extraction."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FieldExtraction(BaseModel):
    """A single extracted field with its confidence score."""
    value: Any
    confidence: float  # 0.0 - 1.0


class ApprovalLetterData(BaseModel):
    """Structured data extracted from an MCA approval / offer letter."""
    lender_name: FieldExtraction | None = None
    approved_amount: FieldExtraction | None = None
    factor_rate: FieldExtraction | None = None
    buy_rate: FieldExtraction | None = None
    term_days: FieldExtraction | None = None
    payment_frequency: FieldExtraction | None = None  # daily / weekly / bi-weekly / monthly
    payment_amount: FieldExtraction | None = None
    total_payback: FieldExtraction | None = None
    net_funding: FieldExtraction | None = None
    commission_points: FieldExtraction | None = None
    stipulations: FieldExtraction | None = None  # value is list[str]
    expiration_date: FieldExtraction | None = None
    overall_confidence: float = 0.0


class ApprovalExtractionResponse(BaseModel):
    """Response envelope for the /extract-approval endpoint."""
    status: str  # "success" | "error"
    data: ApprovalLetterData | None = None
    extraction_method: str | None = None
    processing_time_ms: int = 0
    tier_logs: list[dict] = []
    error: str | None = None
