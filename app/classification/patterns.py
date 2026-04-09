"""Keyword and structural patterns for document classification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DocTypePattern:
    doc_type: str
    subtype: str | None
    # Primary signals: strong indicators (each match adds 0.3)
    primary: list[str]
    # Secondary signals: supporting evidence (each match adds 0.1)
    secondary: list[str]


PATTERNS: list[DocTypePattern] = [
    DocTypePattern(
        doc_type="bank_statement",
        subtype=None,
        primary=[
            "account summary",
            "beginning balance",
            "ending balance",
            "statement period",
            "deposits and additions",
            "withdrawals and debits",
            "checks and other withdrawals",
            "daily balance summary",
            "daily ledger balance",
        ],
        secondary=[
            "average daily balance",
            "total deposits",
            "total withdrawals",
            "nsf",
            "overdraft",
            "ach credit",
            "ach debit",
            "wire transfer",
            "check number",
            "transaction history",
            "account number",
        ],
    ),
    DocTypePattern(
        doc_type="business_tax_return",
        subtype="1120",
        primary=[
            "form 1120",
            "u.s. corporation income tax return",
            "corporation income tax",
        ],
        secondary=[
            "gross receipts",
            "taxable income",
            "total assets",
            "schedule l",
            "employer identification number",
        ],
    ),
    DocTypePattern(
        doc_type="business_tax_return",
        subtype="1120S",
        primary=[
            "form 1120-s",
            "form 1120s",
            "s corporation",
            "u.s. income tax return for an s corporation",
        ],
        secondary=[
            "gross receipts",
            "ordinary business income",
            "schedule k-1",
            "shareholders",
        ],
    ),
    DocTypePattern(
        doc_type="business_tax_return",
        subtype="1065",
        primary=[
            "form 1065",
            "u.s. return of partnership income",
            "partnership income",
        ],
        secondary=[
            "gross receipts",
            "ordinary business income",
            "schedule k-1",
            "partners",
        ],
    ),
    DocTypePattern(
        doc_type="business_tax_return",
        subtype="schedule_c",
        primary=[
            "schedule c",
            "profit or loss from business",
        ],
        secondary=[
            "gross receipts",
            "net profit",
            "business name",
            "principal business",
        ],
    ),
    DocTypePattern(
        doc_type="personal_tax_return",
        subtype="1040",
        primary=[
            "form 1040",
            "u.s. individual income tax return",
        ],
        secondary=[
            "adjusted gross income",
            "filing status",
            "wages, salaries",
            "standard deduction",
            "taxable income",
            "w-2",
        ],
    ),
    DocTypePattern(
        doc_type="drivers_license",
        subtype=None,
        primary=[
            "driver license",
            "driver's license",
            "identification card",
        ],
        secondary=[
            "dob",
            "date of birth",
            "exp",
            "expires",
            "class",
            "restrictions",
            "endorsements",
        ],
    ),
    DocTypePattern(
        doc_type="voided_check",
        subtype=None,
        primary=[
            "void",
        ],
        secondary=[
            "routing",
            "account",
            "check no",
            "check number",
            "pay to the order",
        ],
    ),
    DocTypePattern(
        doc_type="mca_application",
        subtype=None,
        primary=[
            "merchant cash advance",
            "funding application",
            "business funding",
            "advance application",
            "iso application",
        ],
        secondary=[
            "ownership percentage",
            "owner information",
            "requested amount",
            "use of funds",
            "current positions",
            "existing advances",
            "landlord",
            "monthly revenue",
            "annual revenue",
        ],
    ),
    DocTypePattern(
        doc_type="cc_processing_statement",
        subtype=None,
        primary=[
            "processing statement",
            "merchant processing",
            "credit card processing",
        ],
        secondary=[
            "visa",
            "mastercard",
            "amex",
            "discover",
            "batch",
            "chargebacks",
            "net deposits",
            "gross volume",
        ],
    ),
    DocTypePattern(
        doc_type="lease_agreement",
        subtype=None,
        primary=[
            "lease agreement",
            "commercial lease",
            "rental agreement",
        ],
        secondary=[
            "landlord",
            "tenant",
            "premises",
            "monthly rent",
            "lease term",
            "security deposit",
        ],
    ),
    DocTypePattern(
        doc_type="articles_of_incorporation",
        subtype=None,
        primary=[
            "articles of incorporation",
            "certificate of formation",
            "articles of organization",
            "certificate of incorporation",
        ],
        secondary=[
            "registered agent",
            "incorporator",
            "secretary of state",
            "organized under the laws",
        ],
    ),
    DocTypePattern(
        doc_type="ucc_filing",
        subtype=None,
        primary=[
            "ucc financing statement",
            "uniform commercial code",
            "ucc-1",
        ],
        secondary=[
            "secured party",
            "debtor",
            "filing number",
            "collateral",
        ],
    ),
]
