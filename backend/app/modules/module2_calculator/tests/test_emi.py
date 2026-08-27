"""
Tests for Module 2 — Financial Calculator (EMI Engine)

Test cases cover:
    - Known EMI values (hand-calculated)
    - Null handling (max_loan_amount=None, moratorium_months=None)
    - Cap enforcement (loan amount, tenure)
    - Moratorium shift (EMI starts at moratorium_months + 1)
    - Zero interest rate edge case
    - Amortization schedule generation
"""

import pytest
import math
from app.modules.module2_calculator.emi import calculate_emi, EmiBreakdown


class TestEmiCalculator:
    """Tests for calculate_emi."""

    def test_basic_emi_calculation(self):
        """Verify EMI formula against a known value."""
        # ₹1,00,000 at 6.5% for 36 months
        # Monthly rate r = 6.5/12/100 = 0.00541667
        # EMI = 100000 × 0.00541667 × (1.00541667)^36 / ((1.00541667)^36 - 1)
        # Expected EMI ≈ ₹3,063.35
        result = calculate_emi(
            scheme_id="test",
            requested_amount=100000,
            requested_months=36,
            interest_rate_pct=6.5,
            max_loan_amount=140000,
            project_cost=120000,
            project_cost_coverage_pct=90,
            moratorium_months=0,
        )

        assert isinstance(result, EmiBreakdown)
        # Effective loan should be min(100000, 140000, 120000*0.9=108000) = 100000
        assert result.effective_loan_amount == 100000
        assert result.effective_tenure_months == 36
        # EMI should be approximately ₹3,063
        assert abs(result.emi_amount - 3064.90) < 1.0
        # Total payment should be EMI × months
        assert result.total_payment == round(result.emi_amount * 36, 2)
        # Total interest = total_payment - loan
        assert result.total_interest == round(result.total_payment - 100000, 2)

    def test_loan_capped_to_max_loan_amount(self):
        """Requested amount above max_loan_amount should be capped."""
        result = calculate_emi(
            scheme_id="test",
            requested_amount=200000,  # Request ₹2L
            requested_months=36,
            interest_rate_pct=6.5,
            max_loan_amount=140000,  # Cap at ₹1.4L
            project_cost=300000,
            project_cost_coverage_pct=90,
        )

        assert result.effective_loan_amount == 140000
        assert len(result.caps_applied) > 0
        assert any("capped" in cap.lower() for cap in result.caps_applied)

    def test_loan_capped_to_cost_coverage(self):
        """Requested amount above project_cost × coverage% should be capped."""
        result = calculate_emi(
            scheme_id="test",
            requested_amount=100000,  # Request ₹1L
            requested_months=36,
            interest_rate_pct=6.5,
            max_loan_amount=200000,  # Max is ₹2L — not the binding cap
            project_cost=100000,  # Cost ₹1L × 90% = ₹90K — this is the binding cap
            project_cost_coverage_pct=90,
        )

        assert result.effective_loan_amount == 90000  # ₹1L × 90%

    def test_null_max_loan_derives_from_cost(self):
        """max_loan_amount=None → derive from project_cost × coverage."""
        result = calculate_emi(
            scheme_id="nsfdc_education_loan",
            requested_amount=500000,
            requested_months=84,
            interest_rate_pct=6.5,
            max_loan_amount=None,  # Education Loan has null max
            project_cost=600000,
            project_cost_coverage_pct=90,  # → ₹5,40,000 cap
        )

        # Should be min(500000, 600000*0.9=540000) = 500000
        assert result.effective_loan_amount == 500000

    def test_null_moratorium_treated_as_zero(self):
        """moratorium_months=None → treat as 0."""
        result = calculate_emi(
            scheme_id="test",
            requested_amount=100000,
            requested_months=36,
            interest_rate_pct=6.5,
            max_loan_amount=140000,
            project_cost=200000,
            moratorium_months=None,
        )

        assert result.moratorium_months == 0
        assert result.first_emi_month == 1

    def test_moratorium_shifts_first_emi(self):
        """EMI starts at moratorium_months + 1."""
        result = calculate_emi(
            scheme_id="test",
            requested_amount=100000,
            requested_months=36,
            interest_rate_pct=6.5,
            max_loan_amount=140000,
            project_cost=200000,
            moratorium_months=6,
        )

        assert result.moratorium_months == 6
        assert result.first_emi_month == 7
        assert result.total_duration_months == 42  # 6 + 36

    def test_tenure_capped_to_scheme_max(self):
        """Requested months above scheme's tenure cap should be capped."""
        result = calculate_emi(
            scheme_id="test",
            requested_amount=100000,
            requested_months=120,  # Request 10 years
            interest_rate_pct=6.5,
            max_loan_amount=140000,
            project_cost=200000,
            tenure_years=3,  # Scheme max 3 years = 36 months
        )

        assert result.effective_tenure_months == 36
        assert any("capped" in cap.lower() for cap in result.caps_applied)

    def test_zero_interest_rate(self):
        """Zero interest → simple principal/months division."""
        result = calculate_emi(
            scheme_id="test",
            requested_amount=120000,
            requested_months=12,
            interest_rate_pct=0,
            max_loan_amount=200000,
            project_cost=200000,
        )

        assert result.emi_amount == 10000  # ₹1,20,000 / 12
        assert result.total_interest == 0

    def test_amortization_schedule(self):
        """Schedule should have correct number of entries and sum to total."""
        result = calculate_emi(
            scheme_id="test",
            requested_amount=100000,
            requested_months=12,
            interest_rate_pct=6.5,
            max_loan_amount=200000,
            project_cost=200000,
            moratorium_months=3,
            include_schedule=True,
        )

        assert len(result.schedule) == 15  # 3 moratorium + 12 repayment
        # First 3 months are moratorium
        for i in range(3):
            assert result.schedule[i]["type"] == "moratorium"
            assert result.schedule[i]["emi"] == 0
        # Remaining 12 are repayment
        for i in range(3, 15):
            assert result.schedule[i]["type"] == "repayment"
            assert result.schedule[i]["emi"] == result.emi_amount
        # Last entry should have balance 0
        assert result.schedule[-1]["balance"] == 0

    def test_assumption_note_present(self):
        """Every result must carry the moratorium assumption disclaimer."""
        result = calculate_emi(
            scheme_id="test",
            requested_amount=100000,
            requested_months=36,
            interest_rate_pct=6.5,
            max_loan_amount=140000,
            project_cost=200000,
        )

        assert "moratorium" in result.assumption_note.lower()
        assert "documented" in result.assumption_note.lower()

    def test_high_interest_rate(self):
        """Aajeevika at 15% should produce higher EMI than 6.5%."""
        result_low = calculate_emi(
            scheme_id="micro",
            requested_amount=100000,
            requested_months=36,
            interest_rate_pct=6.5,
            max_loan_amount=140000,
            project_cost=200000,
        )
        result_high = calculate_emi(
            scheme_id="aajeevika",
            requested_amount=100000,
            requested_months=36,
            interest_rate_pct=15.0,
            max_loan_amount=140000,
            project_cost=200000,
        )

        assert result_high.emi_amount > result_low.emi_amount
        assert result_high.total_interest > result_low.total_interest
