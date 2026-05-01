"""Main parse endpoint — orchestrates extraction, classification, and parsing."""

from __future__ import annotations

import logging
import math
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, File, Form, UploadFile

from app.ai.gemini_fallback import get_usage, reset_usage
from app.classification.classifier import classify
from app.extraction.orchestrator import extract
from app.models.bank_statement import BankStatementData, Transaction
from app.models.requests import ParseRequest
from app.models.responses import (
    ActivePosition,
    ByCategory,
    CashFlow,
    ClassificationResult,
    ConfidenceDetail,
    Debt,
    Document,
    Expenses,
    Identity,
    ParseMetadata,
    ParseResponse,
    Period,
    QualityResult,
    Revenue,
    Summary,
    SuspiciousTransfer,
    TierLog,
    Validation,
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
        cross_check_balances=request.cross_check_balances,
        business_name=request.business_name,
        industry=request.industry,
    )


@router.post("/parse/upload", response_model=ParseResponse)
async def parse_upload(
    file: UploadFile = File(...),
    document_type_hint: str | None = Form(None),
    include_enrichment: bool = Form(False),
    cross_check_balances: bool = Form(True),
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
        cross_check_balances=cross_check_balances,
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
    cross_check_balances: bool = True,
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
        template_match_detail: dict | None = None
        expected_fields: list[str] = []

        if classification.document_type == "bank_statement":
            (
                parsed_data,
                template_confidence,
                bank_detected,
                template_used,
                gemini_extraction_used,
                gemini_extraction_result,
                template_match_detail,
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

        # 7. Arithmetic validation (post-processing, not inside LLM call)
        validation_obj = None
        if cross_check_balances and classification.document_type == "bank_statement" and parsed_data:
            from app.validation.arithmetic import validate_arithmetic
            validation_obj = validate_arithmetic(parsed_data)
            if validation_obj.balance_check == "failed":
                import uuid
                from datetime import datetime, timezone
                from app.validation.review_queue import add_to_review, ReviewItem
                add_to_review(ReviewItem(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    file_name=file_name,
                    bank_detected=bank_detected,
                    discrepancy=validation_obj.discrepancy,
                    expected_ending=validation_obj.expected_ending,
                    actual_ending=validation_obj.actual_ending,
                    parsed_data_snapshot=parsed_data,
                ))

        # 8. Optional AI enrichment (bank statements only)
        enrichment_data: dict | None = None
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

        # 9. Assemble namespaced response
        text_quality = round(extraction.text_quality, 2)
        template_match_score = round(template_confidence, 2)

        is_bank_statement = classification.document_type == "bank_statement"
        document = Document(
            type=classification.document_type,
            subtype=classification.subtype,
            page_count=extraction.page_count,
            extraction_method=extraction.method,
            template_used=template_used,
        )

        if is_bank_statement and parsed_data:
            anomaly_buckets = _route_anomalies(enrichment_data)
            identity = _build_identity(parsed_data)
            period = _build_period(parsed_data)
            cash_flow = _build_cash_flow(parsed_data, enrichment_data, anomaly_buckets["cash_flow"])
            revenue = _build_revenue(parsed_data, enrichment_data, anomaly_buckets["revenue"])
            debt = _build_debt(enrichment_data, anomaly_buckets["debt"])
            expenses = Expenses()  # Phase 0: no extractor yet
            validation = _build_validation(validation_obj)
            summary = _build_summary(enrichment_data)
            by_category = _compute_by_category(
                parsed_data, enrichment_data, template_match_score, text_quality
            )
            response_parsed_data: dict | None = None
        else:
            # Non-bank-statement docs (tax returns, MCA apps) keep legacy shape
            # until they get their own namespaced schemas in later phases.
            identity = period = cash_flow = revenue = debt = expenses = validation = summary = None
            by_category = ByCategory()
            response_parsed_data = parsed_data

        return ParseResponse(
            status="succeeded",
            document=document,
            identity=identity,
            period=period,
            cash_flow=cash_flow,
            revenue=revenue,
            debt=debt,
            expenses=expenses,
            validation=validation,
            summary=summary,
            confidence=ConfidenceDetail(
                overall=overall,
                text_quality=text_quality,
                table_extraction=round(table_confidence, 2),
                template_match=template_match_score,
                by_category=by_category,
                needs_human_review=overall < 0.6,
            ),
            extraction_method=extraction.method,
            page_count=extraction.page_count,
            text_content=extraction.text,
            tables=extraction.tables,
            classification=classification,
            processing_time_ms=_elapsed(start),
            tier_logs=tier_logs,
            metadata=metadata,
            quality=quality_response,
            template_match=template_match_detail,
            parsed_data=response_parsed_data,
        )

    finally:
        tmp_path.unlink(missing_ok=True)


def _parse_bank_statement(
    text: str, tables: list
) -> tuple[dict, float, str | None, str | None, bool, dict | None, dict | None]:
    """Parse bank statement using template registry.

    Returns (parsed_data, confidence, bank_detected, template_used, gemini_used, gemini_result, template_match_detail).
    """
    template, match_confidence, template_match_detail = TemplateRegistry.match_detailed(text, tables)

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
        template_match_detail,
    )


def _elapsed(start: float) -> int:
    return int((time.time() - start) * 1000)


# ─── Bank-statement → namespace mapping ─────────────────────────────────────


def _build_identity(parsed_data: dict) -> Identity:
    return Identity(
        account_holder_name=parsed_data.get("account_holder"),
        account_number_last4=parsed_data.get("account_number_last4"),
        # business_name / address / ein / consistency_check have no extractor in Phase 0
    )


def _build_period(parsed_data: dict) -> Period:
    return Period(
        start=parsed_data.get("period_start"),
        end=parsed_data.get("period_end"),
    )


def _build_cash_flow(
    parsed_data: dict, enrichment: dict | None, anomalies: list[str]
) -> CashFlow:
    starting = parsed_data.get("beginning_balance")
    ending = parsed_data.get("ending_balance")
    net_change = (ending - starting) if (starting is not None and ending is not None) else None

    derived = parsed_data.get("derived_metrics") or {}
    daily_balances = derived.get("daily_ending_balances") or {}
    min_balance: float | None = None
    min_balance_date: str | None = None
    if daily_balances:
        min_balance_date, min_balance = min(daily_balances.items(), key=lambda kv: kv[1])

    enr = enrichment or {}
    suspicious: list[SuspiciousTransfer] = []
    for tf in enr.get("transfer_flags") or []:
        suspicious.append(SuspiciousTransfer(
            description=tf.get("description", ""),
            amount=float(tf.get("amount", 0.0)),
        ))

    return CashFlow(
        starting_balance=starting,
        ending_balance=ending,
        total_inflows=parsed_data.get("total_deposits"),
        total_outflows=parsed_data.get("total_withdrawals"),
        net_change=net_change,
        daily_balances=daily_balances,
        min_balance=min_balance,
        min_balance_date=min_balance_date,
        average_daily_balance=parsed_data.get("average_daily_balance"),
        ending_balance_trend=enr.get("edb_trend"),
        days_below_threshold=enr.get("days_below_threshold"),
        negative_balance_days=derived.get("negative_balance_days"),
        nsf_count=parsed_data.get("nsf_count"),
        nsf_count_30d=enr.get("nsf_count_30d"),
        nsf_count_60d=enr.get("nsf_count_60d"),
        nsf_count_90d=enr.get("nsf_count_90d"),
        suspicious_transfers=suspicious,
        anomalies=anomalies,
        # overdraft_events: no extractor in Phase 0
    )


def _build_revenue(
    parsed_data: dict, enrichment: dict | None, anomalies: list[str]
) -> Revenue:
    enr = enrichment or {}
    return Revenue(
        gross_deposits=parsed_data.get("total_deposits"),
        deposit_count=parsed_data.get("deposit_count") or enr.get("deposit_count"),
        monthly_average=enr.get("monthly_revenue_avg"),
        trend=enr.get("monthly_revenue_trend"),
        volatility=enr.get("revenue_volatility"),
        best_month=enr.get("best_month_revenue"),
        worst_month=enr.get("worst_month_revenue"),
        avg_transaction_size=enr.get("avg_transaction_size"),
        anomalies=anomalies,
        # processor_deposits / non_processor_inflows / recurring_revenue_estimate /
        # chargebacks / concentration / seasonality_signal: no extractor in Phase 0
    )


def _build_debt(enrichment: dict | None, anomalies: list[str]) -> Debt:
    if not enrichment:
        return Debt(anomalies=anomalies)

    positions: list[ActivePosition] = []
    for pos in enrichment.get("active_mca_positions") or []:
        positions.append(ActivePosition(
            type="mca",
            lender_name=pos.get("lender_name"),
            daily_debit=pos.get("daily_debit"),
            estimated_balance=pos.get("estimated_balance"),
            # monthly_payment / first_seen: not extracted today
        ))

    total_daily = enrichment.get("total_daily_debits")
    total_monthly = (total_daily * 30) if total_daily else None

    return Debt(
        active_positions=positions,
        total_daily_debt_service=total_daily,
        total_monthly_debt_service=total_monthly,
        stacking_burden_pct=enrichment.get("stacking_burden_pct"),
        dscr=enrichment.get("dscr"),
        lien_flags=list(enrichment.get("lien_flags") or []),
        anomalies=anomalies,
    )


def _build_summary(enrichment: dict | None) -> Summary:
    """Top-level narrative + structured handles.

    Phase 0: narrative comes from the existing Gemini `underwriting_summary`.
    `key_concerns` and `strengths` ship empty until the prompt is updated to
    emit them as structured arrays.
    """
    if not enrichment:
        return Summary()
    narrative = enrichment.get("underwriting_summary") or None
    return Summary(narrative=narrative)


# ─── Anomaly routing ────────────────────────────────────────────────────────


# Keyword-based router for `flagged_anomalies`. The current Gemini prompt
# emits a flat list of strings; we route each to the namespace whose domain
# the keywords suggest. Unmatched anomalies fall through to cash_flow as the
# safest default — MCA underwriting watches cash flow first. A future phase
# should update the Gemini prompt to emit pre-categorized anomalies.

_ANOMALY_ROUTES: list[tuple[str, tuple[str, ...]]] = [
    ("revenue", ("revenue", "deposit", "sales", "income", "credit", "merchant")),
    ("debt", ("mca", "stack", "stacking", "lien", "loan", "lender", "advance", "debt", "garnish", "levy")),
    ("cash_flow", ("withdrawal", "balance", "overdraft", "negative", "nsf", "fee", "transfer", "drain", "drop")),
]


def _route_anomalies(enrichment: dict | None) -> dict[str, list[str]]:
    """Split flagged_anomalies into per-namespace buckets by keyword."""
    buckets: dict[str, list[str]] = {"cash_flow": [], "revenue": [], "debt": []}
    if not enrichment:
        return buckets
    for raw in enrichment.get("flagged_anomalies") or []:
        text = str(raw)
        lowered = text.lower()
        routed = False
        for namespace, keywords in _ANOMALY_ROUTES:
            if any(kw in lowered for kw in keywords):
                buckets[namespace].append(text)
                routed = True
                break
        if not routed:
            buckets["cash_flow"].append(text)
    return buckets


def _build_validation(validation_obj: Any) -> Validation:
    if validation_obj is None:
        return Validation()
    return Validation(
        balance_check=validation_obj.balance_check,
        expected_ending=validation_obj.expected_ending,
        actual_ending=validation_obj.actual_ending,
        discrepancy=validation_obj.discrepancy,
    )


# ─── Per-category confidence aggregator ─────────────────────────────────────


def _is_populated(value: Any) -> bool:
    """Source-population check.

    None, empty list/dict/str → not populated.
    Numeric 0 → populated (we never inject zeros as defaults; the namespace
    builders use None for unimplemented numeric fields, so a real 0 from the
    source is still real data).
    """
    if value is None:
        return False
    if isinstance(value, (list, dict, str)) and len(value) == 0:
        return False
    return True


def _compute_by_category(
    parsed_data: dict,
    enrichment: dict | None,
    template_match: float,
    text_quality: float,
) -> ByCategory:
    """Per-category confidence.

    Formula: by_category[c] = field_population_ratio(c) * sqrt(text_quality * template_match)

    Geometric mean of text_quality and template_match penalizes weakness in
    either signal more than a flat average would, while staying in [0,1].
    Phase 0's job is shape stability — this formula will evolve as later
    phases populate currently-null fields.
    """
    derived = parsed_data.get("derived_metrics") or {}
    enr = enrichment or {}

    cash_flow_sources = [
        parsed_data.get("beginning_balance"),
        parsed_data.get("ending_balance"),
        parsed_data.get("total_deposits"),       # → total_inflows
        parsed_data.get("total_withdrawals"),    # → total_outflows
        derived.get("daily_ending_balances"),    # → daily_balances + min_balance(_date)
        derived.get("negative_balance_days"),
        parsed_data.get("nsf_count"),
        parsed_data.get("average_daily_balance"),
        enr.get("edb_trend"),
        enr.get("days_below_threshold"),
        enr.get("nsf_count_30d"),
        enr.get("nsf_count_60d"),
        enr.get("nsf_count_90d"),
        enr.get("transfer_flags"),               # → suspicious_transfers
        None,                                    # overdraft_events: no extractor yet
    ]

    revenue_sources = [
        parsed_data.get("total_deposits"),       # → gross_deposits
        parsed_data.get("deposit_count") or enr.get("deposit_count"),
        enr.get("monthly_revenue_avg"),
        enr.get("monthly_revenue_trend"),
        enr.get("revenue_volatility"),
        enr.get("best_month_revenue"),
        enr.get("worst_month_revenue"),
        enr.get("avg_transaction_size"),
        None,                                    # processor_deposits
        None,                                    # non_processor_inflows
        None,                                    # recurring_revenue_estimate
        None,                                    # chargebacks
        None,                                    # concentration
        None,                                    # seasonality_signal
    ]

    debt_sources = [
        enr.get("active_mca_positions"),
        enr.get("total_daily_debits"),
        enr.get("stacking_burden_pct"),
        enr.get("dscr"),
        enr.get("lien_flags"),
    ]

    expenses_sources = [None] * 6  # payroll, rent, utilities, insurance, software, taxes

    identity_sources = [
        parsed_data.get("account_holder"),
        parsed_data.get("account_number_last4"),
        None,                                    # business_name
        None,                                    # address
        None,                                    # ein
        None,                                    # consistency_check
    ]

    quality_factor = math.sqrt(max(0.0, text_quality) * max(0.0, template_match))

    def ratio(sources: list) -> float:
        if not sources:
            return 0.0
        populated = sum(1 for s in sources if _is_populated(s))
        return populated / len(sources)

    return ByCategory(
        cash_flow=round(ratio(cash_flow_sources) * quality_factor, 3),
        revenue=round(ratio(revenue_sources) * quality_factor, 3),
        debt=round(ratio(debt_sources) * quality_factor, 3),
        expenses=round(ratio(expenses_sources) * quality_factor, 3),
        identity=round(ratio(identity_sources) * quality_factor, 3),
    )
