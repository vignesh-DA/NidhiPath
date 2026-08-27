"""
Tests for Module 1 — Credit Scheme Recommender

Test cases cover:
    - Exact cost boundaries
    - Overlapping scheme ranges (Micro Finance vs Aajeevika at ₹1,40,000)
    - Education path
    - Zero-match scenario
    - Income over cap
    - Sorting by interest rate ASC
    - Multiple matches returned as ranked list (never single)
"""

import pytest
from app.modules.module1_recommender.credit_engine import (
    filter_and_rank_credit_schemes,
    clear_schemes_cache,
    CreditRecommendationResult,
)


# ─── Test Data ───────────────────────────────────────────────────────────────
# Mirrors the real nsfdc_schemes.json structure with 5 schemes.
# 4 business_self_employment, 1 education. Purpose field manually tagged.

TEST_SCHEMES = [
    {
        "scheme_id": "nsfdc_micro_finance",
        "scheme_name": "Micro Finance Scheme",
        "purpose": "business_self_employment",
        "max_annual_income": 500000,
        "project_cost": {"min": 0, "max": 140000},
        "max_loan_amount": 140000,
        "project_cost_coverage_pct": 90,
        "interest_rate_pct": {"beneficiary": 6.5, "sca": 3.5},
        "tenure_years": 3,
        "moratorium_months": 3,
        "channel_partners": ["SCA", "NBFC-MFI"],
    },
    {
        "scheme_id": "nsfdc_aajeevika",
        "scheme_name": "Aajeevika Scheme",
        "purpose": "business_self_employment",
        "max_annual_income": 500000,
        "project_cost": {"min": 0, "max": 140000},
        "max_loan_amount": 140000,
        "project_cost_coverage_pct": 90,
        "interest_rate_pct": {"beneficiary": 15.0, "sca": 5.0},
        "tenure_years": 3,
        "moratorium_months": 3,
        "channel_partners": ["SCA", "NBFC-MFI"],
    },
    {
        "scheme_id": "nsfdc_udyam_nidhi",
        "scheme_name": "Udyam Nidhi Scheme",
        "purpose": "business_self_employment",
        "max_annual_income": 500000,
        "project_cost": {"min": 0, "max": 1000000},
        "max_loan_amount": 1000000,
        "project_cost_coverage_pct": 90,
        "interest_rate_pct": {"beneficiary": 8.0, "sca": 4.0},
        "tenure_years": 5,
        "moratorium_months": 6,
        "channel_partners": ["SCA", "PSB", "RRB"],
    },
    {
        "scheme_id": "nsfdc_term_loan",
        "scheme_name": "Term Loan Scheme",
        "purpose": "business_self_employment",
        "max_annual_income": 500000,
        "project_cost": {"min": 0, "max": 5000000},
        "max_loan_amount": 5000000,
        "project_cost_coverage_pct": 90,
        "interest_rate_pct": {"beneficiary": 6.5, "sca": 3.0},
        "tenure_years": 10,
        "moratorium_months": 6,
        "channel_partners": ["SCA", "PSB", "RRB"],
    },
    {
        "scheme_id": "nsfdc_education_loan",
        "scheme_name": "Education Loan Scheme",
        "purpose": "education",
        "max_annual_income": 500000,
        "project_cost": {"min": 0, "max": 2000000},
        "max_loan_amount": None,  # Null — derive from project_cost × coverage
        "project_cost_coverage_pct": 90,
        "interest_rate_pct": {"beneficiary": 6.5, "sca": 3.5},
        "tenure_years": 7,
        "moratorium_months": None,  # Null → treat as 0
        "channel_partners": ["SCA", "PSB"],
    },
]


@pytest.fixture(autouse=True)
def reset_cache():
    """Clear scheme cache before each test."""
    clear_schemes_cache()
    yield
    clear_schemes_cache()


# ─── Tests ───────────────────────────────────────────────────────────────────

class TestCreditEngine:
    """Tests for filter_and_rank_credit_schemes."""

    def test_basic_match_small_business(self):
        """Small business project ₹1,00,000 should match multiple schemes."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=100000,
            income_level=300000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        assert result.total_matches >= 2
        assert result.top_pick is not None
        # Top pick should have the lowest interest rate
        assert result.top_pick.interest_rate_beneficiary <= 8.0

    def test_overlapping_range_at_140000(self):
        """
        ₹1,40,000 is the overlap point — Micro Finance AND Aajeevika AND
        Udyam Nidhi AND Term Loan all cover this range. Must return multiple.
        """
        result = filter_and_rank_credit_schemes(
            estimated_cost=140000,
            income_level=300000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        # All 4 business schemes should match at this cost
        assert result.total_matches == 4
        # Top pick must be sorted by lowest rate (6.5% — either Micro Finance or Term Loan)
        assert result.top_pick.interest_rate_beneficiary == 6.5

    def test_sorted_by_interest_rate_asc(self):
        """Verify sorting: cheapest interest rate first."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=100000,
            income_level=300000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        rates = [result.top_pick.interest_rate_beneficiary]
        rates += [alt.interest_rate_beneficiary for alt in result.alternatives]
        assert rates == sorted(rates)

    def test_income_over_cap(self):
        """Income above ₹5,00,000 should match nothing."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=100000,
            income_level=600000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        assert result.total_matches == 0
        assert result.top_pick is None

    def test_cost_exceeds_all_schemes(self):
        """Cost above highest scheme max should match nothing (for business)."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=10000000,  # ₹1 crore — above all schemes
            income_level=300000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        assert result.total_matches == 0
        assert result.top_pick is None

    def test_education_path(self):
        """Education project type should match only the education scheme."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=500000,
            income_level=300000,
            project_type="education",
            education_status="admission_secured",
            schemes=TEST_SCHEMES,
        )
        assert result.total_matches == 1
        assert result.top_pick.scheme_id == "nsfdc_education_loan"

    def test_education_without_status_returns_nothing(self):
        """Education path without education_status should match nothing."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=500000,
            income_level=300000,
            project_type="education",
            education_status=None,
            schemes=TEST_SCHEMES,
        )
        assert result.total_matches == 0

    def test_exact_boundary_min_cost(self):
        """Cost at exact minimum (₹0) should still match."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=1,  # Just above 0
            income_level=300000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        assert result.total_matches >= 1

    def test_exact_boundary_max_cost(self):
        """Cost at exact maximum boundary should match."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=5000000,  # Exact max of Term Loan
            income_level=300000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        assert result.total_matches >= 1
        # Term Loan covers up to ₹50L
        matched_ids = [result.top_pick.scheme_id] + [a.scheme_id for a in result.alternatives]
        assert "nsfdc_term_loan" in matched_ids

    def test_exact_income_boundary(self):
        """Income exactly at cap (₹5,00,000) should still match."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=100000,
            income_level=500000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        assert result.total_matches >= 1

    def test_result_has_match_reason(self):
        """Every matched scheme should have a human-readable match_reason."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=100000,
            income_level=300000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        assert result.top_pick.match_reason != ""
        assert "₹" in result.top_pick.match_reason  # Should mention money amounts

    def test_result_echoes_input(self):
        """Result should echo input for transparency."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=100000,
            income_level=300000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        assert result.input_summary["estimated_cost"] == 100000
        assert result.input_summary["income_level"] == 300000
        assert result.input_summary["project_type"] == "business_self_employment"

    def test_top_pick_has_channel_partners(self):
        """Top pick should include channel partners list for Module 3 handoff."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=100000,
            income_level=300000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        assert len(result.top_pick.channel_partners) > 0

    def test_medium_cost_excludes_micro(self):
        """₹5,00,000 project should exclude Micro Finance and Aajeevika (max ₹1,40,000)."""
        result = filter_and_rank_credit_schemes(
            estimated_cost=500000,
            income_level=300000,
            project_type="business_self_employment",
            schemes=TEST_SCHEMES,
        )
        matched_ids = [result.top_pick.scheme_id] + [a.scheme_id for a in result.alternatives]
        assert "nsfdc_micro_finance" not in matched_ids
        assert "nsfdc_aajeevika" not in matched_ids
        assert "nsfdc_udyam_nidhi" in matched_ids
        assert "nsfdc_term_loan" in matched_ids
