"""LlamaParse cloud API fallback for PDFs that local extractors can't handle."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from app.config import settings
from app.extraction.normalizer import normalize_text

logger = logging.getLogger(__name__)

LLAMA_API_BASE = "https://api.cloud.llamaindex.ai/api/parsing"
POLL_MAX_ATTEMPTS = 12
POLL_DELAY_SECONDS = 5


@dataclass
class PageResult:
    page_num: int
    text: str
    char_count: int


@dataclass
class LlamaParseResult:
    pages: list[PageResult] = field(default_factory=list)
    full_text: str = ""
    page_count: int = 0
    total_chars: int = 0


def is_available() -> bool:
    """Check if LlamaParse API key is configured."""
    return bool(settings.llama_cloud_api_key)


def extract(file_path: str | Path) -> LlamaParseResult:
    """Upload PDF to LlamaParse, poll for result, return extracted text.

    This is a synchronous blocking call that can take up to 60s (12 polls × 5s).
    Only used as a fallback when local extractors fail.
    """
    result = LlamaParseResult()

    if not settings.llama_cloud_api_key:
        logger.debug("LlamaParse API key not configured — skipping")
        return result

    api_key = settings.llama_cloud_api_key

    try:
        # 1. Upload the file
        file_path = Path(file_path)
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        with httpx.Client(timeout=30.0) as client:
            upload_resp = client.post(
                f"{LLAMA_API_BASE}/upload",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (file_path.name, file_bytes, "application/pdf")},
            )

            if upload_resp.status_code != 200:
                logger.warning(
                    "LlamaParse upload failed (%d): %s",
                    upload_resp.status_code,
                    upload_resp.text[:200],
                )
                return result

            job_id = upload_resp.json().get("id")
            if not job_id:
                logger.warning("LlamaParse upload returned no job ID")
                return result

            logger.info("LlamaParse job started: %s", job_id)

            # 2. Poll for completion
            markdown = _poll_for_result(client, api_key, job_id)

        if not markdown or len(markdown) < 10:
            logger.warning("LlamaParse returned empty or very short result")
            return result

        # 3. Normalize and structure the result
        cleaned = normalize_text(markdown)
        result.full_text = cleaned
        result.total_chars = len(cleaned)

        # Split by page markers if LlamaParse includes them, otherwise treat as one page
        # LlamaParse markdown doesn't always have clear page breaks
        result.pages = [PageResult(page_num=1, text=cleaned, char_count=len(cleaned))]
        result.page_count = 1

        # Try to estimate page count from content markers
        page_markers = cleaned.count("---") + 1
        if page_markers > 1:
            result.page_count = page_markers

        return result

    except httpx.TimeoutException:
        logger.warning("LlamaParse request timed out")
        return result
    except Exception as e:
        logger.warning("LlamaParse extraction failed: %s", e)
        return result


def _poll_for_result(client: httpx.Client, api_key: str, job_id: str) -> str | None:
    """Poll LlamaParse for job completion. Returns markdown text or None."""
    headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(POLL_MAX_ATTEMPTS):
        status_resp = client.get(
            f"{LLAMA_API_BASE}/job/{job_id}",
            headers=headers,
        )

        if status_resp.status_code != 200:
            logger.warning("LlamaParse status check failed (%d)", status_resp.status_code)
            return None

        status = status_resp.json()

        if status.get("status") == "SUCCESS":
            # Fetch the markdown result
            result_resp = client.get(
                f"{LLAMA_API_BASE}/job/{job_id}/result/markdown",
                headers=headers,
            )
            if result_resp.status_code != 200:
                logger.warning("LlamaParse result fetch failed (%d)", result_resp.status_code)
                return None

            raw = result_resp.text

            # Handle various response formats (JSON or plain text)
            if raw.startswith("{") or raw.startswith("["):
                try:
                    import json
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        return parsed.get("markdown") or parsed.get("md") or parsed.get("text") or raw
                    if isinstance(parsed, list):
                        combined = "\n\n".join(
                            p.get("markdown", p.get("md", p.get("text", str(p)))) if isinstance(p, dict) else str(p)
                            for p in parsed
                        )
                        return combined if len(combined) > 10 else raw
                except (json.JSONDecodeError, TypeError):
                    pass

            return raw

        if status.get("status") == "ERROR":
            logger.warning("LlamaParse job failed: %s", status.get("error_message", "Unknown"))
            return None

        # Still pending — wait
        time.sleep(POLL_DELAY_SECONDS)

    logger.warning("LlamaParse job timed out after %d attempts", POLL_MAX_ATTEMPTS)
    return None
