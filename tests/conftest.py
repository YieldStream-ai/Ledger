"""Test fixtures — synthetic PDF generation for bank statement testing."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_chase_text() -> str:
    """Sample Chase bank statement text for parser testing."""
    return """JPMorgan Chase Bank, N.A.
chase.com

ACME TRUCKING LLC
123 Main Street
Anytown, ST 12345

CHASE BUSINESS CHECKING
Account Number: ****4567

Statement Period: 03/01/2026 - 03/31/2026

Account Summary
Beginning Balance                     $15,432.10
Deposits and Additions        15      $87,654.32
Electronic Withdrawals        42      $79,321.00
Checks and Other Withdrawals   3      $5,000.00
Ending Balance                        $18,765.42

Average Ledger Balance                $16,543.21

Deposits and Additions

03/01  ACH CREDIT SQUARE INC          5,432.10     20,864.20
03/05  ACH CREDIT STRIPE              3,200.00     24,064.20
03/10  WIRE TRANSFER IN              12,345.67     36,409.87
03/15  ACH CREDIT SQUARE INC          4,876.55     41,286.42
03/20  DEPOSIT                         2,500.00     43,786.42

Checks and Other Withdrawals

03/02  CHECK #1234                     1,500.00     18,932.10
03/12  CHECK #1235                     2,000.00     34,409.87
03/25  CHECK #1236                     1,500.00     42,286.42

Electronic Withdrawals

03/03  ACH DEBIT INSURANCE CO          1,200.00     17,732.10
03/07  ACH DEBIT DAILY DEBIT MCA       250.00      23,814.20
03/10  WIRE TRANSFER OUT               5,000.00     31,409.87

Daily Ending Balance
03/01  20,864.20
03/02  18,932.10
03/03  17,732.10

NSF FEE - Returned Item               34.00
"""


@pytest.fixture
def sample_bofa_text() -> str:
    """Sample Bank of America statement text."""
    return """Bank of America
bankofamerica.com

Business Advantage Checking

Account #: ****7890

Statement Period: February 1, 2026 - February 28, 2026

Beginning balance on 02/01/2026     $22,100.50
Deposits and Other Credits          $65,432.10
Checks and Substitute Checks        $8,500.00
ATM and Debit Card Withdrawals      $12,340.00
Ending balance on 02/28/2026        $66,692.60

Average Ledger Balance              $44,396.55
"""


@pytest.fixture
def sample_wells_fargo_text() -> str:
    """Sample Wells Fargo statement text."""
    return """Wells Fargo Bank
wellsfargo.com

Business Choice Checking
Account number: ****2345

Statement Period: 01/01/2026 through 01/31/2026

Beginning balance on 01/01          $10,200.00
Deposits/Credits                     $55,000.00
Withdrawals/Debits                   $48,500.00
Ending balance on 01/31             $16,700.00

Average ledger balance              $13,450.00

Transaction history
"""


@pytest.fixture
def sample_1040_text() -> str:
    """Sample 1040 personal tax return text."""
    return """Form 1040
U.S. Individual Income Tax Return
For the year 2025

Your first name: John Q. Taxpayer
Social Security Number: ***-**-5678

Filing Status: Married filing jointly

Wages, salaries, tips                    $125,000.00
Business income or (loss)                 $45,000.00
Adjusted Gross Income                    $170,000.00

Schedule C - Profit or Loss From Business
Net profit: $45,000.00
"""


@pytest.fixture
def sample_1120s_text() -> str:
    """Sample 1120S business tax return text."""
    return """Form 1120-S
U.S. Income Tax Return for an S Corporation
For tax year ending 12/31/2025

Name of corporation: ACME SERVICES INC
Employer Identification Number: 12-3456789

Gross receipts or sales                $1,250,000.00
Ordinary business income                 $185,000.00
Total assets                             $890,000.00
"""


@pytest.fixture
def sample_mca_application_text() -> str:
    """Sample MCA application text."""
    return """MERCHANT CASH ADVANCE APPLICATION

Business Legal Name: RAPID DELIVERY LLC
DBA: Rapid Express
Business Address: 456 Commerce Ave, Suite 200, Dallas, TX 75201
Phone: (214) 555-1234
Email: john@rapiddelivery.com
EIN: 98-7654321
Date of Incorporation: 03/15/2018
Business Type: LLC

Monthly Revenue: $85,000
Annual Revenue: $1,020,000
Requested Funding Amount: $150,000

Owner #1
Name: John Smith
Ownership: 75%

Owner #2
Name: Jane Doe
Ownership: 25%

Current MCA Positions:
Position: Yellowstone Capital - $500/day

Landlord: ABC Properties
Monthly Rent: $4,500
"""
