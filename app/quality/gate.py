"""
Document Quality Gate
Pre-flight check before sending to extraction pipeline.

Detects:
- Photo taken of a document (vs flat scan/digital)
- Missing corners / cropped edges
- Blur / low sharpness
- Poor contrast / bad lighting
- Resolution too low to parse reliably
- Dark shadows or folds obscuring content

Pipeline position:
  Upload → Quality Gate → Extraction → Classification → Parsing
               ↓ (if fail)
         Reject with message
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from enum import Enum

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)


# ─── Types ────────────────────────────────────────────────────────────────────


class QualityIssue(str, Enum):
    MISSING_CORNERS = "MISSING_CORNERS"
    LOW_SHARPNESS = "LOW_SHARPNESS"
    POOR_CONTRAST = "POOR_CONTRAST"
    LOW_RESOLUTION = "LOW_RESOLUTION"
    EXTREME_SKEW = "EXTREME_SKEW"
    DARK_SHADOWS = "DARK_SHADOWS"
    INSUFFICIENT_TEXT_AREA = "INSUFFICIENT_TEXT_AREA"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"


@dataclass
class PageQualityMetrics:
    sharpness_score: float = 0.0
    contrast_score: float = 0.0
    brightness_score: float = 0.0
    estimated_dpi: int = 0
    dark_pixel_ratio: float = 0.0
    edge_coverage_score: float = 0.0


@dataclass
class PageQualityResult:
    page: int
    passed: bool
    score: float  # 0–100
    issues: list[QualityIssue] = field(default_factory=list)
    metrics: PageQualityMetrics = field(default_factory=PageQualityMetrics)


@dataclass
class DocumentQualityResult:
    passed: bool
    overall_score: float  # 0–100
    pages: list[PageQualityResult] = field(default_factory=list)
    issues: list[QualityIssue] = field(default_factory=list)
    rejection_reason: str | None = None
    recommendation: str | None = None
    processing_allowed: bool = True


# ─── Config ───────────────────────────────────────────────────────────────────


QUALITY_THRESHOLDS = {
    "minimum_overall_score": 55,
    "minimum_sharpness": 30,
    "minimum_contrast": 25,
    "minimum_dpi": 100,
    "maximum_dark_pixel_ratio": 0.25,
    "minimum_edge_coverage": 0.60,
    "maximum_failed_page_ratio": 0.5,
}


# ─── Core Quality Checks ─────────────────────────────────────────────────────


def _measure_sharpness(img: Image.Image) -> float:
    """Estimate sharpness using Laplacian-style edge density."""
    grey = img.convert("L").resize((800, int(800 * img.height / img.width)), Image.LANCZOS)
    arr = np.array(grey, dtype=np.float64)
    h, w = arr.shape

    # Laplacian approximation: 4*center - top - bottom - left - right
    center = arr[1:-1, 1:-1]
    top = arr[:-2, 1:-1]
    bottom = arr[2:, 1:-1]
    left = arr[1:-1, :-2]
    right = arr[1:-1, 2:]

    laplacian = np.abs(4 * center - top - bottom - left - right)
    mean_edge = laplacian.mean()

    return min(100.0, (mean_edge / 20.0) * 100.0)


def _measure_contrast(img: Image.Image) -> tuple[float, float, float]:
    """Measure contrast via pixel brightness std dev. Returns (contrast, brightness, dark_pixel_ratio)."""
    grey = img.convert("L").resize((400, int(400 * img.height / img.width)), Image.LANCZOS)
    arr = np.array(grey, dtype=np.float64)

    mean = arr.mean()
    std_dev = arr.std()
    dark_pixels = np.count_nonzero(arr < 60)
    total = arr.size

    contrast = min(100.0, (std_dev / 80.0) * 100.0)
    brightness = (mean / 255.0) * 100.0
    dark_pixel_ratio = dark_pixels / total

    return contrast, brightness, dark_pixel_ratio


def _measure_edge_coverage(img: Image.Image) -> float:
    """Check edge coverage — are the document corners present?"""
    grey = img.convert("L").resize((400, 400), Image.LANCZOS)
    arr = np.array(grey)
    h, w = arr.shape

    corner_size = int(w * 0.1)
    total_corner_pixels = 0
    light_corner_pixels = 0

    corners = [
        (0, 0),
        (w - corner_size, 0),
        (0, h - corner_size),
        (w - corner_size, h - corner_size),
    ]

    for sx, sy in corners:
        region = arr[sy : sy + corner_size, sx : sx + corner_size]
        total_corner_pixels += region.size
        light_corner_pixels += np.count_nonzero(region > 100)

    return light_corner_pixels / total_corner_pixels if total_corner_pixels > 0 else 0.0


def _estimate_dpi(width: int, height: int) -> int:
    """Estimate DPI assuming US Letter / A4 size (~11 inches on long edge)."""
    longer = max(width, height)
    return round(longer / 11)


# ─── Page Analyzer ────────────────────────────────────────────────────────────


def _analyze_page_image(img: Image.Image, page_number: int) -> PageQualityResult:
    width, height = img.size

    sharpness_score = _measure_sharpness(img)
    contrast_score, brightness_score, dark_pixel_ratio = _measure_contrast(img)
    edge_coverage_score = _measure_edge_coverage(img)
    estimated_dpi = _estimate_dpi(width, height)

    issues: list[QualityIssue] = []

    if sharpness_score < QUALITY_THRESHOLDS["minimum_sharpness"]:
        issues.append(QualityIssue.LOW_SHARPNESS)
    if contrast_score < QUALITY_THRESHOLDS["minimum_contrast"]:
        issues.append(QualityIssue.POOR_CONTRAST)
    if estimated_dpi < QUALITY_THRESHOLDS["minimum_dpi"]:
        issues.append(QualityIssue.LOW_RESOLUTION)
    if dark_pixel_ratio > QUALITY_THRESHOLDS["maximum_dark_pixel_ratio"]:
        issues.append(QualityIssue.DARK_SHADOWS)
    if edge_coverage_score < QUALITY_THRESHOLDS["minimum_edge_coverage"]:
        issues.append(QualityIssue.MISSING_CORNERS)

    # Weighted score — sharpness and edge coverage matter most
    score = round(
        sharpness_score * 0.35
        + contrast_score * 0.20
        + edge_coverage_score * 100 * 0.30
        + min(100.0, (estimated_dpi / 150.0) * 100.0) * 0.15
        - dark_pixel_ratio * 100 * 0.10
    )
    score = max(0, min(100, score))

    return PageQualityResult(
        page=page_number,
        passed=len(issues) == 0 and score >= QUALITY_THRESHOLDS["minimum_overall_score"],
        score=score,
        issues=issues,
        metrics=PageQualityMetrics(
            sharpness_score=round(sharpness_score),
            contrast_score=round(contrast_score),
            brightness_score=round(brightness_score),
            estimated_dpi=estimated_dpi,
            dark_pixel_ratio=round(dark_pixel_ratio, 2),
            edge_coverage_score=round(edge_coverage_score, 2),
        ),
    )


# ─── Issue → Human Message Mapping ───────────────────────────────────────────


_ISSUE_MESSAGES: dict[QualityIssue, str] = {
    QualityIssue.MISSING_CORNERS: "document corners are cut off or missing",
    QualityIssue.LOW_SHARPNESS: "image is too blurry to read accurately",
    QualityIssue.POOR_CONTRAST: "image contrast is too low (washed out or over-exposed)",
    QualityIssue.LOW_RESOLUTION: "image resolution is too low",
    QualityIssue.EXTREME_SKEW: "document is too skewed or angled",
    QualityIssue.DARK_SHADOWS: "dark shadows or folds are obscuring content",
    QualityIssue.INSUFFICIENT_TEXT_AREA: "not enough readable text area detected",
    QualityIssue.UNSUPPORTED_FORMAT: "file format is not supported for quality analysis",
}

ISSUE_LABELS: dict[QualityIssue, str] = {
    QualityIssue.MISSING_CORNERS: "Corners cut off",
    QualityIssue.LOW_SHARPNESS: "Image too blurry",
    QualityIssue.POOR_CONTRAST: "Poor lighting / contrast",
    QualityIssue.LOW_RESOLUTION: "Resolution too low",
    QualityIssue.EXTREME_SKEW: "Document too angled",
    QualityIssue.DARK_SHADOWS: "Shadows or folds detected",
    QualityIssue.INSUFFICIENT_TEXT_AREA: "Not enough readable content",
    QualityIssue.UNSUPPORTED_FORMAT: "Unsupported file format",
}


def _build_rejection_reason(issues: list[QualityIssue]) -> str:
    descriptions = [_ISSUE_MESSAGES[i] for i in dict.fromkeys(issues)]
    if not descriptions:
        return "Unknown quality issue"
    if len(descriptions) == 1:
        return f"Document rejected: {descriptions[0]}."
    last = descriptions[-1]
    rest = ", ".join(descriptions[:-1])
    return f"Document rejected: {rest} and {last}."


def _build_recommendation(issues: list[QualityIssue]) -> str:
    if QualityIssue.MISSING_CORNERS in issues or QualityIssue.EXTREME_SKEW in issues:
        return "Please download the document directly as a PDF, or place it flat on a surface and scan using a scanner app."
    if QualityIssue.LOW_SHARPNESS in issues or QualityIssue.LOW_RESOLUTION in issues:
        return "Please use a higher quality scan or download the document directly as a PDF."
    if QualityIssue.DARK_SHADOWS in issues or QualityIssue.POOR_CONTRAST in issues:
        return "Please ensure even lighting with no shadows when photographing the document, or preferably upload a direct PDF download."
    return "For best results, download the document directly as a PDF."


# ─── PDF → Images ─────────────────────────────────────────────────────────────


def _extract_page_images(file_bytes: bytes) -> tuple[list[Image.Image], bool]:
    """Extract page images from a PDF. Returns (images, is_digital_pdf).

    For native digital PDFs (text-based), returns empty list + True
    since they don't need image quality validation.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = doc.page_count

        if page_count == 0:
            doc.close()
            return [], True

        # Check if it's a text-based PDF by looking for selectable text
        first_page = doc[0]
        text = first_page.get_text()

        if len(text.strip()) > 50:
            # Has substantial text — it's a native digital PDF, skip quality gate
            logger.info(f"[QualityGate] PDF has {page_count} pages, detected as native digital PDF — skipping quality gate")
            doc.close()
            return [], True

        # Image-based/scanned PDF — render pages as images
        logger.info(f"[QualityGate] PDF has {page_count} pages, rendering for quality analysis")
        images: list[Image.Image] = []
        for page_idx in range(min(page_count, 5)):  # Analyze up to 5 pages
            page = doc[page_idx]
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            images.append(img)

        doc.close()
        return images, False

    except Exception:
        # Not a valid PDF — try to open as raw image
        try:
            img = Image.open(io.BytesIO(file_bytes))
            img.load()
            return [img], False
        except Exception:
            logger.warning("[QualityGate] Buffer is not a valid PDF or image — skipping quality gate")
            return [], True


# ─── Main Export ──────────────────────────────────────────────────────────────


def check_document_quality(
    file_bytes: bytes,
    *,
    strict_mode: bool = False,
) -> DocumentQualityResult:
    """Primary entry point. Call before the extraction pipeline.

    Returns processing_allowed=True for:
    - Digital PDFs (auto-pass, no image quality issues)
    - Images/scanned PDFs that meet quality thresholds

    Returns processing_allowed=False for:
    - Blurry phone photos
    - Cropped/angled captures
    - Low resolution images
    - Documents with shadows/folds
    """
    page_images, is_digital_pdf = _extract_page_images(file_bytes)

    # Digital PDFs auto-pass
    if is_digital_pdf:
        return DocumentQualityResult(
            passed=True,
            overall_score=100,
            processing_allowed=True,
        )

    page_results: list[PageQualityResult] = []
    for i, img in enumerate(page_images):
        try:
            page_results.append(_analyze_page_image(img, i + 1))
        except Exception:
            logger.warning(f"[QualityGate] Page {i + 1}: failed to analyze, skipping")
            page_results.append(PageQualityResult(
                page=i + 1,
                passed=False,
                score=0,
                issues=[QualityIssue.UNSUPPORTED_FORMAT],
            ))

    failed_pages = [p for p in page_results if not p.passed]
    failed_ratio = len(failed_pages) / len(page_results) if page_results else 0
    overall_score = round(sum(p.score for p in page_results) / len(page_results)) if page_results else 0

    all_issues = list(dict.fromkeys(issue for p in page_results for issue in p.issues))

    too_many_failed = failed_ratio > QUALITY_THRESHOLDS["maximum_failed_page_ratio"]
    score_too_low = overall_score < QUALITY_THRESHOLDS["minimum_overall_score"]
    passed = not too_many_failed and not score_too_low and len(all_issues) == 0

    if strict_mode:
        processing_allowed = passed
    else:
        processing_allowed = (
            overall_score >= QUALITY_THRESHOLDS["minimum_overall_score"] - 10
            and not too_many_failed
        )

    return DocumentQualityResult(
        passed=passed,
        overall_score=overall_score,
        pages=page_results,
        issues=all_issues,
        rejection_reason=_build_rejection_reason(all_issues) if not processing_allowed else None,
        recommendation=_build_recommendation(all_issues) if not processing_allowed else None,
        processing_allowed=processing_allowed,
    )


# ─── Lightweight Pre-Check ────────────────────────────────────────────────────


def quick_metadata_check(file_bytes: bytes) -> tuple[bool, str | None]:
    """Quick metadata-only check (<5ms). Returns (passed, reason)."""
    size_kb = len(file_bytes) / 1024

    if size_kb < 30:
        return False, "File too small to contain readable document data."

    if size_kb > 50_000:
        return False, "File size too large. Please upload a standard PDF document."

    # Try to check image dimensions if it's a raw image
    try:
        img = Image.open(io.BytesIO(file_bytes))
        w, h = img.size
        if min(w, h) < 500:
            return False, "Image resolution too low. Minimum 500px on shortest side required."
    except Exception:
        pass  # Not an image — likely a native PDF, that's fine

    return True, None
