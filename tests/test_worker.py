"""Tests for the SQS-triggered worker Lambda (worker_handler.py), against moto."""

from __future__ import annotations

import io
import json
import uuid

import boto3
import pytest

import worker_handler
from app.jobs.models import JobOptions, JobStatus
from app.models.responses import ParseResponse
from tests.conftest import JOBS_BUCKET


def _sqs_event(*keys: str, message_id: str = "msg-1") -> dict:
    """SQS batch with one message wrapping an S3 ObjectCreated event."""
    s3_event = {
        "Records": [
            {
                "eventName": "ObjectCreated:Post",
                "s3": {"bucket": {"name": JOBS_BUCKET}, "object": {"key": key}},
            }
            for key in keys
        ]
    }
    return {"Records": [{"messageId": message_id, "body": json.dumps(s3_event)}]}


def _uploaded_job(store, body: bytes = b"%PDF-1.4 stub", **options) -> str:
    job_id = store.create_job(JobOptions(**options))["job_id"]
    boto3.client("s3", region_name="us-west-2").put_object(
        Bucket=JOBS_BUCKET, Key=store.upload_key(job_id), Body=body
    )
    return job_id


@pytest.fixture
def stub_pipeline(monkeypatch):
    """Replace the parse pipeline with a recorder returning a canned response."""
    calls = []
    response = {"value": ParseResponse(status="succeeded", processing_time_ms=5)}

    def fake_process_pdf(pdf_bytes, file_name, hint, start, **kwargs):
        calls.append({"bytes": pdf_bytes, "file_name": file_name, "hint": hint, **kwargs})
        if isinstance(response["value"], Exception):
            raise response["value"]
        return response["value"]

    monkeypatch.setattr(worker_handler, "process_pdf", fake_process_pdf)
    return calls, response


def test_happy_path_completes_job_and_stores_result(jobs_aws, stub_pipeline):
    calls, _ = stub_pipeline
    job_id = _uploaded_job(jobs_aws, file_name="chase.pdf", include_enrichment=True, industry="trucking")

    out = worker_handler.handler(_sqs_event(jobs_aws.upload_key(job_id)))

    assert out == {"batchItemFailures": []}
    assert calls == [{
        "bytes": b"%PDF-1.4 stub", "file_name": "chase.pdf", "hint": None,
        "include_enrichment": True, "cross_check_balances": True,
        "business_name": None, "industry": "trucking",
    }]
    job = jobs_aws.get_job(job_id)
    assert job["status"] == JobStatus.COMPLETED
    assert "processing_time_ms" in job
    assert jobs_aws.get_result(job_id).status == "succeeded"


def test_duplicate_delivery_is_skipped(jobs_aws, stub_pipeline):
    calls, _ = stub_pipeline
    job_id = _uploaded_job(jobs_aws)
    event = _sqs_event(jobs_aws.upload_key(job_id))

    worker_handler.handler(event)
    out = worker_handler.handler(event)

    assert out == {"batchItemFailures": []}
    assert len(calls) == 1


def test_pipeline_rejection_fails_job_without_retry(jobs_aws, stub_pipeline):
    _, response = stub_pipeline
    response["value"] = ParseResponse(status="error", error="Document quality too low")
    job_id = _uploaded_job(jobs_aws)

    out = worker_handler.handler(_sqs_event(jobs_aws.upload_key(job_id)))

    assert out == {"batchItemFailures": []}
    job = jobs_aws.get_job(job_id)
    assert job["status"] == JobStatus.FAILED
    assert job["error"] == "Document quality too low"
    assert jobs_aws.get_result(job_id) is None


def test_unexpected_exception_reports_failure_and_releases_job(jobs_aws, stub_pipeline):
    calls, response = stub_pipeline
    response["value"] = RuntimeError("extractor crashed")
    job_id = _uploaded_job(jobs_aws)
    event = _sqs_event(jobs_aws.upload_key(job_id), message_id="msg-42")

    out = worker_handler.handler(event)

    assert out == {"batchItemFailures": [{"itemIdentifier": "msg-42"}]}
    assert jobs_aws.get_job(job_id)["status"] == JobStatus.PENDING_UPLOAD

    # SQS redelivers; this time the pipeline succeeds
    response["value"] = ParseResponse(status="succeeded")
    assert worker_handler.handler(event) == {"batchItemFailures": []}
    assert jobs_aws.get_job(job_id)["status"] == JobStatus.COMPLETED
    assert len(calls) == 2


def test_missing_upload_object_is_retried(jobs_aws, stub_pipeline):
    job_id = jobs_aws.create_job(JobOptions())["job_id"]  # no object in S3

    out = worker_handler.handler(_sqs_event(jobs_aws.upload_key(job_id)))

    assert out == {"batchItemFailures": [{"itemIdentifier": "msg-1"}]}
    assert jobs_aws.get_job(job_id)["status"] == JobStatus.PENDING_UPLOAD


def test_s3_test_event_is_ignored(jobs_aws, stub_pipeline):
    calls, _ = stub_pipeline
    event = {"Records": [{"messageId": "m", "body": json.dumps({"Event": "s3:TestEvent", "Bucket": JOBS_BUCKET})}]}

    assert worker_handler.handler(event) == {"batchItemFailures": []}
    assert calls == []


@pytest.mark.parametrize("key", ["uploads/not-a-uuid.pdf", f"uploads/{uuid.uuid4()}.pdf"])
def test_unknown_key_or_job_is_skipped(jobs_aws, stub_pipeline, key):
    calls, _ = stub_pipeline

    assert worker_handler.handler(_sqs_event(key)) == {"batchItemFailures": []}
    assert calls == []


def test_one_bad_message_does_not_fail_the_batch(jobs_aws, stub_pipeline):
    good = _uploaded_job(jobs_aws)
    missing = jobs_aws.create_job(JobOptions())["job_id"]
    event = {"Records": [
        _sqs_event(jobs_aws.upload_key(good), message_id="ok")["Records"][0],
        _sqs_event(jobs_aws.upload_key(missing), message_id="bad")["Records"][0],
    ]}

    assert worker_handler.handler(event) == {"batchItemFailures": [{"itemIdentifier": "bad"}]}
    assert jobs_aws.get_job(good)["status"] == JobStatus.COMPLETED


def _statement_pdf(pages: int) -> bytes:
    """Digital Chase-style statement with a transaction table, uncompressed."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter, pageCompression=0)
    balance = 12_500.00
    for page in range(pages):
        c.setFont("Helvetica", 10)
        c.drawString(72, 740, "JPMorgan Chase Bank, N.A.   CHASE BUSINESS CHECKING")
        c.drawString(72, 726, "ACME TRUCKING LLC   Account Number: ****4567")
        c.drawString(72, 712, "January 1, 2026 through January 31, 2026")
        c.drawString(72, 698, f"Beginning Balance $12,500.00   Page {page + 1} of {pages}")
        y = 670
        for i in range(45):
            amount = 250.00 + (i * 37) % 900
            balance += amount if i % 3 else -amount
            kind = "DEPOSIT STRIPE TRANSFER" if i % 3 else "ACH DEBIT FUEL CARD PAYMENT"
            c.drawString(72, y, f"01/{(i % 28) + 1:02d}   {kind} REF#{page}{i:04d}   ${amount:,.2f}   ${balance:,.2f}")
            y -= 13
        c.showPage()
    c.save()
    return buf.getvalue()


def test_real_pipeline_rejects_tiny_pdf(jobs_aws):
    """No stub: the real quality gate rejects a near-empty PDF and the job is FAILED."""
    job_id = _uploaded_job(jobs_aws, body=_statement_pdf(pages=1), file_name="tiny.pdf")

    assert worker_handler.handler(_sqs_event(jobs_aws.upload_key(job_id))) == {"batchItemFailures": []}

    job = jobs_aws.get_job(job_id)
    assert job["status"] == JobStatus.FAILED
    assert "too small" in job["error"]


def test_real_pipeline_completes_statement(jobs_aws):
    """No stub: run actual extraction/classification on a multi-page digital statement."""
    pdf = _statement_pdf(pages=8)
    assert len(pdf) > 30 * 1024  # above the quality gate's minimum size
    job_id = _uploaded_job(jobs_aws, body=pdf, file_name="chase.pdf")

    assert worker_handler.handler(_sqs_event(jobs_aws.upload_key(job_id))) == {"batchItemFailures": []}

    job = jobs_aws.get_job(job_id)
    assert job["status"] == JobStatus.COMPLETED, job.get("error")
    result = jobs_aws.get_result(job_id)
    assert result.status == "succeeded"
