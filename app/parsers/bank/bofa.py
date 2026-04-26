"""Bank of America Business bank statement parser."""

from __future__ import annotations

import re

from app.models.bank_statement import BankStatementSummary, Transaction
from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate
from app.parsers.bank.registry import TemplateRegistry
from app.utils.currency import find_amount, parse_amount
from app.utils.dates import find_date_range, parse_date


class BofATemplate(BankTemplate):
    bank_name = "Bank of America"
    template_id = "bofa"
    match_signal_defs = [
        ("header_text", "BANK OF AMERICA identifier"),
        ("domain", "bankofamerica.com / bofa.com reference"),
        ("account_type", "Business Advantage product name"),
        ("section_header", "Deposits and Other Credits section"),
        ("section_header", "Checks and Substitute Checks section"),
    ]

    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        score = 0.0
        text_upper = text.upper()
        text_lower = text.lower()

        if "BANK OF AMERICA" in text_upper:
            score += 0.4
        if "bankofamerica.com" in text_lower or "bofa.com" in text_lower:
            score += 0.2
        if "Business Advantage" in text or "BUSINESS ADVANTAGE" in text_upper:
            score += 0.2
        if "Deposits and Other Credits" in text:
            score += 0.1
        if "Checks and Substitute Checks" in text:
            score += 0.1

        return min(score, 1.0)

    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        summary = BankStatementSummary(
            bank_name="Bank of America",
            template_used="bofa",
        )

        period_start, period_end = find_date_range(text)
        summary.period_start = period_start
        summary.period_end = period_end

        summary.beginning_balance = find_amount(text, [
            r"Beginning\s+[Bb]alance\s+(?:on\s+\S+\s+)?\$?([\d,]+\.?\d*)",
            r"Previous\s+[Bb]alance\s+\$?([\d,]+\.?\d*)",
        ])

        summary.ending_balance = find_amount(text, [
            r"Ending\s+[Bb]alance\s+(?:on\s+\S+\s+)?\$?([\d,]+\.?\d*)",
            r"New\s+[Bb]alance\s+\$?([\d,]+\.?\d*)",
        ])

        summary.total_deposits = find_amount(text, [
            r"Deposits\s+and\s+[Oo]ther\s+[Cc]redits\s+\$?([\d,]+\.?\d*)",
            r"Total\s+[Dd]eposits[:\s]*\$?([\d,]+\.?\d*)",
        ])

        summary.total_withdrawals = find_amount(text, [
            r"Checks\s+and\s+[Ss]ubstitute\s+[Cc]hecks\s+\$?([\d,]+\.?\d*)",
            r"Total\s+[Ww]ithdrawals[:\s]*\$?([\d,]+\.?\d*)",
            r"(?:ATM|Electronic)\s+[Ww]ithdrawals[:\s]*\$?([\d,]+\.?\d*)",
        ])

        summary.average_daily_balance = find_amount(text, [
            r"Average\s+[Ll]edger\s+[Bb]alance[:\s]*\$?([\d,]+\.?\d*)",
            r"Average\s+[Bb]alance[:\s]*\$?([\d,]+\.?\d*)",
        ])

        nsf_matches = re.findall(r"\bNSF\b|\bReturned\s+Item\b|\bOverdraft\b", text, re.IGNORECASE)
        summary.nsf_count = len(nsf_matches)

        acct_match = re.search(r"Account\s*#?[:\s]*[*xX.\s]*(\d{4})", text, re.IGNORECASE)
        if acct_match:
            summary.account_number_last4 = acct_match.group(1)

        return summary

    def extract_transactions(self, text: str, tables: list[ExtractedTable]) -> list[Transaction]:
        transactions: list[Transaction] = []

        # Table-based extraction
        for table in tables:
            txns = self._parse_bofa_table(table)
            if txns:
                transactions.extend(txns)

        if transactions:
            return transactions

        # Text fallback — BofA format: "MM/DD/YY  Description  Amount"
        pattern = re.compile(
            r"(\d{1,2}/\d{1,2}/?\d{0,4})\s+"
            r"(.+?)\s+"
            r"(-?\$?[\d,]+\.\d{2})\s*"
            r"(\$?[\d,]+\.\d{2})?\s*$",
            re.MULTILINE,
        )

        for match in pattern.finditer(text):
            date_str = parse_date(match.group(1))
            desc = match.group(2).strip()
            amount = parse_amount(match.group(3))
            balance = parse_amount(match.group(4)) if match.group(4) else None

            if amount is None:
                continue

            txn_type = "credit" if amount >= 0 else "debit"
            transactions.append(Transaction(
                date=date_str or match.group(1),
                description=desc,
                amount=round(abs(amount), 2),
                running_balance=round(balance, 2) if balance is not None else None,
                type=txn_type,
            ))

        return transactions

    def _parse_bofa_table(self, table: ExtractedTable) -> list[Transaction]:
        txns: list[Transaction] = []
        headers_lower = [h.lower() for h in table.headers]

        date_idx = next((i for i, h in enumerate(headers_lower) if "date" in h), None)
        desc_idx = next((i for i, h in enumerate(headers_lower) if "description" in h or "detail" in h), None)
        amount_idx = next((i for i, h in enumerate(headers_lower) if "amount" in h), None)
        balance_idx = next((i for i, h in enumerate(headers_lower) if "balance" in h), None)

        if date_idx is None or desc_idx is None:
            return []

        for row in table.rows:
            date_str = parse_date(row[date_idx]) if date_idx < len(row) else None
            desc = row[desc_idx].strip() if desc_idx < len(row) else ""
            if not date_str and not desc:
                continue

            amount = parse_amount(row[amount_idx]) if amount_idx and amount_idx < len(row) else None
            balance = parse_amount(row[balance_idx]) if balance_idx and balance_idx < len(row) else None

            if amount is None:
                continue

            txn_type = "credit" if amount >= 0 else "debit"
            txns.append(Transaction(
                date=date_str or "",
                description=desc,
                amount=round(abs(amount), 2),
                running_balance=round(balance, 2) if balance is not None else None,
                type=txn_type,
            ))

        return txns


TemplateRegistry.register(BofATemplate())
