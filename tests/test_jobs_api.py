"""Tests for the /jobs endpoints, against moto-mocked S3 + DynamoDB."""

from __future__ import annotations

import uuid

import boto3
import pytest
import requests
from fastapi.testclient import TestClient

from app.config import settings
from app.jobs.models import JobOptions, JobStatus
from app.main import app
from app.models.responses import ParseResponse
from tests.conftest import JOBS_BUCKET

client = TestClient(app)


def test_create_job_returns_presigned_upload(jobs_aws):
    resp = client.post("/jobs", json={"file_name": "chase.pdf", "include_enrichment": True})

    assert resp.status_code == 201
    body = resp.json()
    job_id = body["job_id"]
    assert body["status"] == "PENDING_UPLOAD"
    assert body["upload"]["fields"]["key"] == f"uploads/{job_id}.pdf"
    assert body["expires_in"] == 900
    assert body["max_upload_bytes"] == 20 * 1024 * 1024

    job = jobs_aws.get_job(job_id)
    assert job["options"]["file_name"] == "chase.pdf"
    assert job["options"]["include_enrichment"] is True


def test_create_job_without_body_uses_defaults(jobs_aws):
    resp = client.post("/jobs")

    assert resp.status_code == 201
    assert jobs_aws.get_job(resp.json()["job_id"])["options"]["file_name"] == "document.pdf"


def test_presigned_post_uploads_to_s3(jobs_aws):
    """The returned url + fields work as a real multipart POST (moto intercepts requests)."""
    upload = client.post("/jobs").json()["upload"]

    r = requests.post(upload["url"], data=upload["fields"], files={"file": ("doc.pdf", b"%PDF-1.4 test")})

    assert r.status_code in (200, 204)
    obj = boto3.client("s3", region_name="us-west-2").get_object(Bucket=JOBS_BUCKET, Key=upload["fields"]["key"])
    assert obj["Body"].read() == b"%PDF-1.4 test"


def test_get_job_pending(jobs_aws):
    job_id = client.post("/jobs").json()["job_id"]

    resp = client.get(f"/jobs/{job_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "PENDING_UPLOAD"
    assert "result" not in body
    assert "created_at" in body


def test_get_job_completed_includes_result(jobs_aws):
    job_id = jobs_aws.create_job(JobOptions())["job_id"]
    jobs_aws.claim_job(job_id)
    jobs_aws.put_result(job_id, ParseResponse(status="succeeded", processing_time_ms=812))
    jobs_aws.complete_job(job_id, processing_time_ms=812)

    body = client.get(f"/jobs/{job_id}").json()

    assert body["status"] == "COMPLETED"
    assert body["processing_time_ms"] == 812
    assert body["result"]["status"] == "succeeded"


def test_get_job_failed_includes_error(jobs_aws):
    job_id = jobs_aws.create_job(JobOptions())["job_id"]
    jobs_aws.fail_job(job_id, "Document quality too low")

    body = client.get(f"/jobs/{job_id}").json()

    assert body["status"] == JobStatus.FAILED
    assert body["error"] == "Document quality too low"
    assert "result" not in body


@pytest.mark.parametrize("job_id", [str(uuid.uuid4()), "not-a-uuid"])
def test_get_job_not_found(jobs_aws, job_id):
    assert client.get(f"/jobs/{job_id}").status_code == 404


def test_jobs_return_503_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "jobs_bucket", "")
    monkeypatch.setattr(settings, "jobs_table", "")

    assert client.post("/jobs").status_code == 503
    assert client.get(f"/jobs/{uuid.uuid4()}").status_code == 503
