"""Tests for the AI enrichment module."""

from __future__ import annotations

import json

import pytest

from app.ai.enrichment import BankIntelligenceResult, McaPosition, TransferFlag, _parse_json_response


class TestParseJsonResponse:
    def test_parses_clean_json(self):
        data = {"monthly_revenue_avg": 50000, "monthly_revenue_trend": "growing"}
        result = _parse_json_response(json.dumps(data))
        assert result == data

    def test_strips_markdown_fences(self):
        raw = '```json\n{"monthly_revenue_avg": 50000}\n```'
        result = _parse_json_response(raw)
        assert result["monthly_revenue_avg"] == 50000

    def test_strips_plain_fences(self):
        raw = '```\n{"monthly_revenue_avg": 50000}\n```'
        result = _parse_json_response(raw)
        assert result["monthly_revenue_avg"] == 50000


class TestBankIntelligenceResult:
    def test_default_values(self):
        result = BankIntelligenceResult()
        assert result.monthly_revenue_avg is None
        assert result.monthly_revenue_trend == "stable"
        assert result.active_mca_positions == []
        assert result.flagged_anomalies == []
        assert result.human_review_required is False

    def test_full_construction(self):
        result = BankIntelligenceResult(
            monthly_revenue_avg=75000,
            monthly_revenue_trend="growing",
            revenue_volatility=0.15,
            best_month_revenue=95000,
            worst_month_revenue=60000,
            average_daily_balance=12500,
            lowest_daily_balance=3200,
            ending_daily_balance=15000,
            edb_trend="growing",
            negative_days_count=0,
            nsf_count_30d=0,
            nsf_count_60d=1,
            nsf_count_90d=2,
            deposit_count=45,
            avg_transaction_size=1666.67,
            active_mca_positions=[
                McaPosition(lender_name="Funder A", daily_debit=150, estimated_balance=8000)
            ],
            total_daily_debits=150,
            stacking_burden_pct=6.0,
            dscr=1.67,
            lien_flags=[],
            transfer_flags=[
                TransferFlag(description="Owner Draw", amount=15000)
            ],
            flagged_anomalies=["Large withdrawal on 2026-01-15"],
            human_review_required=False,
            ocr_confidence=0.92,
            underwriting_summary="Strong revenue profile with consistent growth.",
        )
        assert result.monthly_revenue_avg == 75000
        assert len(result.active_mca_positions) == 1
        assert result.active_mca_positions[0].lender_name == "Funder A"
        assert len(result.transfer_flags) == 1

    def test_from_dict(self):
        """Simulate parsing a Gemini JSON response into the model."""
        raw = {
            "monthly_revenue_avg": 50000,
            "monthly_revenue_trend": "stable",
            "revenue_volatility": 0.2,
            "best_month_revenue": 60000,
            "worst_month_revenue": 40000,
            "average_daily_balance": 8000,
            "lowest_daily_balance": 1500,
            "ending_daily_balance": 9000,
            "edb_trend": "flat",
            "days_below_threshold": 0,
            "negative_days_count": 0,
            "nsf_count_30d": 0,
            "nsf_count_60d": 0,
            "nsf_count_90d": 0,
            "deposit_count": 30,
            "avg_transaction_size": 1666.67,
            "active_mca_positions": [],
            "total_daily_debits": 0,
            "stacking_burden_pct": 0,
            "dscr": None,
            "lien_flags": [],
            "transfer_flags": [],
            "flagged_anomalies": [],
            "human_review_required": False,
            "ocr_confidence": 0.95,
            "underwriting_summary": "Clean profile with stable revenue.",
        }
        result = BankIntelligenceResult(**raw)
        assert result.monthly_revenue_avg == 50000
        assert result.ocr_confidence == 0.95
