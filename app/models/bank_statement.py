from __future__ import annotations

from pydantic import BaseModel


class Transaction(BaseModel):
    date: str
    description: str
    amount: float
    running_balance: float | None = None
    type: str  # "credit" | "debit"
    category: str = "other"  # "revenue", "transfer", "mca_payment", "tax", "fee", "other"


class BankStatementSummary(BaseModel):
    bank_name: str | None = None
    template_used: str = "generic"
    account_holder: str | None = None
    account_number_last4: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    beginning_balance: float | None = None
    ending_balance: float | None = None
    total_deposits: float | None = None
    total_withdrawals: float | None = None
    deposit_count: int | None = None
    nsf_count: int = 0
    average_daily_balance: float | None = None


class DerivedMetrics(BaseModel):
    calculated_adb: float | None = None
    negative_balance_days: int = 0
    largest_deposit: float | None = None
    largest_withdrawal: float | None = None
    revenue_deposits_total: float | None = None
    transfer_deposits_total: float | None = None
    daily_ending_balances: dict[str, float] = {}


class BankStatementData(BaseModel):
    """Full parsed bank statement — returned in ParseResponse.parsed_data."""
    bank_name: str | None = None
    template_used: str = "generic"
    account_holder: str | None = None
    account_number_last4: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    beginning_balance: float | None = None
    ending_balance: float | None = None
    total_deposits: float | None = None
    total_withdrawals: float | None = None
    deposit_count: int | None = None
    nsf_count: int = 0
    average_daily_balance: float | None = None
    transactions: list[Transaction] = []
    derived_metrics: DerivedMetrics = DerivedMetrics()
