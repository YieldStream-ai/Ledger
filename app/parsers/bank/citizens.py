"""Citizens Bank Business bank statement parser."""

from __future__ import annotations

import re

from app.models.bank_statement import BankStatementSummary, Transaction
from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate
from app.parsers.bank.generic import GenericBankParser
from app.parsers.bank.registry import TemplateRegistry
from app.utils.currency import find_amount
from app.utils.dates import find_date_range


class CitizensTemplate(BankTemplate):
    bank_name = "Citizens Bank"
    template_id = "citizens"
    match_signal_defs = [
        ("header_text", "CITIZENS BANK / CITIZENS FINANCIAL identifier"),
        ("domain", "citizensbank.com domain reference"),
        ("account_type", "Business Checking with Citizens label"),
    ]

    _generic = GenericBankParser()

    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        score = 0.0
        text_upper = text.upper()
        text_lower = text.lower()

        if "CITIZENS BANK" in text_upper or "CITIZENS FINANCIAL" in text_upper:
            score += 0.4
        if "citizensbank.com" in text_lower:
            score += 0.2
        if "Business Checking" in text and "Citizens" in text:
            score += 0.2

        return min(score, 1.0)

    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        summary = BankStatementSummary(bank_name="Citizens Bank", template_used="citizens")

        period_start, period_end = find_date_range(text)
        summary.period_start = period_start
        summary.period_end = period_end

        summary.beginning_balance = find_amount(text, [
            r"Beginning\s+Balance[:\s]*\$?([\d,]+\.?\d*)",
        ])
        summary.ending_balance = find_amount(text, [
            r"Ending\s+Balance[:\s]*\$?([\d,]+\.?\d*)",
        ])
        summary.total_deposits = find_amount(text, [
            r"Total\s+(?:Deposits|Credits|Additions)[:\s]*\$?([\d,]+\.?\d*)",
        ])
        summary.total_withdrawals = find_amount(text, [
            r"Total\s+(?:Withdrawals|Debits|Subtractions)[:\s]*\$?([\d,]+\.?\d*)",
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


TemplateRegistry.register(CitizensTemplate())
