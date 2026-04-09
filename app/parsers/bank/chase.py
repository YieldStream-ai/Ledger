"""Chase bank statement parser — handles both personal and business formats."""

from __future__ import annotations

import re

from app.models.bank_statement import BankStatementSummary, Transaction
from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate
from app.parsers.bank.registry import TemplateRegistry
from app.utils.currency import find_amount, parse_amount
from app.utils.dates import find_date_range, parse_date


class ChaseTemplate(BankTemplate):
    bank_name = "Chase"
    template_id = "chase"

    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        score = 0.0
        text_upper = text.upper()
        text_lower = text.lower()

        if "JPMORGAN CHASE BANK" in text_upper:
            score += 0.4
        if "chase.com" in text_lower:
            score += 0.2
        # Business signals
        if "Deposits and Additions" in text:
            score += 0.15
        if "Checks and Other Withdrawals" in text:
            score += 0.05
        # Personal signals
        if "CHECKING SUMMARY" in text_upper:
            score += 0.15
        if "ATM & Debit Card Withdrawals" in text:
            score += 0.05
        if "CHASE TOTAL CHECKING" in text_upper or "CHASE BUSINESS CHECKING" in text_upper:
            score += 0.1

        return min(score, 1.0)

    def _is_personal(self, text: str) -> bool:
        """Detect if this is a Chase personal (vs business) statement."""
        return "CHECKING SUMMARY" in text.upper() or "*start*summary" in text

    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        summary = BankStatementSummary(
            bank_name="Chase",
            template_used="chase",
        )

        # Statement period — personal format: "February 19, 2026throughMarch 17, 2026"
        # (no spaces around "through")
        period_match = re.search(
            r"([A-Z][a-z]+ \d{1,2},?\s*\d{4})\s*through\s*([A-Z][a-z]+ \d{1,2},?\s*\d{4})",
            text,
        )
        if period_match:
            summary.period_start = parse_date(period_match.group(1))
            summary.period_end = parse_date(period_match.group(2))
        else:
            # Business format: "Statement Period: 03/01/2026 - 03/31/2026"
            period_start, period_end = find_date_range(text)
            summary.period_start = period_start
            summary.period_end = period_end

        # Beginning balance
        summary.beginning_balance = find_amount(text, [
            r"Beginning\s+Balance\s+\$?([\d,]+\.?\d*)",
        ])

        # Ending balance
        summary.ending_balance = find_amount(text, [
            r"Ending\s+Balance\s+\$?([\d,]+\.?\d*)",
        ])

        if self._is_personal(text):
            # Personal format: summary has signed amounts
            # "Deposits and Additions 681.00"
            # "ATM & Debit Card Withdrawals -1,018.55"
            # "Electronic Withdrawals -78.98"
            # "Fees -0.21"
            summary.total_deposits = find_amount(text, [
                r"Deposits\s+and\s+Additions\s+\$?([\d,]+\.?\d*)",
            ])

            # Sum all withdrawal categories for total
            atm_wd = find_amount(text, [r"ATM\s*&\s*Debit\s+Card\s+Withdrawals\s+-?\$?([\d,]+\.?\d*)"])
            elec_wd = find_amount(text, [r"Electronic\s+Withdrawals\s+-?\$?([\d,]+\.?\d*)"])
            fees = find_amount(text, [r"Fees\s+-?\$?([\d,]+\.?\d*)"])
            checks = find_amount(text, [r"Checks\s+(?:Paid|Written)\s+-?\$?([\d,]+\.?\d*)"])

            parts = [v for v in [atm_wd, elec_wd, fees, checks] if v]
            if parts:
                summary.total_withdrawals = round(sum(parts), 2)
        else:
            # Business format: "Deposits and Additions  15  $87,654.32"
            summary.total_deposits = find_amount(text, [
                r"Deposits\s+and\s+Additions\s+\d*\s*\$?([\d,]+\.?\d*)",
                r"Total\s+Deposits\s+and\s+Additions[:\s]*\$?([\d,]+\.?\d*)",
            ])

            summary.total_withdrawals = find_amount(text, [
                r"(?:Checks\s+and\s+Other\s+)?Withdrawals[:\s]+\d*\s*\$?([\d,]+\.?\d*)",
                r"Total\s+Withdrawals[:\s]*\$?([\d,]+\.?\d*)",
                r"Electronic\s+Withdrawals\s+\d*\s*\$?([\d,]+\.?\d*)",
            ])

        # Deposit count — business: "Deposits and Additions  15"
        dep_count_match = re.search(r"Deposits\s+and\s+Additions\s+(\d+)", text)
        if dep_count_match:
            val = int(dep_count_match.group(1))
            # Sanity check: if the number looks like a dollar amount (>= 100), it's not a count
            if val < 500:
                summary.deposit_count = val

        summary.average_daily_balance = find_amount(text, [
            r"Average\s+(?:Ledger\s+)?Balance[:\s]*\$?([\d,]+\.?\d*)",
        ])

        # NSF
        nsf_matches = re.findall(r"\bNSF\b|\bInsufficient\s+Funds\b|\bReturned\s+Item\b", text, re.IGNORECASE)
        summary.nsf_count = len(nsf_matches)

        # Account holder — look for name pattern
        # Personal: "JOSHUA DINH\n6344 OSLER ST" (name above address)
        # Business: first line of the statement body
        name_match = re.search(
            r"(?:^|\n)([A-Z][A-Z]+ [A-Z][A-Z ]+?)\s*\n\s*\d+\s+[A-Z]",
            text,
        )
        if name_match:
            candidate = name_match.group(1).strip()
            # Filter out false positives
            skip = {"CUSTOMER SERVICE INFORMATION", "CHECKING SUMMARY", "TRANSACTION DETAIL"}
            if candidate not in skip and len(candidate) > 4:
                summary.account_holder = candidate

        # Account number — Chase often redacts on personal, shows on business
        acct_match = re.search(r"Account\s+(?:Number|#)[:\s]*[*xX.]*(\d{4})", text, re.IGNORECASE)
        if acct_match:
            last4 = acct_match.group(1)
            if last4 != "0000":  # Skip if fully redacted
                summary.account_number_last4 = last4

        return summary

    def extract_transactions(self, text: str, tables: list[ExtractedTable]) -> list[Transaction]:
        transactions: list[Transaction] = []

        # Try tables first
        for table in tables:
            txns = self._parse_chase_table(table)
            if txns:
                transactions.extend(txns)

        if transactions:
            return transactions

        # Check if this is personal format (unified transaction list with signed amounts)
        if self._is_personal(text):
            return self._parse_personal_transactions(text)

        # Business format: separate sections for deposits and withdrawals
        deposits_section = self._extract_section(text, "Deposits and Additions", [
            "Checks and Other Withdrawals", "Electronic Withdrawals",
            "ATM & Debit Card", "Fees", "Daily Ending Balance",
        ])
        if deposits_section:
            transactions.extend(self._parse_text_transactions(deposits_section, "credit"))

        for section_name in ["Checks and Other Withdrawals", "Electronic Withdrawals"]:
            section = self._extract_section(text, section_name, [
                "Deposits and Additions", "ATM & Debit Card",
                "Fees", "Daily Ending Balance", "Service Charge Summary",
            ])
            if section:
                transactions.extend(self._parse_text_transactions(section, "debit"))

        return transactions

    def _parse_personal_transactions(self, text: str) -> list[Transaction]:
        """Parse Chase personal statement transactions.

        Format: MM/DD Description -Amount Balance
        Amounts are signed: negative for debits, positive for credits.
        Multi-line descriptions have continuation lines (no date prefix).
        """
        txns: list[Transaction] = []

        # Match: "02/19 Card Purchase With Pin 02/18 Aldi 79102 San Diego CA Card 6082 -8.85 494.75"
        # The amount and balance are at the end of the line
        pattern = re.compile(
            r"(\d{2}/\d{2})\s+"                   # date MM/DD
            r"(.+?)\s+"                             # description
            r"(-?[\d,]+\.\d{2})\s+"                # amount (signed)
            r"([\d,]+\.\d{2})\s*$",                # balance
            re.MULTILINE,
        )

        for match in pattern.finditer(text):
            date_raw = match.group(1)
            description = match.group(2).strip()
            amount_raw = match.group(3)
            balance_raw = match.group(4)

            # Skip beginning/ending balance lines
            if "Beginning Balance" in description or "Ending Balance" in description:
                continue

            amount = parse_amount(amount_raw)
            if amount is None:
                continue

            balance = parse_amount(balance_raw)

            # Resolve full date
            date_str = self._resolve_date(date_raw, text)

            txn_type = "credit" if amount >= 0 else "debit"

            txns.append(Transaction(
                date=date_str or date_raw,
                description=description,
                amount=round(abs(amount), 2),
                running_balance=round(balance, 2) if balance is not None else None,
                type=txn_type,
            ))

        return txns

    def _resolve_date(self, mm_dd: str, text: str) -> str | None:
        """Resolve MM/DD to full YYYY-MM-DD using statement period context."""
        # Try "through" format first (personal)
        period_match = re.search(
            r"([A-Z][a-z]+ \d{1,2},?\s*(\d{4}))\s*through\s*([A-Z][a-z]+ \d{1,2},?\s*(\d{4}))",
            text,
        )
        if period_match:
            start_year = period_match.group(2)
            end_year = period_match.group(4)
        else:
            # Try numeric date range
            yr_match = re.search(r"(\d{1,2}/\d{1,2}/(\d{4}))\s*-\s*(\d{1,2}/\d{1,2}/(\d{4}))", text)
            if yr_match:
                start_year = yr_match.group(2)
                end_year = yr_match.group(4)
            else:
                return parse_date(mm_dd)

        month = int(mm_dd.split("/")[0])
        day = mm_dd.split("/")[1]

        # If statement spans year boundary, figure out which year this date is in
        start_month_match = re.search(r"([A-Z][a-z]+) \d{1,2}", text)
        if start_month_match:
            # Rough heuristic: months in start year's range use start year
            if start_year != end_year:
                # If month is >= start month, use start year; else end year
                start_period = re.search(r"(\d{1,2})/\d{1,2}", text)
                start_m = int(start_period.group(1)) if start_period else 1
                year = start_year if month >= start_m else end_year
            else:
                year = start_year
        else:
            year = end_year

        return parse_date(f"{mm_dd}/{year}")

    def _parse_chase_table(self, table: ExtractedTable) -> list[Transaction]:
        """Parse a Chase-formatted transaction table."""
        txns: list[Transaction] = []
        headers_lower = [h.lower() for h in table.headers]

        date_idx = None
        desc_idx = None
        amount_idx = None
        balance_idx = None

        for i, h in enumerate(headers_lower):
            if "date" in h:
                date_idx = i
            elif "description" in h or "detail" in h:
                desc_idx = i
            elif "amount" in h:
                amount_idx = i
            elif "balance" in h:
                balance_idx = i

        if date_idx is None or desc_idx is None:
            return []

        for row in table.rows:
            if len(row) <= max(i for i in [date_idx, desc_idx, amount_idx or 0, balance_idx or 0] if i is not None):
                continue

            date_str = parse_date(row[date_idx])
            desc = row[desc_idx].strip()

            if not date_str and not desc:
                continue

            amount = parse_amount(row[amount_idx]) if amount_idx is not None and amount_idx < len(row) else None
            balance = parse_amount(row[balance_idx]) if balance_idx is not None and balance_idx < len(row) else None

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

    def _extract_section(self, text: str, start_header: str, end_headers: list[str]) -> str:
        """Extract a section of text between headers.

        Finds the header that starts its own line (section header),
        not one embedded in a summary line.
        """
        pattern = re.compile(re.escape(start_header) + r"\s*\n", re.MULTILINE)
        start_match = pattern.search(text)
        if not start_match:
            start_match = re.search(re.escape(start_header), text)
            if not start_match:
                return ""

        start_pos = start_match.end()
        end_pos = len(text)

        for end_header in end_headers:
            end_match = re.search(re.escape(end_header), text[start_pos:])
            if end_match:
                candidate = start_pos + end_match.start()
                if candidate < end_pos:
                    end_pos = candidate

        return text[start_pos:end_pos]

    def _parse_text_transactions(self, section: str, txn_type: str) -> list[Transaction]:
        """Parse transactions from a business statement text section."""
        txns: list[Transaction] = []

        pattern = re.compile(
            r"(\d{1,2}/\d{1,2})\s+"          # date (MM/DD)
            r"(.+?)\s{2,}"                     # description (followed by 2+ spaces)
            r"(-?\$?[\d,]+\.\d{2})\s*"        # amount
            r"(-?\$?[\d,]+\.\d{2})?\s*$",     # optional balance
            re.MULTILINE,
        )

        for match in pattern.finditer(section):
            date_str = parse_date(match.group(1))
            desc = match.group(2).strip()
            amount = parse_amount(match.group(3))
            balance = parse_amount(match.group(4)) if match.group(4) else None

            if amount is None:
                continue

            txns.append(Transaction(
                date=date_str or match.group(1),
                description=desc,
                amount=round(abs(amount), 2),
                running_balance=round(balance, 2) if balance is not None else None,
                type=txn_type,
            ))

        return txns


TemplateRegistry.register(ChaseTemplate())
