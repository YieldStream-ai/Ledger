"""Tests for the async job store (DynamoDB state + S3 files), against moto."""

from __future__ import annotations

import base64
import json
import time
import uuid

import boto3

from app.jobs.models import JobOptions, JobStatus
from app.models.responses import ParseResponse
from tests.conftest import JOBS_BUCKET


def test_create_job_writes_pending_item_with_ttl(jobs_aws):
    item = jobs_aws.create_job(JobOptions(file_name="chase.pdf", include_enrichment=True))

    job = jobs_aws.get_job(item["job_id"])
    assert job["status"] == JobStatus.PENDING_UPLOAD
    assert job["options"]["file_name"] == "chase.pdf"
    assert job["options"]["include_enrichment"] is True
    assert "business_name" not in job["options"]  # None values are dropped
    assert isinstance(job["expires_at"], int)
    assert job["expires_at"] > time.time() + 29 * 24 * 3600


def test_get_job_unknown_returns_none(jobs_aws):
    assert jobs_aws.get_job(str(uuid.uuid4())) is None


def test_claim_is_idempotent(jobs_aws):
    job_id = jobs_aws.create_job(JobOptions())["job_id"]

    assert jobs_aws.claim_job(job_id) is True
    assert jobs_aws.claim_job(job_id) is False  # duplicate SQS delivery
    assert jobs_aws.get_job(job_id)["status"] == JobStatus.PROCESSING


def test_claim_unknown_job_returns_false(jobs_aws):
    assert jobs_aws.claim_job(str(uuid.uuid4())) is False


def test_release_allows_reclaim(jobs_aws):
    job_id = jobs_aws.create_job(JobOptions())["job_id"]
    jobs_aws.claim_job(job_id)

    assert jobs_aws.release_job(job_id) is True
    assert jobs_aws.get_job(job_id)["status"] == JobStatus.PENDING_UPLOAD
    assert jobs_aws.claim_job(job_id) is True


def test_complete_and_fail(jobs_aws):
    ok = jobs_aws.create_job(JobOptions())["job_id"]
    bad = jobs_aws.create_job(JobOptions())["job_id"]

    jobs_aws.complete_job(ok, processing_time_ms=1234)
    jobs_aws.fail_job(bad, "Document quality too low")

    done = jobs_aws.get_job(ok)
    assert done["status"] == JobStatus.COMPLETED
    assert done["processing_time_ms"] == 1234
    assert "updated_at" in done

    failed = jobs_aws.get_job(bad)
    assert failed["status"] == JobStatus.FAILED
    assert failed["error"] == "Document quality too low"


def test_presign_upload_restricts_key_type_and_size(jobs_aws):
    job_id = jobs_aws.create_job(JobOptions())["job_id"]

    upload = jobs_aws.presign_upload(job_id)

    assert upload.url == f"https://{JOBS_BUCKET}.s3.us-west-2.amazonaws.com/"
    assert upload.fields["key"] == f"uploads/{job_id}.pdf"
    assert upload.fields["Content-Type"] == "application/pdf"
    policy = json.loads(base64.b64decode(upload.fields["policy"]))
    assert ["content-length-range", 1, 20 * 1024 * 1024] in policy["conditions"]
    assert {"Content-Type": "application/pdf"} in policy["conditions"]


def test_result_round_trip(jobs_aws):
    job_id = str(uuid.uuid4())
    assert jobs_aws.get_result(job_id) is None

    jobs_aws.put_result(job_id, ParseResponse(status="succeeded", processing_time_ms=42))

    result = jobs_aws.get_result(job_id)
    assert result.status == "succeeded"
    assert result.processing_time_ms == 42


def test_read_upload(jobs_aws):
    job_id = str(uuid.uuid4())
    key = jobs_aws.upload_key(job_id)
    boto3.client("s3", region_name="us-west-2").put_object(Bucket=JOBS_BUCKET, Key=key, Body=b"%PDF-1.4")

    assert jobs_aws.read_upload(key) == b"%PDF-1.4"


def test_job_id_from_key():
    from app.jobs.store import job_id_from_key

    job_id = str(uuid.uuid4())
    assert job_id_from_key(f"uploads/{job_id}.pdf") == job_id
    assert job_id_from_key(f"results/{job_id}.json") is None
    assert job_id_from_key("uploads/not-a-uuid.pdf") is None
    assert job_id_from_key(f"uploads/{job_id}.txt") is None
