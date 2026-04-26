"""Generic bank statement parser — best-effort regex for unknown formats."""

from __future__ import annotations

import re

from app.models.bank_statement import BankStatementSummary, Transaction
from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate
from app.utils.currency import find_amount, parse_amount
from app.utils.dates import find_date_range, parse_date


class GenericBankParser(BankTemplate):
    bank_name = "Unknown"
    template_id = "generic"
    match_signal_defs = []

    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        # Generic always matches at 0.0 — only used as fallback
        return 0.0

    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        summary = BankStatementSummary(template_used="generic")

        # Statement period
        period_start, period_end = find_date_range(text)
        summary.period_start = period_start
        summary.period_end = period_end

        # Beginning balance
        summary.beginning_balance = find_amount(text, [
            r"beginning\s+balance[:\s]*\$?([\d,]+\.?\d*)",
            r"opening\s+balance[:\s]*\$?([\d,]+\.?\d*)",
            r"previous\s+balance[:\s]*\$?([\d,]+\.?\d*)",
            r"balance\s+forward[:\s]*\$?([\d,]+\.?\d*)",
        ])

        # Ending balance
        summary.ending_balance = find_amount(text, [
            r"ending\s+balance[:\s]*\$?([\d,]+\.?\d*)",
            r"closing\s+balance[:\s]*\$?([\d,]+\.?\d*)",
            r"new\s+balance[:\s]*\$?([\d,]+\.?\d*)",
        ])

        # Total deposits
        summary.total_deposits = find_amount(text, [
            r"total\s+(?:credits?|deposits?)[:\s]*\$?([\d,]+\.?\d*)",
            r"total\s+additions[:\s]*\$?([\d,]+\.?\d*)",
            r"deposits?\s+(?:&|and)\s+(?:other\s+)?credits?\s+total[:\s]*\$?([\d,]+\.?\d*)",
        ])

        # Total withdrawals
        summary.total_withdrawals = find_amount(text, [
            r"total\s+(?:debits?|withdrawals?)[:\s]*\$?([\d,]+\.?\d*)",
            r"total\s+subtractions[:\s]*\$?([\d,]+\.?\d*)",
            r"withdrawals?\s+(?:&|and)\s+(?:other\s+)?debits?\s+total[:\s]*\$?([\d,]+\.?\d*)",
            r"checks?\s+(?:&|and)\s+(?:other\s+)?debits?\s+total[:\s]*\$?([\d,]+\.?\d*)",
        ])

        # Average daily balance
        summary.average_daily_balance = find_amount(text, [
            r"average\s+daily\s+balance[:\s]*\$?([\d,]+\.?\d*)",
            r"avg\.?\s+daily\s+bal(?:ance)?[:\s]*\$?([\d,]+\.?\d*)",
            r"average\s+(?:collected\s+)?balance[:\s]*\$?([\d,]+\.?\d*)",
        ])

        # NSF count
        nsf_matches = re.findall(
            r"\bNSF\b|\bnon.sufficient\s+funds?\b|\binsufficient\s+funds?\b|\breturned\s+item\b",
            text,
            re.IGNORECASE,
        )
        summary.nsf_count = len(nsf_matches)

        # Account holder (best effort — look for common label patterns)
        acct_match = re.search(
            r"(?:account\s+(?:holder|owner|name)|primary\s+owner)[:\s]+([A-Z][A-Z\s,.]+?)(?:\n|$)",
            text,
        )
        if acct_match:
            summary.account_holder = acct_match.group(1).strip()

        # Account number last 4
        acct_num_match = re.search(
            r"(?:account\s+(?:number|#|no\.?))[:\s]*[*xX.\s]*(\d{4})\b",
            text,
            re.IGNORECASE,
        )
        if acct_num_match:
            summary.account_number_last4 = acct_num_match.group(1)

        return summary

    def extract_transactions(self, text: str, tables: list[ExtractedTable]) -> list[Transaction]:
        """Extract transactions from tables if available, else try text parsing."""
        transactions: list[Transaction] = []

        # Try table-based extraction first
        for table in tables:
            txns = self._parse_transaction_table(table)
            if txns:
                transactions.extend(txns)

        if transactions:
            return transactions

        # Fallback: line-by-line text parsing
        return self._parse_transactions_from_text(text)

    def _parse_transaction_table(self, table: ExtractedTable) -> list[Transaction]:
        """Parse transactions from an extracted table."""
        txns: list[Transaction] = []

        headers_lower = [h.lower() for h in table.headers]

        # Find relevant column indices
        date_idx = self._find_col(headers_lower, ["date", "post date", "posting date", "trans date"])
        desc_idx = self._find_col(headers_lower, ["description", "transaction", "details", "memo"])
        amount_idx = self._find_col(headers_lower, ["amount"])
        credit_idx = self._find_col(headers_lower, ["credit", "credits", "deposits", "deposit"])
        debit_idx = self._find_col(headers_lower, ["debit", "debits", "withdrawal", "withdrawals"])
        balance_idx = self._find_col(headers_lower, ["balance", "running balance"])

        if date_idx is None or desc_idx is None:
            return []

        for row in table.rows:
            if len(row) <= max(filter(None, [date_idx, desc_idx, amount_idx, credit_idx, debit_idx, balance_idx]), default=0):
                continue

            date_str = parse_date(row[date_idx]) if date_idx < len(row) else None
            description = row[desc_idx] if desc_idx < len(row) else ""

            if not date_str and not description:
                continue

            # Determine amount and type
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
                raw_amount = parse_amount(row[amount_idx])
                if raw_amount is not None:
                    if raw_amount >= 0:
                        amount = raw_amount
                        txn_type = "credit"
                    else:
                        amount = abs(raw_amount)
                        txn_type = "debit"

            # Running balance
            balance = None
            if balance_idx is not None and balance_idx < len(row):
                balance = parse_amount(row[balance_idx])

            txns.append(Transaction(
                date=date_str or "",
                description=description.strip(),
                amount=round(amount, 2),
                running_balance=round(balance, 2) if balance is not None else None,
                type=txn_type,
            ))

        return txns

    def _parse_transactions_from_text(self, text: str) -> list[Transaction]:
        """Last-resort: parse transactions from raw text lines."""
        txns: list[Transaction] = []

        # Common pattern: MM/DD  Description  Amount  Balance
        pattern = re.compile(
            r"(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+"  # date
            r"(.+?)\s+"                               # description
            r"(-?\$?[\d,]+\.\d{2})\s*"               # amount
            r"(-?\$?[\d,]+\.\d{2})?\s*$",            # optional balance
            re.MULTILINE,
        )

        for match in pattern.finditer(text):
            date_str = parse_date(match.group(1))
            description = match.group(2).strip()
            raw_amount = parse_amount(match.group(3))
            balance = parse_amount(match.group(4)) if match.group(4) else None

            if raw_amount is None:
                continue

            txn_type = "credit" if raw_amount >= 0 else "debit"

            txns.append(Transaction(
                date=date_str or match.group(1),
                description=description,
                amount=round(abs(raw_amount), 2),
                running_balance=round(balance, 2) if balance is not None else None,
                type=txn_type,
            ))

        return txns

    @staticmethod
    def _find_col(headers: list[str], candidates: list[str]) -> int | None:
        """Find the index of the first header matching any candidate."""
        for i, h in enumerate(headers):
            for c in candidates:
                if c in h:
                    return i
        return None
