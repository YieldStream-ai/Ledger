"""Async parse jobs: create a job + presigned upload, then poll for the result.

Flow:
    1. POST /jobs                → job_id + presigned S3 POST (uploads/{job_id}.pdf)
    2. client uploads the PDF straight to S3 (bypasses API Gateway's 30s / Lambda's 6 MB limits)
    3. S3 event → SQS → worker Lambda runs the same pipeline as POST /parse
    4. GET /jobs/{job_id}        → status; includes the ParseResponse once COMPLETED
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.jobs import store
from app.jobs.models import CreateJobResponse, JobOptions, JobStatus, JobStatusResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _require_configured() -> None:
    if not (settings.jobs_bucket and settings.jobs_table):
        raise HTTPException(status_code=503, detail="Async jobs are not configured (JOBS_BUCKET / JOBS_TABLE).")


@router.post("", status_code=201, response_model=CreateJobResponse)
def create_job(options: JobOptions | None = None) -> CreateJobResponse:
    """Create a job and return a presigned POST for uploading the PDF."""
    _require_configured()
    item = store.create_job(options or JobOptions())
    return CreateJobResponse(
        job_id=item["job_id"],
        status=JobStatus.PENDING_UPLOAD,
        upload=store.presign_upload(item["job_id"]),
        expires_in=store.PRESIGN_EXPIRES_SECONDS,
        max_upload_bytes=store.max_upload_bytes(),
    )


@router.get("/{job_id}", response_model=JobStatusResponse, response_model_exclude_none=True)
def get_job(job_id: str) -> JobStatusResponse:
    """Job status; the full ParseResponse is included once the job is COMPLETED."""
    _require_configured()
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")

    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    result = store.get_result(job_id) if job["status"] == JobStatus.COMPLETED else None
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        created_at=job["created_at"],
        updated_at=job.get("updated_at"),
        error=job.get("error"),
        processing_time_ms=job.get("processing_time_ms"),
        result=result,
    )
