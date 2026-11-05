"""Job state (DynamoDB) and file storage (S3) for the async parse pipeline.

Layout in the jobs bucket:
    uploads/{job_id}.pdf    — client uploads here via a presigned POST
    results/{job_id}.json   — worker writes the ParseResponse here

Results live in S3 rather than DynamoDB because a ParseResponse (transactions +
raw text) can exceed DynamoDB's 400 KB item limit.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from functools import cache
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings
from app.jobs.models import JobOptions, JobStatus, PresignedUpload
from app.models.responses import ParseResponse

UPLOAD_PREFIX = "uploads/"
RESULT_PREFIX = "results/"
PRESIGN_EXPIRES_SECONDS = 15 * 60
JOB_TTL_SECONDS = 30 * 24 * 60 * 60


# ─── Clients (cached per process; reset_clients() for tests) ─────────────────


@cache
def _s3():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )


@cache
def _table():
    return boto3.resource("dynamodb", region_name=settings.aws_region).Table(settings.jobs_table)


def reset_clients() -> None:
    _s3.cache_clear()
    _table.cache_clear()


# ─── Keys ─────────────────────────────────────────────────────────────────────


def upload_key(job_id: str) -> str:
    return f"{UPLOAD_PREFIX}{job_id}.pdf"


def result_key(job_id: str) -> str:
    return f"{RESULT_PREFIX}{job_id}.json"


def job_id_from_key(key: str) -> str | None:
    """Return the job id for an `uploads/{uuid}.pdf` key, or None if it isn't one."""
    if not (key.startswith(UPLOAD_PREFIX) and key.endswith(".pdf")):
        return None
    candidate = key[len(UPLOAD_PREFIX):-len(".pdf")]
    try:
        return str(uuid.UUID(candidate))
    except ValueError:
        return None


# ─── Job lifecycle ────────────────────────────────────────────────────────────


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(options: JobOptions) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    item = {
        "job_id": job_id,
        "status": JobStatus.PENDING_UPLOAD.value,
        "created_at": _now(),
        "options": options.model_dump(exclude_none=True),
        "expires_at": int(time.time()) + JOB_TTL_SECONDS,
    }
    _table().put_item(Item=item, ConditionExpression="attribute_not_exists(job_id)")
    return item


def get_job(job_id: str) -> dict[str, Any] | None:
    item = _table().get_item(Key={"job_id": job_id}).get("Item")
    return _plain(item) if item else None


def claim_job(job_id: str) -> bool:
    """Atomically move PENDING_UPLOAD → PROCESSING.

    Returns False if the job doesn't exist or was already claimed — SQS is
    at-least-once, so the worker uses this to skip duplicate deliveries.
    """
    return _transition(job_id, JobStatus.PENDING_UPLOAD, JobStatus.PROCESSING)


def release_job(job_id: str) -> bool:
    """Move PROCESSING → PENDING_UPLOAD so an SQS retry can claim the job again."""
    return _transition(job_id, JobStatus.PROCESSING, JobStatus.PENDING_UPLOAD)


def complete_job(job_id: str, processing_time_ms: int) -> None:
    _finish(job_id, JobStatus.COMPLETED, processing_time_ms=processing_time_ms)


def fail_job(job_id: str, error: str, processing_time_ms: int | None = None) -> None:
    _finish(job_id, JobStatus.FAILED, error=error, processing_time_ms=processing_time_ms)


def _transition(job_id: str, expected: JobStatus, new: JobStatus) -> bool:
    try:
        _table().update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #s = :new, updated_at = :now",
            ConditionExpression="attribute_exists(job_id) AND #s = :expected",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":new": new.value, ":expected": expected.value, ":now": _now()},
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def _finish(job_id: str, status: JobStatus, *, error: str | None = None,
            processing_time_ms: int | None = None) -> None:
    names = {"#s": "status"}
    values: dict[str, Any] = {":s": status.value, ":now": _now()}
    sets = ["#s = :s", "updated_at = :now"]
    if error is not None:
        sets.append("#e = :e")
        names["#e"] = "error"
        values[":e"] = error
    if processing_time_ms is not None:
        sets.append("processing_time_ms = :ms")
        values[":ms"] = processing_time_ms
    _table().update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET " + ", ".join(sets),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


# ─── S3 ───────────────────────────────────────────────────────────────────────


def max_upload_bytes() -> int:
    return settings.max_upload_mb * 1024 * 1024


def presign_upload(job_id: str) -> PresignedUpload:
    """Presigned POST restricted to one key, PDF content type, and the size cap."""
    post = _s3().generate_presigned_post(
        Bucket=settings.jobs_bucket,
        Key=upload_key(job_id),
        Fields={"Content-Type": "application/pdf"},
        Conditions=[
            {"Content-Type": "application/pdf"},
            ["content-length-range", 1, max_upload_bytes()],
        ],
        ExpiresIn=PRESIGN_EXPIRES_SECONDS,
    )
    return PresignedUpload(url=post["url"], fields=post["fields"])


def read_upload(key: str) -> bytes:
    return _s3().get_object(Bucket=settings.jobs_bucket, Key=key)["Body"].read()


def put_result(job_id: str, result: ParseResponse) -> None:
    _s3().put_object(
        Bucket=settings.jobs_bucket,
        Key=result_key(job_id),
        Body=result.model_dump_json().encode(),
        ContentType="application/json",
    )


def get_result(job_id: str) -> ParseResponse | None:
    try:
        body = _s3().get_object(Bucket=settings.jobs_bucket, Key=result_key(job_id))["Body"].read()
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return None
        raise
    return ParseResponse.model_validate_json(body)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _plain(value: Any) -> Any:
    """DynamoDB returns numbers as Decimal; convert to int/float for Pydantic/JSON."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value
