"""Tests for tax return parsers."""

from app.parsers.tax.business import parse_business_tax_return
from app.parsers.tax.personal import parse_personal_tax_return


class TestBusinessTaxParser:
    def test_parse_1120s(self, sample_1120s_text):
        result = parse_business_tax_return(sample_1120s_text)
        assert result.filing_type == "1120S"
        assert result.business_name == "ACME SERVICES INC"
        assert result.ein == "12-3456789"
        assert result.gross_receipts == 1250000.00
        assert result.net_income == 185000.00
        assert result.total_assets == 890000.00

    def test_parse_1120(self):
        text = """Form 1120
U.S. Corporation Income Tax Return
For tax year 2025

Name of corporation: BIG CORP INC
Employer Identification Number: 45-6789012

Gross receipts or sales    $500,000
Taxable income             $75,000
Total assets               $1,200,000
"""
        result = parse_business_tax_return(text)
        assert result.filing_type == "1120"
        assert result.gross_receipts == 500000.00
        assert result.net_income == 75000.00

    def test_parse_schedule_c(self):
        text = """Schedule C
Profit or Loss From Business

Name of proprietor: Jane Smith
Principal business: Consulting

Gross receipts: $120,000
Net profit: $45,000
"""
        result = parse_business_tax_return(text)
        assert result.filing_type == "schedule_c"
        assert result.gross_receipts == 120000.00


class TestPersonalTaxParser:
    def test_parse_1040(self, sample_1040_text):
        result = parse_personal_tax_return(sample_1040_text)
        assert result.ssn_last4 == "5678"
        assert result.filing_status == "Married filing jointly"
        assert result.adjusted_gross_income == 170000.00
        assert result.schedule_c_income == 45000.00

    def test_parse_single_filer(self):
        text = """Form 1040
U.S. Individual Income Tax Return
For the year 2025

Your first name: Alice Wonderland
Social Security Number: 123-45-9999

Filing Status: Single

Adjusted Gross Income: $95,000
"""
        result = parse_personal_tax_return(text)
        assert result.name is not None
        assert result.ssn_last4 == "9999"
        assert result.filing_status == "Single"
        assert result.adjusted_gross_income == 95000.00
