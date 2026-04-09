from __future__ import annotations

from pydantic import BaseModel


class BusinessTaxReturn(BaseModel):
    filing_type: str | None = None  # "1120", "1120S", "1065", "schedule_c"
    business_name: str | None = None
    ein: str | None = None
    tax_year: str | None = None
    gross_receipts: float | None = None
    net_income: float | None = None
    total_assets: float | None = None


class PersonalTaxReturn(BaseModel):
    tax_year: str | None = None
    name: str | None = None
    ssn_last4: str | None = None
    filing_status: str | None = None
    adjusted_gross_income: float | None = None
    schedule_c_income: float | None = None
