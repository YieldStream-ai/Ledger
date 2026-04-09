"""Tests for the extraction orchestrator and utilities."""

from app.utils.currency import parse_amount, find_amount
from app.utils.dates import parse_date, find_date_range


class TestCurrencyParsing:
    def test_simple_amount(self):
        assert parse_amount("$1,234.56") == 1234.56

    def test_negative_amount(self):
        assert parse_amount("-$1,234.56") == -1234.56

    def test_parenthesized_negative(self):
        assert parse_amount("($500.00)") == -500.00

    def test_no_dollar_sign(self):
        assert parse_amount("1234.56") == 1234.56

    def test_trailing_minus(self):
        assert parse_amount("1,234.56-") == -1234.56

    def test_no_decimals(self):
        assert parse_amount("$1,234") == 1234.0

    def test_empty(self):
        assert parse_amount("") is None
        assert parse_amount(None) is None

    def test_invalid(self):
        assert parse_amount("abc") is None

    def test_find_amount(self):
        text = "Total Deposits: $12,345.67"
        result = find_amount(text, [r"Total\s+Deposits[:\s]*\$?([\d,]+\.?\d*)"])
        assert result == 12345.67


class TestDateParsing:
    def test_us_format(self):
        assert parse_date("03/15/2026") == "2026-03-15"

    def test_short_year(self):
        assert parse_date("03/15/26") == "2026-03-15"

    def test_named_month(self):
        assert parse_date("March 15, 2026") == "2026-03-15"

    def test_short_month(self):
        assert parse_date("Mar 15, 2026") == "2026-03-15"

    def test_iso_format(self):
        assert parse_date("2026-03-15") == "2026-03-15"

    def test_empty(self):
        assert parse_date("") is None
        assert parse_date(None) is None

    def test_find_date_range_numeric(self):
        text = "Statement Period: 03/01/2026 - 03/31/2026"
        start, end = find_date_range(text)
        assert start == "2026-03-01"
        assert end == "2026-03-31"

    def test_find_date_range_through(self):
        text = "Statement Period: 01/01/2026 through 01/31/2026"
        start, end = find_date_range(text)
        assert start == "2026-01-01"
        assert end == "2026-01-31"

    def test_find_date_range_named(self):
        text = "Statement Period: March 1, 2026 - March 31, 2026"
        start, end = find_date_range(text)
        assert start == "2026-03-01"
        assert end == "2026-03-31"
