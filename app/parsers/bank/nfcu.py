"""Navy Federal Credit Union (NFCU) bank statement parser."""

from __future__ import annotations

import re

from app.models.bank_statement import BankStatementSummary, Transaction
from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate
from app.parsers.bank.registry import TemplateRegistry
from app.utils.currency import parse_amount
from app.utils.dates import parse_date


class NFCUTemplate(BankTemplate):
    bank_name = "Navy Federal Credit Union"
    template_id = "nfcu"

    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        score = 0.0
        text_upper = text.upper()
        text_lower = text.lower()

        if "NAVY FEDERAL" in text_upper:
            score += 0.4
        if "navyfederal.org" in text_lower:
            score += 0.2
        if "e-Checking" in text:
            score += 0.2
        if "NCUA" in text_upper or "Insured by NCUA" in text:
            score += 0.1
        if "Access No." in text:
            score += 0.1

        return min(score, 1.0)

    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        summary = BankStatementSummary(
            bank_name="Navy Federal Credit Union",
            template_used="nfcu",
        )

        # Statement period: "11/25/25 - 12/24/25" (short year format)
        period_match = re.search(
            r"Statement\s+Period\s*\n\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*-\s*(\d{1,2}/\d{1,2}/\d{2,4})",
            text,
        )
        if period_match:
            summary.period_start = parse_date(period_match.group(1))
            summary.period_end = parse_date(period_match.group(2))

        # Account holder: "For JOSHUA H DINH" or "JOSHUA H DINH" near top
        name_match = re.search(r"(?:For\s+)?([A-Z][A-Z\s.]+(?:JR|SR|II|III)?)\s*\n", text)
        if name_match:
            name = name_match.group(1).strip()
            # Filter out headers/labels that look like names
            if name not in ("Statement Period", "Statement of Account", "Page") and len(name) > 3:
                summary.account_holder = name

        # Account number — "e-Checking\n7020341736" or "e-Checking - 7020341736"
        acct_match = re.search(r"e-Checking\s*[-\n]\s*(\d{10})", text)
        if acct_match:
            summary.account_number_last4 = acct_match.group(1)[-4:]

        # Summary table: "e-Checking"
        # Format: "e-Checking\n7020341736 $1,636.78 $5,232.90 $5,209.27 $1,660.41 $0.25"
        # Columns: Previous Balance | Deposits/Credits | Withdrawals/Debits | Ending Balance | YTD Dividends
        summary_match = re.search(
            r"e-Checking\s*\n\s*\d{10}\s+"
            r"\$?([\d,]+\.?\d*)\s+"   # Previous Balance
            r"\$?([\d,]+\.?\d*)\s+"   # Deposits/Credits
            r"\$?([\d,]+\.?\d*)\s+"   # Withdrawals/Debits
            r"\$?([\d,]+\.?\d*)",     # Ending Balance
            text,
        )
        if summary_match:
            summary.beginning_balance = parse_amount(summary_match.group(1))
            summary.total_deposits = parse_amount(summary_match.group(2))
            summary.total_withdrawals = parse_amount(summary_match.group(3))
            summary.ending_balance = parse_amount(summary_match.group(4))

        # NSF count
        nsf_matches = re.findall(
            r"\bNSF\b|\bInsufficient\s+Funds\b|\bReturned\s+Item\b",
            text, re.IGNORECASE,
        )
        summary.nsf_count = len(nsf_matches)

        # Deposit count from transactions (computed later, but try from text)
        deposit_matches = re.findall(r"Deposit\s+-\s+ACH", text, re.IGNORECASE)
        if deposit_matches:
            summary.deposit_count = len(deposit_matches)

        return summary

    def extract_transactions(self, text: str, tables: list[ExtractedTable]) -> list[Transaction]:
        """Parse NFCU transactions from text.

        NFCU format per line:
          MM-DD Description Amount Balance
          - Credits: "1,082.62  2,574.53" (no sign)
          - Debits: "0.01-  1,636.77" (trailing minus)
          - Beginning/Ending balance lines have no amount, just balance
        """
        transactions: list[Transaction] = []

        # Find all checking transaction sections
        # Match lines in "e-Checking" sections
        # Pattern: date (MM-DD), description, amount with optional trailing minus, balance
        pattern = re.compile(
            r"(\d{2}-\d{2})\s+"                    # date: MM-DD
            r"(.+?)\s+"                              # description
            r"([\d,]+\.\d{2}-?)\s+"                 # amount (trailing - for debit)
            r"([\d,]+\.\d{2})\s*$",                 # balance
            re.MULTILINE,
        )

        for match in pattern.finditer(text):
            date_raw = match.group(1)
            description = match.group(2).strip()
            amount_raw = match.group(3).strip()
            balance_raw = match.group(4).strip()

            # Skip beginning/ending balance lines
            if "Beginning Balance" in description or "Ending Balance" in description:
                continue

            # Parse amount — trailing minus means debit
            is_debit = amount_raw.endswith("-")
            amount_clean = amount_raw.rstrip("-")
            amount = parse_amount(amount_clean)
            if amount is None:
                continue

            balance = parse_amount(balance_raw)

            # Resolve full date using statement period context
            date_str = self._resolve_date(date_raw, text)

            txn_type = "debit" if is_debit else "credit"

            transactions.append(Transaction(
                date=date_str or date_raw,
                description=description,
                amount=round(amount, 2),
                running_balance=round(balance, 2) if balance is not None else None,
                type=txn_type,
            ))

        return transactions

    def _resolve_date(self, mm_dd: str, text: str) -> str | None:
        """Convert MM-DD to full date using statement period year context."""
        # Extract year from statement period
        period_match = re.search(
            r"Statement\s+Period\s*\n\s*(\d{1,2}/\d{1,2}/(\d{2,4}))\s*-\s*(\d{1,2}/\d{1,2}/(\d{2,4}))",
            text,
        )
        if not period_match:
            return None

        start_year = period_match.group(2)
        end_year = period_match.group(4)

        # Normalize to 4-digit year
        if len(start_year) == 2:
            start_year = "20" + start_year
        if len(end_year) == 2:
            end_year = "20" + end_year

        month, day = mm_dd.split("-")
        month_int = int(month)

        # If the statement spans a year boundary (e.g., 11/25/25 - 01/24/26),
        # months >= start month use start year, others use end year
        start_month_match = re.search(r"(\d{1,2})/\d{1,2}/\d{2,4}\s*-", text)
        if start_month_match:
            start_month = int(start_month_match.group(1))
            if month_int >= start_month:
                year = start_year
            else:
                year = end_year
        else:
            year = end_year

        return parse_date(f"{month}/{day}/{year}")


TemplateRegistry.register(NFCUTemplate())
