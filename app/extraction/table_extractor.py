"""Table-specific extraction using pdfplumber's table detection."""

from __future__ import annotations

import logging
from pathlib import Path

import pdfplumber

from app.models.responses import ExtractedTable

logger = logging.getLogger(__name__)


def extract_tables(file_path: str | Path) -> list[ExtractedTable]:
    """Extract all tables from a PDF using pdfplumber's table detection."""
    tables: list[ExtractedTable] = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_tables = page.extract_tables() or []

                for raw_table in page_tables:
                    if not raw_table or len(raw_table) < 2:
                        continue

                    # First row as headers, rest as data
                    headers = [str(cell or "").strip() for cell in raw_table[0]]
                    rows = []
                    for row in raw_table[1:]:
                        cleaned = [str(cell or "").strip() for cell in row]
                        # Skip rows that are all empty
                        if any(c for c in cleaned):
                            rows.append(cleaned)

                    if rows:
                        tables.append(ExtractedTable(
                            page=i + 1,
                            headers=headers,
                            rows=rows,
                        ))

    except Exception as e:
        logger.warning("Table extraction failed: %s", e)

    return tables
