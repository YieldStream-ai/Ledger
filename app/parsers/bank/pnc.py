"""PNC Business bank statement parser."""

from __future__ import annotations

import re

from app.models.bank_statement import BankStatementSummary, Transaction
from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate
from app.parsers.bank.generic import GenericBankParser
from app.parsers.bank.registry import TemplateRegistry
from app.utils.currency import find_amount
from app.utils.dates import find_date_range


class PNCTemplate(BankTemplate):
    bank_name = "PNC"
    template_id = "pnc"

    _generic = GenericBankParser()

    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        score = 0.0
        text_upper = text.upper()
        text_lower = text.lower()

        if "PNC BANK" in text_upper or "PNC BUSINESS" in text_upper:
            score += 0.4
        if "pnc.com" in text_lower:
            score += 0.2
        if "Business Checking" in text and "PNC" in text_upper:
            score += 0.2
        if "Deposit and Credit Summary" in text:
            score += 0.1
        if "Withdrawal and Debit Summary" in text:
            score += 0.1

        return min(score, 1.0)

    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        summary = BankStatementSummary(bank_name="PNC", template_used="pnc")

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
            r"Total\s+(?:Deposits|Credits)[:\s]*\$?([\d,]+\.?\d*)",
            r"Deposit\s+and\s+Credit\s+Summary[:\s]*\$?([\d,]+\.?\d*)",
        ])
        summary.total_withdrawals = find_amount(text, [
            r"Total\s+(?:Withdrawals|Debits)[:\s]*\$?([\d,]+\.?\d*)",
            r"Withdrawal\s+and\s+Debit\s+Summary[:\s]*\$?([\d,]+\.?\d*)",
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


TemplateRegistry.register(PNCTemplate())
