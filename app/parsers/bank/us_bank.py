"""US Bank bank statement parser — handles business and consumer (Uni-Statement) formats."""

from __future__ import annotations

import re

from app.models.bank_statement import BankStatementSummary, DerivedMetrics, Transaction
from app.models.responses import ExtractedTable
from app.parsers.bank.base import BankTemplate
from app.parsers.bank.registry import TemplateRegistry
from app.utils.currency import find_amount, parse_amount
from app.utils.dates import parse_date


class USBankTemplate(BankTemplate):
    bank_name = "US Bank"
    template_id = "us_bank"
    _stmt_year: str = "2026"  # updated during extract_summary
    _raw_text: str = ""  # stored for compute_derived_metrics

    def matches(self, text: str, tables: list[ExtractedTable]) -> float:
        score = 0.0
        text_upper = text.upper()
        text_lower = text.lower()

        if "U.S. BANK" in text_upper or "US BANK" in text_upper:
            score += 0.4
        if "usbank.com" in text_lower:
            score += 0.2
        # Business account types
        if "Silver Business" in text or "Gold Business" in text or "Platinum Business" in text:
            score += 0.2
        # Consumer account types (Uni-Statement format)
        if "Uni-Statement" in text:
            score += 0.2
        if "STUDENT CHECKING" in text_upper or "CHECKING" in text_upper:
            score += 0.1
        if "TRANSACTION DETAIL" in text_upper:
            score += 0.1

        return min(score, 1.0)

    def extract_summary(self, text: str, tables: list[ExtractedTable]) -> BankStatementSummary:
        # Store raw text for compute_derived_metrics
        self._raw_text = text

        summary = BankStatementSummary(bank_name="US Bank", template_used="us_bank")

        # --- Statement period ---
        # US Bank Uni-Statement splits dates across lines:
        #   "Statement Period:\nFeb 19, 2026\nthrough\nMar 17, 2026"
        # Page 1 has barcode noise; subsequent pages are clean.
        # Try clean format first (pages 3+), then noisy page 1 format.
        period_match = re.search(
            r"Statement\s+Period:\s*\n"
            r"\s*([A-Z][a-z]+\s+\d{1,2},?\s*\d{4})\s*\n"
            r"\s*through\s*\n"
            r"\s*([A-Z][a-z]+\s+\d{1,2},?\s*\d{4})",
            text,
        )
        if not period_match:
            # Page 1: noise between "Statement Period:" and dates
            period_match = re.search(
                r"Statement\s+Period:\s*\n"
                r"(?:.*\n)*?"
                r".*?([A-Z][a-z]+\s+\d{1,2},?\s*\d{4})\s*\n"
                r"\s*through\s*\n"
                r"(?:.*\n)*?"
                r".*?([A-Z][a-z]+\s+\d{1,2},?\s*\d{4})",
                text,
            )
        if period_match:
            summary.period_start = parse_date(period_match.group(1))
            summary.period_end = parse_date(period_match.group(2))
            # Extract year for transaction date parsing
            year_match = re.search(r"(\d{4})", period_match.group(2))
            if year_match:
                self._stmt_year = year_match.group(1)

        # --- Balances ---
        # Business format: "Beginning Balance: $10,128.47"
        # Consumer format: "Beginning Balance on Feb 19 $ 10,128.47"
        summary.beginning_balance = find_amount(text, [
            r"Beginning\s+Balance[^\n]*\$\s*([\d,]+\.?\d*)",
            r"Beginning\s+[Bb]alance[:\s]*\$?([\d,]+\.?\d*)",
        ])
        summary.ending_balance = find_amount(text, [
            r"Ending\s+Balance[^\n]*\$\s*([\d,]+\.?\d*)",
            r"Ending\s+[Bb]alance[:\s]*\$?([\d,]+\.?\d*)",
        ])

        # --- Deposits / Credits ---
        # Consumer: "Total Deposits / Credits $ 1,256.90" at section end
        # Consumer: "Deposits / Credits 1,256.90" in account summary
        summary.total_deposits = find_amount(text, [
            r"Total\s+Deposits\s*/\s*Credits[:\s]*\$?\s*([\d,]+\.?\d*)",
            r"Total\s+[Dd]eposits\s+and\s+[Cc]redits[:\s]*\$?([\d,]+\.?\d*)",
            r"Total\s+[Cc]redits[:\s]*\$?([\d,]+\.?\d*)",
            # Account summary line
            r"Deposits\s*/\s*Credits\s+([\d,]+\.?\d*)",
        ])

        # --- Withdrawals ---
        # Consumer format has separate "Card Withdrawals" and "Other Withdrawals"
        # with subtotals. Sum them for total.
        card_wd = find_amount(text, [
            r"Total\s+Card\s+Withdrawals[:\s]*\$?\s*([\d,]+\.?\d*)",
        ])
        other_wd = find_amount(text, [
            r"Total\s+Other\s+Withdrawals[:\s]*\$?\s*([\d,]+\.?\d*)",
        ])
        if card_wd is not None or other_wd is not None:
            summary.total_withdrawals = round(
                abs(card_wd or 0) + abs(other_wd or 0), 2
            )
        else:
            # Business format fallback
            summary.total_withdrawals = find_amount(text, [
                r"Total\s+[Ww]ithdrawals\s+and\s+[Dd]ebits[:\s]*\$?([\d,]+\.?\d*)",
                r"Total\s+[Dd]ebits[:\s]*\$?([\d,]+\.?\d*)",
            ])

        # --- Average daily balance ---
        summary.average_daily_balance = find_amount(text, [
            r"Average\s+(?:Daily\s+)?[Bb]alance[:\s]*\$?([\d,]+\.?\d*)",
        ])

        # --- NSF count ---
        nsf_matches = re.findall(
            r"\bNSF\b|\bOverdraft\b|\bReturned\s+Item\b",
            text, re.IGNORECASE,
        )
        summary.nsf_count = len(nsf_matches)

        # --- Account holder ---
        # US Bank repeats the header on each page. Page 3+ has a clean format:
        #   "Account Number:\n1 575 1432 7020\nAMBERLYN DINH\n628 WILLIAMSON..."
        # Page 1 has barcode noise. Match name directly after the account number line.
        holder_match = re.search(
            r"Account\s+Number:\s*\n"
            r"\s*[\d][\d\s-]+[\d]\s*\n"  # account number line (digits with spaces/hyphens)
            r"\s*([A-Z][A-Z]+(?:\s+[A-Z][A-Z]+)+)\s*\n"  # ALL-CAPS name
            r"\s*\d+\s+[A-Z]",  # followed by street address number
            text,
        )
        if holder_match:
            name = holder_match.group(1).strip()
            if len(name) < 60 and not any(kw in name for kw in ["BANK", "STATEMENT", "CHECKING"]):
                summary.account_holder = name

        # --- Account number last 4 ---
        # Format: "Account Number:\n1 575 1432 7020" or "1-575-1432-7020"
        acct_match = re.search(
            r"Account\s+Number[:\s]*\n?\s*([\d][\d\s-]+[\d])",
            text, re.IGNORECASE,
        )
        if acct_match:
            digits = re.sub(r"[\s-]", "", acct_match.group(1))
            if len(digits) >= 4:
                summary.account_number_last4 = digits[-4:]

        # --- Deposit count ---
        deposit_lines = re.findall(
            r"(?:Electronic Deposit|Debit Purchase Ret)",
            text, re.IGNORECASE,
        )
        if deposit_lines:
            summary.deposit_count = len(deposit_lines)

        return summary

    def extract_transactions(self, text: str, tables: list[ExtractedTable]) -> list[Transaction]:
        """Extract transactions from US Bank statement text.

        US Bank Uni-Statement transactions are multi-line:
          Feb 24 Debit Purchase Ret - VISA On 022326 Amzn.com/bil WA 4109456571 $ 9.69
                 AMAZON MKTPLACE REF # 74692166054109456571 US1
        """
        transactions: list[Transaction] = []

        sections = self._split_sections(text)
        for section_type, section_text in sections:
            txns = self._extract_section_transactions(section_text, section_type)
            transactions.extend(txns)

        return transactions

    def compute_derived_metrics(
        self,
        summary: BankStatementSummary,
        transactions: list[Transaction],
    ) -> DerivedMetrics:
        """Override to parse the Balance Summary table from US Bank statements."""
        metrics = super().compute_derived_metrics(summary, transactions)

        # Parse the Balance Summary section for daily ending balances
        if not metrics.daily_ending_balances and self._raw_text:
            bal_section = re.search(
                r"Balance\s+Summary\s*\n"
                r"Date\s+Ending\s+Balance.*?\n"
                r"(.*?)"
                r"(?:Balances\s+only|$)",
                self._raw_text, re.DOTALL,
            )
            if bal_section:
                # Lines have pairs: "Feb 19 9,939.81 Mar 2 9,698.04 Mar 11 7,010.07"
                daily_balances: dict[str, float] = {}
                for match in re.finditer(
                    r"([A-Z][a-z]{2}\s+\d{1,2})\s+([\d,]+\.\d{2})",
                    bal_section.group(1),
                ):
                    date_str = parse_date(f"{match.group(1)}, {self._stmt_year}")
                    amount = parse_amount(match.group(2))
                    if date_str and amount is not None:
                        daily_balances[date_str] = amount

                if daily_balances:
                    metrics.daily_ending_balances = daily_balances
                    metrics.negative_balance_days = sum(
                        1 for v in daily_balances.values() if v < 0
                    )
                    metrics.calculated_adb = round(
                        sum(daily_balances.values()) / len(daily_balances), 2
                    )

        return metrics

    # ── Private helpers ──────────────────────────────────────────────────

    def _split_sections(self, text: str) -> list[tuple[str, str]]:
        """Split statement text into typed deposit/withdrawal sections."""
        sections: list[tuple[str, str]] = []

        # Deposits / Credits
        dep_match = re.search(
            r"Deposits\s*/\s*Credits\s*\n"
            r"Date\s+Description.*?\n"
            r"(.*?)"
            r"Total\s+Deposits\s*/\s*Credits",
            text, re.DOTALL,
        )
        if dep_match:
            sections.append(("credit", dep_match.group(1)))

        # Card Withdrawals (initial + continued)
        for card_match in re.finditer(
            r"Card\s+Withdrawals(?:\s+\(continued\))?\s*\n"
            r"(?:Card\s+Number:.*?\n)?"
            r"Date\s+Description.*?\n"
            r"(.*?)"
            r"(?:Card\s+\d+\s+Withdrawals\s+Subtotal|Total\s+Card\s+Withdrawals)",
            text, re.DOTALL,
        ):
            sections.append(("debit", card_match.group(1)))

        # Other Withdrawals (initial + continued)
        for other_match in re.finditer(
            r"Other\s+Withdrawals(?:\s+\(continued\))?\s*\n"
            r"Date\s+Description.*?\n"
            r"(.*?)"
            r"Total\s+Other\s+Withdrawals",
            text, re.DOTALL,
        ):
            sections.append(("debit", other_match.group(1)))

        return sections

    def _extract_section_transactions(
        self, section_text: str, txn_type: str
    ) -> list[Transaction]:
        """Extract individual transactions from a section.

        Each transaction starts with a date like 'Feb 24' or 'Mar 2'.
        """
        txns: list[Transaction] = []

        # Split on transaction start lines (date at line start)
        parts = re.split(
            r"^([A-Z][a-z]{2}\s+\d{1,2})\s+",
            section_text,
            flags=re.MULTILINE,
        )

        # parts: [before_first, date1, content1, date2, content2, ...]
        i = 1
        while i < len(parts) - 1:
            date_str = parts[i].strip()
            content = parts[i + 1]
            i += 2

            first_line = content.split("\n")[0].strip()

            # Extract amount — look for "$ 9.69" or "$9.69" with optional trailing minus
            amount = None
            amount_matches = re.findall(r"\$\s*([\d,]+\.\d{2})-?", content)
            if amount_matches:
                # Use the first amount found (the transaction amount, not ref numbers)
                amount = parse_amount(amount_matches[0])
            else:
                # Bare amount at end of first line
                bare_match = re.search(r"([\d,]+\.\d{2})-?\s*$", first_line)
                if bare_match:
                    amount = parse_amount(bare_match.group(1))

            if amount is None:
                continue

            # Build description — strip amount and long ref numbers
            desc = re.sub(r"\s*\$?\s*[\d,]+\.\d{2}-?\s*$", "", first_line).strip()
            desc = re.sub(r"\s+\d{10,}\s*$", "", desc).strip()

            # Parse short date with statement year
            parsed_date = parse_date(f"{date_str}, {self._stmt_year}") or date_str

            txns.append(Transaction(
                date=parsed_date,
                description=desc,
                amount=round(abs(amount), 2),
                type=txn_type,
            ))

        return txns


TemplateRegistry.register(USBankTemplate())
