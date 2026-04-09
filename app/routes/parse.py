"""Main parse endpoint — orchestrates extraction, classification, and parsing."""

from __future__ import annotations

import logging
import re
import tempfile
import time
from pathlib import Path

import httpx
from fastapi import APIRouter, File, Form, UploadFile

from app.ai.gemini_fallback import get_usage, reset_usage
from app.classification.classifier import classify
from app.extraction.orchestrator import extract
from app.models.bank_statement import BankStatementData, Transaction
from app.models.requests import ParseRequest
from app.models.responses import (
    BankProfileSample,
    ClassificationResult,
    ConfidenceDetail,
    ParseMetadata,
    ParseResponse,
    QualityResult,
    TierLog,
)
from app.parsers.bank.registry import TemplateRegistry
from app.utils.confidence import compute_field_confidence

logger = logging.getLogger(__name__)

router = APIRouter()

# Fields we expect to extract from each document type
_BANK_STATEMENT_FIELDS = [
    "bank_name", "account_holder", "account_number_last4",
    "period_start", "period_end", "beginning_balance", "ending_balance",
    "total_deposits", "total_withdrawals", "deposit_count",
    "nsf_count", "average_daily_balance",
]

_TAX_RETURN_FIELDS = [
    "filing_type", "business_name", "tax_year", "gross_receipts", "net_income",
]

_PERSONAL_TAX_FIELDS = [
    "tax_year", "name", "adjusted_gross_income", "filing_status",
]

_MCA_APPLICATION_FIELDS = [
    "business_legal_name", "ein", "monthly_revenue", "requested_funding_amount",
]


def _slugify_bank(name: str) -> str:
    """Convert bank name to a slug for grouping. 'Navy Federal Credit Union' → 'navy_federal_credit_union'."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")
    return slug


@router.post("/parse", response_model=ParseResponse)
async def parse_document(request: ParseRequest):
    """Download PDF from URL, extract text, classify, and parse."""
    start = time.time()

    # Download the file
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(request.file_url)
            resp.raise_for_status()
            pdf_bytes = resp.content
    except Exception as e:
        return ParseResponse(
            status="error",
            error=f"Failed to download file: {e}",
            processing_time_ms=_elapsed(start),
        )

    return _process_pdf(
        pdf_bytes,
        request.file_name,
        request.document_type_hint,
        start,
        include_enrichment=request.include_enrichment,
        business_name=request.business_name,
        industry=request.industry,
    )


@router.post("/parse/upload", response_model=ParseResponse)
async def parse_upload(
    file: UploadFile = File(...),
    document_type_hint: str | None = Form(None),
    include_enrichment: bool = Form(False),
    business_name: str | None = Form(None),
    industry: str | None = Form(None),
):
    """Accept PDF as multipart upload."""
    start = time.time()
    pdf_bytes = await file.read()
    return _process_pdf(
        pdf_bytes,
        file.filename or "document.pdf",
        document_type_hint,
        start,
        include_enrichment=include_enrichment,
        business_name=business_name,
        industry=industry,
    )


def _process_pdf(
    pdf_bytes: bytes,
    file_name: str,
    document_type_hint: str | None,
    start: float,
    *,
    include_enrichment: bool = False,
    business_name: str | None = None,
    industry: str | None = None,
) -> ParseResponse:
    """Core processing pipeline: quality gate → extract → classify → parse → (enrich)."""

    # Reset per-request Gemini usage tracking
    reset_usage()

    # Quality gate — pre-flight document quality check
    from app.quality.gate import check_document_quality, quick_metadata_check

    meta_passed, meta_reason = quick_metadata_check(pdf_bytes)
    if not meta_passed:
        return ParseResponse(
            status="error",
            error=meta_reason,
            processing_time_ms=_elapsed(start),
            quality=QualityResult(
                passed=False,
                overall_score=0,
                processing_allowed=False,
                issues=["METADATA_CHECK_FAILED"],
                rejection_reason=meta_reason,
            ),
        )

    quality_result = check_document_quality(pdf_bytes)
    quality_response = QualityResult(
        passed=quality_result.passed,
        overall_score=quality_result.overall_score,
        processing_allowed=quality_result.processing_allowed,
        issues=[i.value for i in quality_result.issues],
        rejection_reason=quality_result.rejection_reason,
        recommendation=quality_result.recommendation,
    )

    if not quality_result.processing_allowed:
        return ParseResponse(
            status="error",
            error=quality_result.rejection_reason or "Document quality too low for reliable parsing.",
            processing_time_ms=_elapsed(start),
            quality=quality_response,
        )

    # Write to temp file (extractors need a file path)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = Path(tmp.name)

    try:
        # 1. Extract text + tables
        extraction = extract(tmp_path)

        # Convert orchestrator tier attempts to TierLog models
        tier_logs: list[TierLog] = [
            TierLog(
                tier=a.tier,
                tier_order=a.tier_order,
                status=a.status,
                failure_reason=a.failure_reason,
                text_char_count=a.text_char_count,
                table_count=a.table_count,
                confidence_score=a.confidence_score,
                processing_time_ms=a.processing_time_ms,
            )
            for a in extraction.tier_attempts
        ]

        if extraction.method == "failed" and extraction.char_count < 10:
            return ParseResponse(
                status="error",
                error="Failed to extract text from PDF — all methods returned empty",
                extraction_method="failed",
                processing_time_ms=_elapsed(start),
                tier_logs=tier_logs,
                metadata=ParseMetadata(
                    winning_tier=None,
                    tiers_attempted=len(tier_logs),
                    total_processing_time_ms=_elapsed(start),
                    needs_human_review=True,
                ),
            )

        # 2. Classify document
        if document_type_hint:
            classification = ClassificationResult(
                document_type=document_type_hint,
                confidence=1.0,
                method="hint",
            )
        else:
            classification = classify(extraction.text)

        # 3. Parse based on document type
        parsed_data = None
        template_confidence = 0.0
        bank_detected: str | None = None
        template_used: str | None = None
        gemini_extraction_used = False
        gemini_extraction_result: dict | None = None
        expected_fields: list[str] = []

        if classification.document_type == "bank_statement":
            (
                parsed_data,
                template_confidence,
                bank_detected,
                template_used,
                gemini_extraction_used,
                gemini_extraction_result,
            ) = _parse_bank_statement(extraction.text, extraction.tables)
            expected_fields = _BANK_STATEMENT_FIELDS
        elif classification.document_type in ("business_tax_return",):
            from app.parsers.tax.business import parse_business_tax_return
            result = parse_business_tax_return(extraction.text)
            parsed_data = result.model_dump()
            template_confidence = compute_field_confidence(
                parsed_data, ["gross_receipts", "net_income", "business_name", "tax_year"]
            )
            expected_fields = _TAX_RETURN_FIELDS
        elif classification.document_type == "personal_tax_return":
            from app.parsers.tax.personal import parse_personal_tax_return
            result = parse_personal_tax_return(extraction.text)
            parsed_data = result.model_dump()
            template_confidence = compute_field_confidence(
                parsed_data, ["adjusted_gross_income", "tax_year", "name"]
            )
            expected_fields = _PERSONAL_TAX_FIELDS
        elif classification.document_type == "mca_application":
            from app.parsers.mca_application import parse_mca_application
            result = parse_mca_application(extraction.text)
            parsed_data = result.model_dump()
            template_confidence = compute_field_confidence(
                parsed_data, ["business_legal_name", "requested_funding_amount"]
            )
            expected_fields = _MCA_APPLICATION_FIELDS

        # If Gemini was used for bank extraction, add a tier log
        if gemini_extraction_used:
            gemini_tier_order = len(tier_logs) + 1
            tier_logs.append(TierLog(
                tier="gemini",
                tier_order=gemini_tier_order,
                status="success",
                text_char_count=0,
                table_count=0,
                confidence_score=template_confidence,
                processing_time_ms=0,
            ))

        # If Gemini was used for classification, add a tier log
        if classification.method == "gemini":
            gemini_tier_order = len(tier_logs) + 1
            tier_logs.append(TierLog(
                tier="gemini",
                tier_order=gemini_tier_order,
                status="success",
                failure_reason=None,
                text_char_count=0,
                table_count=0,
                confidence_score=classification.confidence,
                processing_time_ms=0,
            ))

        # 4. Compute fields_missing and fields_extracted_count
        fields_missing: list[str] = []
        fields_extracted_count = 0
        if parsed_data and expected_fields:
            for f in expected_fields:
                val = parsed_data.get(f)
                if val is None or val == 0 and f != "nsf_count":
                    fields_missing.append(f)
                else:
                    fields_extracted_count += 1

        # 5. Compute overall confidence
        table_confidence = min(len(extraction.tables) / 3, 1.0) if extraction.tables else 0.3
        overall = round(
            (extraction.text_quality * 0.4 + classification.confidence * 0.3 + template_confidence * 0.3),
            2,
        )

        # 6. Build metadata
        gemini_usage = get_usage()

        metadata = ParseMetadata(
            winning_tier=extraction.method if extraction.method != "failed" else None,
            tiers_attempted=len(tier_logs),
            total_processing_time_ms=_elapsed(start),
            bank_detected=bank_detected,
            template_used=template_used,
            template_match_confidence=round(template_confidence, 2),
            document_type_classified=classification.document_type,
            classification_confidence=round(classification.confidence, 2),
            classification_method=classification.method,
            fields_extracted_count=fields_extracted_count,
            fields_missing=fields_missing,
            needs_human_review=overall < 0.6,
            gemini_tokens_used=gemini_usage.tokens_used if gemini_usage.tokens_used > 0 else None,
            gemini_cost_estimate=round(gemini_usage.cost_estimate, 4) if gemini_usage.cost_estimate > 0 else None,
        )

        # 7. Build bank profile sample for template learning
        bank_profile_sample = None
        if classification.document_type == "bank_statement" and bank_detected:
            period_str = None
            if parsed_data:
                ps = parsed_data.get("period_start")
                pe = parsed_data.get("period_end")
                if ps and pe:
                    period_str = f"{ps} to {pe}"

            bank_profile_sample = BankProfileSample(
                bank_name=bank_detected,
                bank_slug=_slugify_bank(bank_detected),
                period=period_str,
                raw_text_sample=extraction.text[:3000],
                gemini_extraction=gemini_extraction_result,
                fields_missing=fields_missing,
                observed_patterns=gemini_extraction_result.get("observed_patterns", {}) if gemini_extraction_result else {},
                has_template=template_used != "generic",
            )

        # Optional AI enrichment
        enrichment_data = None
        if include_enrichment and classification.document_type == "bank_statement" and extraction.text:
            try:
                from app.ai.enrichment import enrich_bank_statement
                enrichment_result = enrich_bank_statement(
                    text_content=extraction.text,
                    business_name=business_name or "Unknown",
                    industry=industry,
                )
                enrichment_data = enrichment_result.model_dump()
            except Exception as e:
                logger.warning(f"Enrichment failed (non-fatal): {e}")

        return ParseResponse(
            status="success",
            extraction_method=extraction.method,
            page_count=extraction.page_count,
            text_content=extraction.text,
            tables=extraction.tables,
            classification=classification,
            parsed_data=parsed_data,
            confidence=ConfidenceDetail(
                overall=overall,
                text_quality=round(extraction.text_quality, 2),
                table_extraction=round(table_confidence, 2),
                template_match=round(template_confidence, 2),
                needs_human_review=overall < 0.6,
            ),
            processing_time_ms=_elapsed(start),
            tier_logs=tier_logs,
            metadata=metadata,
            bank_profile_sample=bank_profile_sample,
            quality=quality_response,
            enrichment=enrichment_data,
        )

    finally:
        tmp_path.unlink(missing_ok=True)


def _parse_bank_statement(
    text: str, tables: list
) -> tuple[dict, float, str | None, str | None, bool, dict | None]:
    """Parse bank statement using template registry.

    Returns (parsed_data, confidence, bank_detected, template_used, gemini_used, gemini_result).
    """
    template, match_confidence = TemplateRegistry.match(text, tables)

    summary = template.extract_summary(text, tables)
    transactions = template.extract_transactions(text, tables)
    derived = template.compute_derived_metrics(summary, transactions)

    bank_detected = summary.bank_name
    template_used_id = template.template_id
    gemini_used = False
    gemini_result: dict | None = None

    # If template match was low and generic parser got poor results, try Gemini
    # Enhanced: Gemini now extracts transactions too, not just summary
    if match_confidence < 0.3 and summary.total_deposits is None and summary.ending_balance is None:
        from app.ai.gemini_fallback import extract_bank_statement_gemini
        gemini_data = extract_bank_statement_gemini(text)
        if gemini_data:
            gemini_used = True
            gemini_result = gemini_data

            # Merge Gemini summary fields into our summary
            for key in [
                "bank_name", "account_holder", "account_number_last4",
                "period_start", "period_end", "beginning_balance", "ending_balance",
                "total_deposits", "total_withdrawals", "nsf_count",
                "average_daily_balance", "deposit_count",
            ]:
                value = gemini_data.get(key)
                if value is not None and hasattr(summary, key):
                    current = getattr(summary, key)
                    if current is None:
                        setattr(summary, key, value)

            # Update bank_detected from Gemini if we didn't have it
            if not bank_detected and gemini_data.get("bank_name"):
                bank_detected = gemini_data["bank_name"]

            # Merge Gemini transactions if regex found none
            if not transactions and gemini_data.get("transactions"):
                for txn in gemini_data["transactions"]:
                    try:
                        transactions.append(Transaction(
                            date=txn.get("date", ""),
                            description=txn.get("description", ""),
                            amount=float(txn.get("amount", 0)),
                            running_balance=float(txn["running_balance"]) if txn.get("running_balance") is not None else None,
                            type=txn.get("type", "debit"),
                        ))
                    except (ValueError, TypeError):
                        continue

                # Recompute derived metrics with Gemini transactions
                derived = template.compute_derived_metrics(summary, transactions)

    data = BankStatementData(
        bank_name=summary.bank_name,
        template_used=summary.template_used,
        account_holder=summary.account_holder,
        account_number_last4=summary.account_number_last4,
        period_start=summary.period_start,
        period_end=summary.period_end,
        beginning_balance=summary.beginning_balance,
        ending_balance=summary.ending_balance,
        total_deposits=summary.total_deposits,
        total_withdrawals=summary.total_withdrawals,
        deposit_count=summary.deposit_count or len([t for t in transactions if t.type == "credit"]),
        nsf_count=summary.nsf_count,
        average_daily_balance=summary.average_daily_balance,
        transactions=transactions,
        derived_metrics=derived,
    )

    # Confidence based on how many key fields we extracted
    field_confidence = compute_field_confidence(
        data.model_dump(),
        ["total_deposits", "total_withdrawals", "ending_balance", "period_start", "period_end"],
    )

    return (
        data.model_dump(),
        round(max(match_confidence, field_confidence), 2),
        bank_detected,
        template_used_id,
        gemini_used,
        gemini_result,
    )


def _elapsed(start: float) -> int:
    return int((time.time() - start) * 1000)
