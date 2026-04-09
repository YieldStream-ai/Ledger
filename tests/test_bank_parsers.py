"""Tests for bank statement parsers."""

from app.models.responses import ExtractedTable
from app.parsers.bank.chase import ChaseTemplate
from app.parsers.bank.bofa import BofATemplate
from app.parsers.bank.wells_fargo import WellsFargoTemplate
from app.parsers.bank.generic import GenericBankParser
from app.parsers.bank.registry import TemplateRegistry


class TestChaseTemplate:
    def test_matches_chase(self, sample_chase_text):
        t = ChaseTemplate()
        score = t.matches(sample_chase_text, [])
        assert score >= 0.6

    def test_no_match_bofa(self, sample_bofa_text):
        t = ChaseTemplate()
        score = t.matches(sample_bofa_text, [])
        assert score < 0.3

    def test_extract_summary(self, sample_chase_text):
        t = ChaseTemplate()
        summary = t.extract_summary(sample_chase_text, [])
        assert summary.bank_name == "Chase"
        assert summary.template_used == "chase"
        assert summary.beginning_balance == 15432.10
        assert summary.ending_balance == 18765.42
        assert summary.total_deposits == 87654.32
        assert summary.nsf_count >= 1
        assert summary.account_number_last4 == "4567"
        assert summary.period_start == "2026-03-01"
        assert summary.period_end == "2026-03-31"

    def test_extract_transactions(self, sample_chase_text):
        t = ChaseTemplate()
        txns = t.extract_transactions(sample_chase_text, [])
        assert len(txns) > 0
        # Should have both credits and debits
        credits = [tx for tx in txns if tx.type == "credit"]
        debits = [tx for tx in txns if tx.type == "debit"]
        assert len(credits) > 0
        assert len(debits) > 0

    def test_derived_metrics(self, sample_chase_text):
        t = ChaseTemplate()
        summary = t.extract_summary(sample_chase_text, [])
        txns = t.extract_transactions(sample_chase_text, [])
        metrics = t.compute_derived_metrics(summary, txns)

        if txns:
            assert metrics.largest_deposit is not None or metrics.largest_withdrawal is not None


class TestBofATemplate:
    def test_matches_bofa(self, sample_bofa_text):
        t = BofATemplate()
        score = t.matches(sample_bofa_text, [])
        assert score >= 0.6

    def test_no_match_chase(self, sample_chase_text):
        t = BofATemplate()
        score = t.matches(sample_chase_text, [])
        assert score < 0.3

    def test_extract_summary(self, sample_bofa_text):
        t = BofATemplate()
        summary = t.extract_summary(sample_bofa_text, [])
        assert summary.bank_name == "Bank of America"
        assert summary.beginning_balance == 22100.50
        assert summary.ending_balance == 66692.60
        assert summary.total_deposits == 65432.10
        assert summary.account_number_last4 == "7890"


class TestWellsFargoTemplate:
    def test_matches_wells(self, sample_wells_fargo_text):
        t = WellsFargoTemplate()
        score = t.matches(sample_wells_fargo_text, [])
        assert score >= 0.6

    def test_extract_summary(self, sample_wells_fargo_text):
        t = WellsFargoTemplate()
        summary = t.extract_summary(sample_wells_fargo_text, [])
        assert summary.bank_name == "Wells Fargo"
        assert summary.beginning_balance == 10200.00
        assert summary.ending_balance == 16700.00
        assert summary.total_deposits == 55000.00
        assert summary.total_withdrawals == 48500.00
        assert summary.account_number_last4 == "2345"


class TestGenericParser:
    def test_always_matches_at_zero(self):
        g = GenericBankParser()
        assert g.matches("anything", []) == 0.0

    def test_extract_summary_generic(self, sample_chase_text):
        """Generic parser should still extract some data from Chase text."""
        g = GenericBankParser()
        summary = g.extract_summary(sample_chase_text, [])
        # Should pick up beginning/ending balance
        assert summary.beginning_balance is not None
        assert summary.ending_balance is not None

    def test_transaction_table_parsing(self):
        """Test generic parser with a structured table."""
        table = ExtractedTable(
            page=1,
            headers=["Date", "Description", "Amount", "Balance"],
            rows=[
                ["03/01/2026", "ACH DEPOSIT", "5,000.00", "15,000.00"],
                ["03/02/2026", "CHECK #100", "-1,200.00", "13,800.00"],
            ],
        )
        g = GenericBankParser()
        txns = g.extract_transactions("", [table])
        assert len(txns) == 2
        assert txns[0].type == "credit"
        assert txns[0].amount == 5000.00
        assert txns[1].type == "debit"
        assert txns[1].amount == 1200.00


class TestTemplateRegistry:
    def test_registry_has_templates(self):
        templates = TemplateRegistry.list_templates()
        assert "chase" in templates
        assert "bofa" in templates
        assert "wells_fargo" in templates

    def test_registry_matches_chase(self, sample_chase_text):
        template, confidence = TemplateRegistry.match(sample_chase_text, [])
        assert template.template_id == "chase"
        assert confidence >= 0.5

    def test_registry_matches_bofa(self, sample_bofa_text):
        template, confidence = TemplateRegistry.match(sample_bofa_text, [])
        assert template.template_id == "bofa"
        assert confidence >= 0.5

    def test_registry_falls_back_to_generic(self):
        template, confidence = TemplateRegistry.match("random text with no bank", [])
        assert template.template_id == "generic"
