"""Wells Fargo Business bank statement parser."""

from __future__ import annotations

import re

from app.models.bank_statement import BankStatementSummary, Transaction
from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate
from app.parsers.bank.registry import TemplateRegistry
from app.utils.currency import find_amount, parse_amount
from app.utils.dates import find_date_range, parse_date


class WellsFargoTemplate(BankTemplate):
    bank_name = "Wells Fargo"
    template_id = "wells_fargo"
    match_signal_defs = [
        ("header_text", "WELLS FARGO identifier"),
        ("domain", "wellsfargo.com domain reference"),
        ("account_type", "Business Choice Checking product name"),
        ("section_header", "Transaction history section"),
        ("section_header", "Ending day balance / Daily balance section"),
    ]

    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        score = 0.0
        text_upper = text.upper()
        text_lower = text.lower()

        if "WELLS FARGO" in text_upper:
            score += 0.4
        if "wellsfargo.com" in text_lower:
            score += 0.2
        if "Business Choice Checking" in text or "BUSINESS CHOICE" in text_upper:
            score += 0.2
        if "Transaction history" in text:
            score += 0.1
        if "Ending day balance" in text or "Daily balance" in text:
            score += 0.1

        return min(score, 1.0)

    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        summary = BankStatementSummary(
            bank_name="Wells Fargo",
            template_used="wells_fargo",
        )

        period_start, period_end = find_date_range(text)
        summary.period_start = period_start
        summary.period_end = period_end

        summary.beginning_balance = find_amount(text, [
            r"Beginning\s+balance\s+(?:on\s+\S+\s+)?\$?([\d,]+\.?\d*)",
        ])

        summary.ending_balance = find_amount(text, [
            r"Ending\s+balance\s+(?:on\s+\S+\s+)?\$?([\d,]+\.?\d*)",
        ])

        summary.total_deposits = find_amount(text, [
            r"Deposits/?[Cc]redits[:\s]+[\d+\s]*\$?([\d,]+\.?\d*)",
            r"Total\s+deposits[:\s]*\$?([\d,]+\.?\d*)",
        ])

        summary.total_withdrawals = find_amount(text, [
            r"Withdrawals/?[Dd]ebits[:\s]+[\d+\s]*\$?([\d,]+\.?\d*)",
            r"Total\s+withdrawals[:\s]*\$?([\d,]+\.?\d*)",
        ])

        summary.average_daily_balance = find_amount(text, [
            r"Average\s+ledger\s+balance[:\s]*\$?([\d,]+\.?\d*)",
            r"Average\s+balance[:\s]*\$?([\d,]+\.?\d*)",
        ])

        nsf_matches = re.findall(r"\bNSF\b|\bOverdraft\b|\bReturned\s+Item\b", text, re.IGNORECASE)
        summary.nsf_count = len(nsf_matches)

        acct_match = re.search(r"Account\s+number[:\s]*[*xX.\s]*(\d{4})", text, re.IGNORECASE)
        if acct_match:
            summary.account_number_last4 = acct_match.group(1)

        return summary

    def extract_transactions(self, text: str, tables: list[ExtractedTable]) -> list[Transaction]:
        transactions: list[Transaction] = []

        for table in tables:
            txns = self._parse_wf_table(table)
            if txns:
                transactions.extend(txns)

        if transactions:
            return transactions

        # Wells Fargo text format: "MM/DD  Description  Amount"
        pattern = re.compile(
            r"(\d{1,2}/\d{1,2})\s+"
            r"(.+?)\s+"
            r"(-?\$?[\d,]+\.\d{2})\s*$",
            re.MULTILINE,
        )

        for match in pattern.finditer(text):
            date_str = parse_date(match.group(1))
            desc = match.group(2).strip()
            amount = parse_amount(match.group(3))

            if amount is None:
                continue

            txn_type = "credit" if amount >= 0 else "debit"
            transactions.append(Transaction(
                date=date_str or match.group(1),
                description=desc,
                amount=round(abs(amount), 2),
                type=txn_type,
            ))

        return transactions

    def _parse_wf_table(self, table: ExtractedTable) -> list[Transaction]:
        txns: list[Transaction] = []
        headers_lower = [h.lower() for h in table.headers]

        date_idx = next((i for i, h in enumerate(headers_lower) if "date" in h), None)
        desc_idx = next((i for i, h in enumerate(headers_lower) if "description" in h or "detail" in h), None)
        amount_idx = next((i for i, h in enumerate(headers_lower) if "amount" in h), None)
        credit_idx = next((i for i, h in enumerate(headers_lower) if "addition" in h or "credit" in h or "deposit" in h), None)
        debit_idx = next((i for i, h in enumerate(headers_lower) if "subtraction" in h or "debit" in h or "withdrawal" in h), None)
        balance_idx = next((i for i, h in enumerate(headers_lower) if "balance" in h), None)

        if date_idx is None:
            return []

        for row in table.rows:
            date_str = parse_date(row[date_idx]) if date_idx < len(row) else None
            desc = row[desc_idx].strip() if desc_idx is not None and desc_idx < len(row) else ""
            if not date_str and not desc:
                continue

            amount = 0.0
            txn_type = "debit"

            if credit_idx is not None and debit_idx is not None:
                credit_val = parse_amount(row[credit_idx]) if credit_idx < len(row) else None
                debit_val = parse_amount(row[debit_idx]) if debit_idx < len(row) else None
                if credit_val and credit_val > 0:
                    amount = credit_val
                    txn_type = "credit"
                elif debit_val:
                    amount = abs(debit_val)
                    txn_type = "debit"
            elif amount_idx is not None and amount_idx < len(row):
                raw = parse_amount(row[amount_idx])
                if raw is not None:
                    txn_type = "credit" if raw >= 0 else "debit"
                    amount = abs(raw)

            balance = parse_amount(row[balance_idx]) if balance_idx is not None and balance_idx < len(row) else None

            if amount == 0.0:
                continue

            txns.append(Transaction(
                date=date_str or "",
                description=desc,
                amount=round(amount, 2),
                running_balance=round(balance, 2) if balance is not None else None,
                type=txn_type,
            ))

        return txns


TemplateRegistry.register(WellsFargoTemplate())
