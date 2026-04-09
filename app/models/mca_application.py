from __future__ import annotations

from pydantic import BaseModel


class OwnerInfo(BaseModel):
    name: str | None = None
    ownership_percent: float | None = None


class MCAApplication(BaseModel):
    business_legal_name: str | None = None
    dba_name: str | None = None
    owners: list[OwnerInfo] = []
    business_address: str | None = None
    phone: str | None = None
    email: str | None = None
    ein: str | None = None
    date_of_incorporation: str | None = None
    business_type: str | None = None  # LLC, Corp, Sole Prop, etc.
    monthly_revenue: float | None = None
    annual_revenue: float | None = None
    requested_funding_amount: float | None = None
    current_mca_positions: list[str] = []
    landlord_name: str | None = None
    rent_amount: float | None = None
