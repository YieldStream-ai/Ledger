"""Health check endpoint."""

from __future__ import annotations

import shutil

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    extractors = {
        "pdfplumber": _check_import("pdfplumber"),
        "pymupdf": _check_import("fitz"),
        "tesseract": shutil.which("tesseract") is not None,
    }

    return {
        "status": "healthy",
        "version": "0.1.0",
        "extractors": extractors,
    }


def _check_import(module: str) -> bool:
    try:
        __import__(module)
        return True
    except ImportError:
        return False
