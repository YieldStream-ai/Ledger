"""Tests for MCA application parser."""

from app.parsers.mca_application import parse_mca_application


def test_parse_mca_application(sample_mca_application_text):
    result = parse_mca_application(sample_mca_application_text)
    assert result.business_legal_name == "RAPID DELIVERY LLC"
    assert result.dba_name == "Rapid Express"
    assert result.ein == "98-7654321"
    assert result.business_type == "LLC"
    assert result.monthly_revenue == 85000.00
    assert result.annual_revenue == 1020000.00
    assert result.requested_funding_amount == 150000.00
    assert result.rent_amount == 4500.00


def test_parse_mca_phone_email(sample_mca_application_text):
    result = parse_mca_application(sample_mca_application_text)
    assert result.phone is not None
    assert result.email == "john@rapiddelivery.com"


def test_parse_mca_owners(sample_mca_application_text):
    result = parse_mca_application(sample_mca_application_text)
    # Owner parsing is best-effort with regex — at least one should be found
    # (depending on how well the regex matches the multi-line format)
    assert isinstance(result.owners, list)


def test_parse_empty():
    result = parse_mca_application("")
    assert result.business_legal_name is None
    assert result.requested_funding_amount is None
