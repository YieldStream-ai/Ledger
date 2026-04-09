"""Truist Business bank statement parser."""

from __future__ import annotations

import re

from app.models.bank_statement import BankStatementSummary, Transaction
from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate
from app.parsers.bank.generic import GenericBankParser
from app.parsers.bank.registry import TemplateRegistry
from app.utils.currency import find_amount
from app.utils.dates import find_date_range


class TruistTemplate(BankTemplate):
    bank_name = "Truist"
    template_id = "truist"

    _generic = GenericBankParser()

    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        score = 0.0
        text_upper = text.upper()
        text_lower = text.lower()

        if "TRUIST" in text_upper:
            score += 0.4
        if "truist.com" in text_lower:
            score += 0.2
        # Legacy BB&T / SunTrust references
        if "BB&T" in text_upper or "SUNTRUST" in text_upper:
            score += 0.3
        if "Business Checking" in text and ("Truist" in text or "BB&T" in text or "SunTrust" in text):
            score += 0.2

        return min(score, 1.0)

    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        summary = BankStatementSummary(bank_name="Truist", template_used="truist")

        period_start, period_end = find_date_range(text)
        summary.period_start = period_start
        summary.period_end = period_end

        summary.beginning_balance = find_amount(text, [
            r"Beginning\s+Balance[:\s]*\$?([\d,]+\.?\d*)",
            r"Previous\s+Balance[:\s]*\$?([\d,]+\.?\d*)",
        ])
        summary.ending_balance = find_amount(text, [
            r"Ending\s+Balance[:\s]*\$?([\d,]+\.?\d*)",
        ])
        summary.total_deposits = find_amount(text, [
            r"Total\s+(?:Deposits|Credits|Additions)[:\s]*\$?([\d,]+\.?\d*)",
        ])
        summary.total_withdrawals = find_amount(text, [
            r"Total\s+(?:Withdrawals|Debits|Subtractions|Checks)[:\s]*\$?([\d,]+\.?\d*)",
        ])
        summary.average_daily_balance = find_amount(text, [
            r"Average\s+(?:Daily\s+)?(?:Ledger\s+)?Balance[:\s]*\$?([\d,]+\.?\d*)",
        ])

        nsf_matches = re.findall(r"\bNSF\b|\bOverdraft\b|\bReturned\b", text, re.IGNORECASE)
        summary.nsf_count = len(nsf_matches)

        acct_match = re.search(r"Account\s*#?[:\s]*[*xX.\s]*(\d{4})", text, re.IGNORECASE)
        if acct_match:
            summary.account_number_last4 = acct_match.group(1)

        return summary

    def extract_transactions(self, text: str, tables: list[ExtractedTable]) -> list[Transaction]:
        return self._generic.extract_transactions(text, tables)


TemplateRegistry.register(TruistTemplate())
