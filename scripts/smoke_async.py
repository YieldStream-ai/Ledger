"""End-to-end smoke test for the async job pipeline against a deployed API.

    python scripts/smoke_async.py <API_URL> <PDF_PATH> [--timeout 300]

Creates a job, uploads the PDF to S3 with the presigned POST, then polls
GET /jobs/{id} until it reaches COMPLETED or FAILED. Exits 0 on COMPLETED.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("api_url", help="API base URL, e.g. terraform output -raw api_url")
    parser.add_argument("pdf", type=Path, help="PDF to parse")
    parser.add_argument("--timeout", type=int, default=300, help="seconds to wait for a terminal status")
    parser.add_argument("--enrich", action="store_true", help="request Gemini enrichment")
    args = parser.parse_args()

    api = args.api_url.rstrip("/")
    pdf = args.pdf.read_bytes()

    with httpx.Client(timeout=60) as client:
        t0 = time.time()
        r = client.post(f"{api}/jobs", json={"file_name": args.pdf.name, "include_enrichment": args.enrich})
        r.raise_for_status()
        job = r.json()
        job_id = job["job_id"]
        print(f"created   job {job_id}")

        # S3 requires the policy fields before the file in the multipart body
        upload = job["upload"]
        r = client.post(upload["url"], data=upload["fields"], files={"file": (args.pdf.name, pdf, "application/pdf")})
        if r.status_code not in (200, 204):
            print(f"upload failed: HTTP {r.status_code}\n{r.text}", file=sys.stderr)
            return 1
        print(f"uploaded  {len(pdf):,} bytes to S3 ({time.time() - t0:.1f}s)")

        status = None
        deadline = time.time() + args.timeout
        while time.time() < deadline:
            body = client.get(f"{api}/jobs/{job_id}").json()
            if body["status"] != status:
                status = body["status"]
                print(f"{status:<9} {time.time() - t0:.1f}s")
            if status in ("COMPLETED", "FAILED"):
                break
            time.sleep(2)
        else:
            print(f"timed out after {args.timeout}s in status {status}", file=sys.stderr)
            return 1

    if status == "FAILED":
        print(f"error: {body.get('error')}", file=sys.stderr)
        return 1

    result = body["result"]
    doc = result.get("document") or {}
    print(f"result    status={result['status']} type={doc.get('type')} template={doc.get('template_used')} "
          f"worker_ms={body.get('processing_time_ms')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
