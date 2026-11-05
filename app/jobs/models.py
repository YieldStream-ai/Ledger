"""Request/response models for the async job API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from app.models.responses import ParseResponse


class JobStatus(StrEnum):
    PENDING_UPLOAD = "PENDING_UPLOAD"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobOptions(BaseModel):
    """Parse options captured at job creation and replayed by the worker.

    Mirrors `ParseRequest` (app/models/requests.py) minus `file_url` — the file
    arrives via the presigned S3 upload instead.
    """

    file_name: str = "document.pdf"
    document_type_hint: str | None = None
    include_enrichment: bool = False
    cross_check_balances: bool = True
    business_name: str | None = None
    industry: str | None = None


class PresignedUpload(BaseModel):
    """Presigned S3 POST: send `fields` plus the file (as `file`) to `url`."""

    url: str
    fields: dict[str, str]


class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    upload: PresignedUpload
    expires_in: int
    max_upload_bytes: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: str
    updated_at: str | None = None
    error: str | None = None
    processing_time_ms: int | None = None
    result: ParseResponse | None = None
