"""Tests for the document quality gate."""

from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw

from app.quality.gate import (
    DocumentQualityResult,
    QualityIssue,
    check_document_quality,
    quick_metadata_check,
)


def _make_image_bytes(width: int = 2000, height: int = 2800, fmt: str = "BMP") -> bytes:
    """Create a realistic test image with text-like content.
    Uses BMP format to avoid compression making the file too small for the 30KB threshold.
    """
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    # Simulate document content — alternating dark and light bands
    for y in range(50, height - 50, 14):
        draw.rectangle([(100, y), (width - 100, y + 6)], fill=(30, 30, 30))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _make_minimal_pdf() -> bytes:
    """Create a minimal valid PDF with text (digital PDF — should auto-pass)."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.drawString(100, 700, "This is a test bank statement with enough text to be detected as digital.")
        c.drawString(100, 680, "Account Number: ****4521")
        c.drawString(100, 660, "Period: January 1, 2026 - January 31, 2026")
        c.save()
        return buf.getvalue()
    except ImportError:
        content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 84>>stream
BT /F1 12 Tf 100 700 Td (This is a test document with enough text to classify as digital.) Tj ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000400 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
470
%%EOF"""
        return content


# ─── quick_metadata_check ─────────────────────────────────────────────────────


class TestQuickMetadataCheck:
    def test_passes_normal_file(self):
        data = _make_image_bytes()
        passed, reason = quick_metadata_check(data)
        assert passed is True
        assert reason is None

    def test_rejects_tiny_file(self):
        passed, reason = quick_metadata_check(b"tiny")
        assert passed is False
        assert "too small" in reason.lower()

    def test_rejects_oversized_file(self):
        data = b"\x00" * (51 * 1024 * 1024)  # 51 MB
        passed, reason = quick_metadata_check(data)
        assert passed is False
        assert "too large" in reason.lower()

    def test_rejects_low_res_image(self):
        # Create a small image that's still big enough in bytes (>30KB)
        img = Image.new("RGB", (200, 300), "white")
        draw = ImageDraw.Draw(img)
        # Add noise to increase file size
        for y in range(0, 300, 2):
            for x in range(0, 200, 2):
                draw.point((x, y), fill=(x % 256, y % 256, (x + y) % 256))
        buf = io.BytesIO()
        img.save(buf, format="BMP")  # BMP is uncompressed = bigger
        data = buf.getvalue()
        passed, reason = quick_metadata_check(data)
        assert passed is False
        assert "resolution" in reason.lower()


# ─── check_document_quality ───────────────────────────────────────────────────


class TestCheckDocumentQuality:
    def test_digital_pdf_auto_passes(self):
        pdf = _make_minimal_pdf()
        result = check_document_quality(pdf)
        assert result.passed is True
        assert result.overall_score == 100
        assert result.processing_allowed is True

    def test_clean_image_passes(self):
        data = _make_image_bytes()
        result = check_document_quality(data)
        assert result.processing_allowed is True

    def test_result_has_expected_fields(self):
        data = _make_image_bytes()
        result = check_document_quality(data)
        assert isinstance(result, DocumentQualityResult)
        assert isinstance(result.passed, bool)
        assert isinstance(result.overall_score, (int, float))
        assert isinstance(result.processing_allowed, bool)
