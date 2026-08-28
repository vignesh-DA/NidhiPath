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
from app.modules.module1_recommender.welfare_engine import (
    filter_welfare_schemes,
    clear_welfare_cache,
    load_welfare_schemes,
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


# ─── Welfare Engine (Module 1B) ──────────────────────────────────────────────
# Mirrors schemes_production_deduped.json field shapes: income_criteria as a
# LIST of {type, operator, amount} dicts, caste_or_target_scope as a list,
# education_criteria as unstructured list-of-strings.

TEST_WELFARE_SCHEMES = [
    {
        "scheme_id": "welf_central_sc",
        "scheme_name": "Central SC Venture Scheme",
        "issuing_state": "central",
        "benefits": "Subsidy for SC entrepreneurs",
        "income_criteria": [
            {"type": "annual_family_income", "operator": "less_than", "amount": 250000}
        ],
        "caste_or_target_scope": ["SC", "ST"],
        "education_criteria": [],
    },
    {
        "scheme_id": "welf_karnataka_obc",
        "scheme_name": "Karnataka OBC Development Corp Scheme",
        "issuing_state": "Karnataka",
        "benefits": "Low-interest loans",
        "income_criteria": [
            {"type": "annual_family_income", "operator": "less_than_or_equal", "amount": 100000}
        ],
        "caste_or_target_scope": ["OBC"],
        "education_criteria": [],
    },
    {
        "scheme_id": "welf_tn_open",
        "scheme_name": "Tamil Nadu Open Welfare Scheme",
        "issuing_state": "Tamil Nadu",
        "benefits": "General assistance grant",
        "income_criteria": None,      # No income restriction
        "caste_or_target_scope": [],  # Open to all
        "education_criteria": [],
    },
    {
        "scheme_id": "welf_delhi_school",
        "scheme_name": "Delhi School Fee Reimbursement",
        "issuing_state": "Delhi",
        "benefits": "Tuition fee reimbursement",
        "income_criteria": [
            {"type": "annual_family_income", "operator": "less_than", "amount": 500000}
        ],
        "caste_or_target_scope": ["General"],
        "education_criteria": ["Students in public schools from Class I to XII"],
    },
]


class TestWelfare:
    """
    Tests for filter_welfare_schemes (Module 1B — secondary tier).
    Rule-based filtering ONLY: issuing_state, income_criteria,
    caste_or_target_scope, education keywords. These tests double as the guard
    for the no-RAG-for-eligibility architecture rule: every assertion here
    exercises a deterministic rule, never a similarity score.
    """

    @pytest.fixture(autouse=True)
    def reset_welfare_cache(self):
        clear_welfare_cache()
        yield
        clear_welfare_cache()

    # ── State filter ──

    def test_state_filter_central_always_matches(self):
        # Income ₹80,000 clears the Karnataka scheme's ₹1,00,000 cap →
        # both state-eligible schemes appear.
        result = filter_welfare_schemes(
            income_level=80000, user_state="Karnataka",
            caste_scope=None, schemes=TEST_WELFARE_SCHEMES,
        )
        ids = [m.scheme_id for m in result.matches]
        assert "welf_central_sc" in ids      # central → everyone
        assert "welf_karnataka_obc" in ids   # exact state match
        assert "welf_tn_open" not in ids     # different state, not central
        assert "welf_delhi_school" not in ids

        # Same state, but income ₹2,00,000 breaches the Karnataka cap →
        # only the central scheme survives (state match alone is not enough).
        result_high = filter_welfare_schemes(
            income_level=200000, user_state="Karnataka",
            caste_scope=None, schemes=TEST_WELFARE_SCHEMES,
        )
        assert [m.scheme_id for m in result_high.matches] == ["welf_central_sc"]

    def test_no_state_returns_central_only(self):
        result = filter_welfare_schemes(
            income_level=200000, user_state=None,
            caste_scope=None, schemes=TEST_WELFARE_SCHEMES,
        )
        ids = [m.scheme_id for m in result.matches]
        assert ids == ["welf_central_sc"]

    # ── Income filter ──

    def test_income_cap_boundary_inclusive(self):
        """less_than_or_equal at exactly ₹1,00,000 must still match."""
        result = filter_welfare_schemes(
            income_level=100000, user_state="Karnataka",
            caste_scope=["OBC"], schemes=TEST_WELFARE_SCHEMES,
        )
        ids = [m.scheme_id for m in result.matches]
        assert "welf_karnataka_obc" in ids

    def test_income_cap_excludes_higher_income(self):
        result = filter_welfare_schemes(
            income_level=150000, user_state="Karnataka",
            caste_scope=["OBC"], schemes=TEST_WELFARE_SCHEMES,
        )
        ids = [m.scheme_id for m in result.matches]
        assert "welf_karnataka_obc" not in ids  # lte ₹1,00,000 — ₹1,50,000 fails

    def test_satisfying_any_one_criterion_passes(self):
        """income_criteria is a LIST — user must satisfy ANY one criterion."""
        two_criteria = [
            {
                "scheme_id": "welf_multi",
                "scheme_name": "Multi Criteria Scheme",
                "issuing_state": "central",
                "income_criteria": [
                    {"type": "annual_family_income", "operator": "less_than", "amount": 50000},
                    {"type": "annual_family_income", "operator": "greater_than", "amount": 400000},
                ],
                "caste_or_target_scope": [],
            },
        ]
        result = filter_welfare_schemes(
            income_level=450000, user_state=None, caste_scope=None, schemes=two_criteria,
        )
        assert result.total_matches == 1

    def test_no_income_criteria_open_to_all_income(self):
        """Scheme with no income_criteria must not be blocked by income —
        only by state here (Tamil Nadu vs user in Tamil Nadu)."""
        result = filter_welfare_schemes(
            income_level=10000000, user_state="Tamil Nadu", caste_scope=None,
            schemes=TEST_WELFARE_SCHEMES,
        )
        ids = [m.scheme_id for m in result.matches]
        assert "welf_tn_open" in ids

    # ── Caste / target scope filter ──

    def test_caste_scope_overlap_with_aliases(self):
        result = filter_welfare_schemes(
            income_level=200000, user_state=None,
            caste_scope=["scheduled caste"], schemes=TEST_WELFARE_SCHEMES,
        )
        ids = [m.scheme_id for m in result.matches]
        assert "welf_central_sc" in ids  # "scheduled caste" alias matches "SC"

    def test_caste_mismatch_excluded(self):
        # caste ["OBC"] vs central scheme's SC/ST scope → excluded. Karnataka
        # scheme is caste-compatible but income-blocked (₹2,00,000 > ₹1,00,000
        # cap). TN open scheme is state-blocked (user_state=None → central
        # only, per test_no_state_returns_central_only). Net: nothing matches.
        result = filter_welfare_schemes(
            income_level=200000, user_state=None,
            caste_scope=["OBC"], schemes=TEST_WELFARE_SCHEMES,
        )
        ids = [m.scheme_id for m in result.matches]
        assert "welf_central_sc" not in ids  # SC/ST scope vs OBC user
        assert ids == []
        # Open-scope schemes still match caste-specific users — see
        # test_open_scope_matches_everyone (with a matching state).

    def test_open_scope_matches_everyone(self):
        result = filter_welfare_schemes(
            income_level=200000, user_state="Tamil Nadu",
            caste_scope=["ST"], schemes=TEST_WELFARE_SCHEMES,
        )
        assert "welf_tn_open" in [m.scheme_id for m in result.matches]

    # ── Education keyword filter (approximate) ──

    def test_education_keyword_match(self):
        result = filter_welfare_schemes(
            income_level=200000, user_state="Delhi", caste_scope=["General"],
            education_keywords=["public schools"], schemes=TEST_WELFARE_SCHEMES,
        )
        ids = [m.scheme_id for m in result.matches]
        assert "welf_delhi_school" in ids

    def test_education_keyword_miss_excludes(self):
        result = filter_welfare_schemes(
            income_level=200000, user_state="Delhi", caste_scope=["General"],
            education_keywords=["college"], schemes=TEST_WELFARE_SCHEMES,
        )
        ids = [m.scheme_id for m in result.matches]
        assert "welf_delhi_school" not in ids

    def test_no_education_keywords_is_inclusive(self):
        result = filter_welfare_schemes(
            income_level=200000, user_state="Delhi", caste_scope=["General"],
            education_keywords=None, schemes=TEST_WELFARE_SCHEMES,
        )
        assert "welf_delhi_school" in [m.scheme_id for m in result.matches]

    # ── Output contract ──

    def test_welfare_matches_always_approximate(self):
        """Spec: the welfare tier is APPROXIMATE by definition — it must never
        be presented with the same confidence as NSFDC credit matches."""
        result = filter_welfare_schemes(
            income_level=100000, user_state="Karnataka",
            caste_scope=["OBC"], schemes=TEST_WELFARE_SCHEMES,
        )
        assert result.total_matches >= 1
        assert all(m.match_confidence == "approximate" for m in result.matches)
        assert all(m.match_reasons for m in result.matches)  # human-readable reasons
        assert "approximate" in result.disclaimer.lower()

    def test_max_results_cap(self):
        many = [
            {
                "scheme_id": f"welf_{i}",
                "scheme_name": f"Welfare {i}",
                "issuing_state": "central",
                "income_criteria": None,
                "caste_or_target_scope": [],
            }
            for i in range(30)
        ]
        result = filter_welfare_schemes(
            income_level=200000, user_state=None, caste_scope=None,
            schemes=many, max_results=5,
        )
        assert result.total_matches == 5
        assert len(result.matches) == 5

    # ── Real corpus + robustness ──

    def test_real_corpus_loads_and_matches(self):
        """Smoke test against the real 377-scheme corpus — proves the loader
        and the rule filters work on production data shapes, not just
        fixtures."""
        schemes = load_welfare_schemes()
        assert len(schemes) >= 300
        assert all("scheme_name" in s or "name" in s for s in schemes)
        # Rule filters must produce at least one match across major states
        matched_anywhere = False
        for state in ("Madhya Pradesh", "Tamil Nadu", "Delhi", "Punjab", "Goa", "Karnataka"):
            r = filter_welfare_schemes(
                income_level=250000, user_state=state, caste_scope=None, schemes=schemes,
            )
            if r.total_matches > 0:
                matched_anywhere = True
                break
        assert matched_anywhere, "Rule filters must produce matches against the real corpus"

    def test_malformed_records_do_not_crash(self):
        broken = [
            {"scheme_id": 123, "scheme_name": "Int ID Scheme", "issuing_state": "central"},
            {"scheme_name": "No ID Scheme"},
            {
                "scheme_id": "welf_string_income", "scheme_name": "String Income",
                "issuing_state": "central", "income_criteria": "less than 2 lakh",
            },
            {
                "scheme_id": "welf_nulls", "scheme_name": None, "issuing_state": None,
                "income_criteria": None, "caste_or_target_scope": None,
            },
        ]
        result = filter_welfare_schemes(
            income_level=200000, user_state=None, caste_scope=None, schemes=broken,
        )
        # Must not raise; the valid central schemes must be returned
        ids = [m.scheme_id for m in result.matches]
        assert "123" in ids                 # int id coerced to str
        assert "welf_string_income" in ids  # unparseable income → included for user verification
