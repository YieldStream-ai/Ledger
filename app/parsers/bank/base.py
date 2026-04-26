"""Abstract base class for bank-specific statement parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime

from app.models.bank_statement import (
    BankStatementSummary,
    DerivedMetrics,
    Transaction,
)
from app.models.responses import ExtractedTable

# Keywords that suggest a deposit is a transfer, not revenue
_TRANSFER_KEYWORDS = [
    "transfer from", "xfer from", "internal transfer",
    "zelle", "venmo", "paypal xfer", "owner deposit", "loan deposit",
    "personal deposit",
]

# Keywords that suggest an MCA payment
_MCA_KEYWORDS = [
    "ach debit", "daily debit", "advance", "factor",
    "yellowstone", "capytal", "libertas", "clearco",
    "ondeck", "kabbage", "forward financing", "credibly",
]


class BankTemplate(ABC):
    """Abstract base for bank-specific statement parsers."""

    bank_name: str
    template_id: str

    # Subclasses should override with list of signal descriptions checked by matches().
    # Each entry is a (label, description) tuple, e.g. ("header_text", "JPMORGAN CHASE BANK").
    match_signal_defs: list[tuple[str, str]] = []

    @abstractmethod
    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        """Return confidence 0-1 that this template matches the document."""
        ...

    @abstractmethod
    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        """Extract header/summary fields from the statement."""
        ...

    @abstractmethod
    def extract_transactions(self, text: str, tables: list[ExtractedTable]) -> list[Transaction]:
        """Extract the transaction table as structured records."""
        ...

    def compute_derived_metrics(
        self,
        summary: BankStatementSummary,
        transactions: list[Transaction],
    ) -> DerivedMetrics:
        """Compute derived metrics from parsed summary and transactions.

        This default implementation works for all banks. Override only if
        a specific bank requires different calculation logic.
        """
        metrics = DerivedMetrics()

        if not transactions:
            return metrics

        # Classify transactions
        revenue_total = 0.0
        transfer_total = 0.0

        for txn in transactions:
            if txn.type == "credit":
                desc_lower = txn.description.lower()

                is_transfer = any(kw in desc_lower for kw in _TRANSFER_KEYWORDS)
                if is_transfer:
                    transfer_total += txn.amount
                    txn.category = "transfer"
                else:
                    revenue_total += txn.amount
                    txn.category = "revenue"
            elif txn.type == "debit":
                desc_lower = txn.description.lower()
                if any(kw in desc_lower for kw in _MCA_KEYWORDS):
                    txn.category = "mca_payment"
                elif "fee" in desc_lower or "service charge" in desc_lower:
                    txn.category = "fee"

        metrics.revenue_deposits_total = round(revenue_total, 2)
        metrics.transfer_deposits_total = round(transfer_total, 2)

        # Largest deposit/withdrawal
        credits = [t.amount for t in transactions if t.type == "credit"]
        debits = [abs(t.amount) for t in transactions if t.type == "debit"]

        if credits:
            metrics.largest_deposit = round(max(credits), 2)
        if debits:
            metrics.largest_withdrawal = round(max(debits), 2)

        # Daily ending balances + negative balance days
        daily_balances: dict[str, float] = {}
        negative_days = 0

        if any(t.running_balance is not None for t in transactions):
            # Use running balances from transactions
            by_date: dict[str, list[Transaction]] = defaultdict(list)
            for t in transactions:
                if t.date:
                    by_date[t.date].append(t)

            for date_str in sorted(by_date.keys()):
                day_txns = by_date[date_str]
                # Last transaction of the day has the end-of-day balance
                last = day_txns[-1]
                if last.running_balance is not None:
                    daily_balances[date_str] = last.running_balance
                    if last.running_balance < 0:
                        negative_days += 1

        metrics.daily_ending_balances = daily_balances
        metrics.negative_balance_days = negative_days

        # Calculated ADB from daily balances
        if daily_balances:
            metrics.calculated_adb = round(
                sum(daily_balances.values()) / len(daily_balances), 2
            )

        return metrics
