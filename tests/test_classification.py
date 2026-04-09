"""Tests for document classification."""

from app.classification.classifier import classify


def test_classify_bank_statement(sample_chase_text):
    result = classify(sample_chase_text)
    assert result.document_type == "bank_statement"
    assert result.confidence >= 0.5


def test_classify_bofa(sample_bofa_text):
    result = classify(sample_bofa_text)
    assert result.document_type == "bank_statement"


def test_classify_personal_tax(sample_1040_text):
    result = classify(sample_1040_text)
    assert result.document_type == "personal_tax_return"
    assert result.confidence >= 0.5


def test_classify_business_tax(sample_1120s_text):
    result = classify(sample_1120s_text)
    assert result.document_type == "business_tax_return"
    assert result.subtype == "1120S"


def test_classify_mca_application(sample_mca_application_text):
    result = classify(sample_mca_application_text)
    assert result.document_type == "mca_application"
    assert result.confidence >= 0.5


def test_classify_unknown():
    result = classify("some random text that doesn't match anything specific")
    # Should return something, even if low confidence
    assert result.document_type is not None


def test_classify_empty():
    result = classify("")
    assert result.document_type == "unknown"
    assert result.confidence == 0.0


def test_classify_voided_check():
    text = "VOID  Pay to the order of  Routing: 123456789  Account: 987654321  Check No 1001"
    result = classify(text)
    assert result.document_type == "voided_check"


def test_classify_drivers_license():
    text = "DRIVER LICENSE  State of California  DOB: 01/15/1985  EXP: 01/15/2030  Class C"
    result = classify(text)
    assert result.document_type == "drivers_license"


def test_classify_ucc():
    text = "UCC FINANCING STATEMENT  Secured Party: ABC Fund  Debtor: XYZ Corp  Filing Number: 12345"
    result = classify(text)
    assert result.document_type == "ucc_filing"
