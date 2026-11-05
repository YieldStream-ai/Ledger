"""AWS Lambda entry point for the async parse worker (SQS-triggered).

Each SQS message carries an S3 ObjectCreated event for `uploads/{job_id}.pdf`.
For each one the worker:
    1. claims the job (PENDING_UPLOAD → PROCESSING, conditional — skips duplicate deliveries)
    2. downloads the PDF and runs the same pipeline as POST /parse (`process_pdf`)
    3. writes the ParseResponse to `results/{job_id}.json` and marks the job COMPLETED

A pipeline-level rejection (e.g. the quality gate) marks the job FAILED and is
not retried. An unexpected exception releases the job and reports the message
in `batchItemFailures`, so SQS redelivers it (and moves it to the DLQ after
maxReceiveCount attempts).
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any
from urllib.parse import unquote_plus

from app.jobs import store
from app.jobs.models import JobOptions
from app.routes.parse import process_pdf

logger = logging.getLogger("ledger.worker")
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    for record in event.get("Records", []):
        message_id = record.get("messageId", "")
        try:
            for bucket, key in _s3_objects(record):
                _process_object(bucket, key)
        except Exception:
            _log("message_failed", message_id=message_id, level=logging.ERROR, exc_info=True)
            failures.append({"itemIdentifier": message_id})
    return {"batchItemFailures": failures}


def _s3_objects(record: dict[str, Any]) -> list[tuple[str, str]]:
    """Extract (bucket, key) pairs from the S3 event in an SQS message body."""
    body = json.loads(record["body"])
    if body.get("Event") == "s3:TestEvent":  # sent once when the notification is configured
        return []
    return [
        (r["s3"]["bucket"]["name"], unquote_plus(r["s3"]["object"]["key"]))
        for r in body.get("Records", [])
        if r.get("eventName", "").startswith("ObjectCreated")
    ]


def _process_object(bucket: str, key: str) -> None:
    job_id = store.job_id_from_key(key)
    if job_id is None:
        _log("skipped_unknown_key", bucket=bucket, key=key, level=logging.WARNING)
        return

    job = store.get_job(job_id)
    if job is None or not store.claim_job(job_id):
        _log("skipped_unclaimable", job_id=job_id, status=job and job["status"])
        return

    _log("job_started", job_id=job_id)
    start = time.time()
    try:
        options = JobOptions(**job.get("options", {}))
        result = process_pdf(
            store.read_upload(key),
            options.file_name,
            options.document_type_hint,
            start,
            include_enrichment=options.include_enrichment,
            cross_check_balances=options.cross_check_balances,
            business_name=options.business_name,
            industry=options.industry,
        )
    except Exception:
        store.release_job(job_id)  # let the SQS retry claim it again
        raise

    elapsed_ms = int((time.time() - start) * 1000)
    if result.status == "error":
        store.fail_job(job_id, result.error or "Processing failed", processing_time_ms=elapsed_ms)
        _log("job_failed", job_id=job_id, error=result.error, processing_time_ms=elapsed_ms)
        return

    store.put_result(job_id, result)
    store.complete_job(job_id, processing_time_ms=elapsed_ms)
    _log("job_completed", job_id=job_id, processing_time_ms=elapsed_ms)


def _log(event: str, *, level: int = logging.INFO, exc_info: bool = False, **fields: Any) -> None:
    """One JSON object per line so CloudWatch Logs Insights can filter on job_id."""
    logger.log(level, json.dumps({"event": event, **fields}, default=str), exc_info=exc_info)
