from __future__ import annotations

from fastapi import APIRouter

from app.parsers.bank.registry import TemplateRegistry

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/bank")
async def list_bank_templates():
    """Return all registered bank templates with match counts (last 30 days)."""
    return TemplateRegistry.get_template_details()
