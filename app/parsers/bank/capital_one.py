"""Capital One Business bank statement parser."""

from __future__ import annotations

import re

from app.models.bank_statement import BankStatementSummary, Transaction
from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate
from app.parsers.bank.generic import GenericBankParser
from app.parsers.bank.registry import TemplateRegistry
from app.utils.currency import find_amount
from app.utils.dates import find_date_range


class CapitalOneTemplate(BankTemplate):
    bank_name = "Capital One"
    template_id = "capital_one"
    match_signal_defs = [
        ("header_text", "CAPITAL ONE identifier"),
        ("domain", "capitalone.com domain reference"),
        ("account_type", "Spark Business product name"),
        ("account_type", "Basic Checking with Capital One label"),
    ]

    _generic = GenericBankParser()

    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        score = 0.0
        text_upper = text.upper()
        text_lower = text.lower()

        if "CAPITAL ONE" in text_upper:
            score += 0.4
        if "capitalone.com" in text_lower:
            score += 0.2
        if "Spark Business" in text or "SPARK BUSINESS" in text_upper:
            score += 0.2
        if "Basic Checking" in text and "Capital One" in text:
            score += 0.1

        return min(score, 1.0)

    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        summary = BankStatementSummary(bank_name="Capital One", template_used="capital_one")

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
            r"Total\s+(?:Withdrawals|Debits|Subtractions)[:\s]*\$?([\d,]+\.?\d*)",
        ])
        summary.average_daily_balance = find_amount(text, [
            r"Average\s+(?:Daily\s+)?Balance[:\s]*\$?([\d,]+\.?\d*)",
        ])

        nsf_matches = re.findall(r"\bNSF\b|\bOverdraft\b|\bReturned\b", text, re.IGNORECASE)
        summary.nsf_count = len(nsf_matches)

        acct_match = re.search(r"Account\s*#?[:\s]*[*xX.\s]*(\d{4})", text, re.IGNORECASE)
        if acct_match:
            summary.account_number_last4 = acct_match.group(1)

        return summary

    def extract_transactions(self, text: str, tables: list[ExtractedTable]) -> list[Transaction]:
        return self._generic.extract_transactions(text, tables)


TemplateRegistry.register(CapitalOneTemplate())
