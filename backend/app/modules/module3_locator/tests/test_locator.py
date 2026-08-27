"""
Tests for Module 3 — Partner Locator

Test cases cover:
    - Capability filtering by partner type
    - SCA state-bound eligibility
    - National eligibility for PSB/RRB/etc.
    - Health deprioritization (not exclusion)
    - Full pipeline integration
    - Proximity stub returns correct status
"""

import pytest
from app.modules.module3_locator.capability_filter import (
    filter_by_capability,
    clear_partners_cache,
)
from app.modules.module3_locator.eligibility_filter import filter_by_eligibility
from app.modules.module3_locator.health_filter import filter_by_health
from app.modules.module3_locator.proximity import rank_by_proximity


# ─── Test Data ───────────────────────────────────────────────────────────────

TEST_PARTNERS = [
    {
        "partner_id": "sca_karnataka",
        "partner_name": "Karnataka SC/ST Development Corporation",
        "partner_type": "SCA",
        "state": "Karnataka",
        "contact": "+91-80-22345678",
    },
    {
        "partner_id": "sca_tamil_nadu",
        "partner_name": "Tamil Nadu Adi Dravidar Housing Development Corporation",
        "partner_type": "SCA",
        "state": "Tamil Nadu",
        "contact": "+91-44-22345678",
    },
    {
        "partner_id": "psb_sbi",
        "partner_name": "State Bank of India",
        "partner_type": "PSB",
        "state": "National",
        "contact": "+91-11-23345678",
    },
    {
        "partner_id": "rrb_kaveri",
        "partner_name": "Kaveri Grameena Bank",
        "partner_type": "RRB",
        "state": "Karnataka",
        "contact": "+91-80-22445678",
    },
    {
        "partner_id": "nbfc_mfi_1",
        "partner_name": "Bandhan Financial Services",
        "partner_type": "NBFC-MFI",
        "state": "National",
        "contact": "+91-33-22345678",
    },
]


@pytest.fixture(autouse=True)
def reset_cache():
    """Clear partner cache before each test."""
    clear_partners_cache()
    yield
    clear_partners_cache()


# ─── Step 1: Capability Filter ──────────────────────────────────────────────

class TestCapabilityFilter:
    def test_filters_by_partner_type(self):
        """Should return only partners whose type is in the scheme list."""
        result = filter_by_capability(
            scheme_channel_partners=["SCA", "PSB"],
            partners=TEST_PARTNERS,
        )
        types = {p["partner_type"] for p in result}
        assert types == {"SCA", "PSB"}
        assert len(result) == 3  # 2 SCAs + 1 PSB

    def test_case_insensitive_matching(self):
        """Partner type matching should be case-insensitive."""
        result = filter_by_capability(
            scheme_channel_partners=["sca", "psb"],
            partners=TEST_PARTNERS,
        )
        assert len(result) == 3

    def test_no_match_returns_empty(self):
        """Types not in data should return empty list."""
        result = filter_by_capability(
            scheme_channel_partners=["COOPERATIVE"],
            partners=TEST_PARTNERS,
        )
        assert len(result) == 0

    def test_all_types_returns_all(self):
        """All types should return all partners."""
        result = filter_by_capability(
            scheme_channel_partners=["SCA", "PSB", "RRB", "NBFC-MFI"],
            partners=TEST_PARTNERS,
        )
        assert len(result) == len(TEST_PARTNERS)


# ─── Step 2: Eligibility Filter ─────────────────────────────────────────────

class TestEligibilityFilter:
    def test_sca_state_match(self):
        """SCAs should only match when user's state matches."""
        partners_with_sca = [p for p in TEST_PARTNERS if p["partner_type"] in ("SCA", "PSB")]
        result = filter_by_eligibility(partners_with_sca, user_state="Karnataka")

        # Should include: Karnataka SCA + PSB (national), exclude: Tamil Nadu SCA
        ids = {p["partner_id"] for p in result}
        assert "sca_karnataka" in ids
        assert "sca_tamil_nadu" not in ids
        assert "psb_sbi" in ids

    def test_sca_excluded_without_state(self):
        """SCAs should be excluded when no user state is provided."""
        result = filter_by_eligibility(TEST_PARTNERS, user_state=None)
        types = {p["partner_type"] for p in result}
        assert "SCA" not in types

    def test_national_always_eligible(self):
        """PSB, RRB, NBFC-MFI should always be eligible regardless of state."""
        result = filter_by_eligibility(TEST_PARTNERS, user_state="Kerala")
        national_types = {p["partner_type"] for p in result if p["partner_type"] != "SCA"}
        assert "PSB" in national_types
        assert "RRB" in national_types
        assert "NBFC-MFI" in national_types


# ─── Step 3: Health Filter ──────────────────────────────────────────────────

class TestHealthFilter:
    def test_adds_health_metadata(self):
        """Every partner should get health metadata."""
        result = filter_by_health(TEST_PARTNERS)
        for partner in result:
            assert "health" in partner
            assert "npa_ratio" in partner["health"]
            assert "utilization_pct" in partner["health"]

    def test_never_hard_excludes(self):
        """Health filter must NEVER hard-exclude — only deprioritize."""
        # With mocked data, all are healthy, so count should be same
        result = filter_by_health(TEST_PARTNERS)
        assert len(result) == len(TEST_PARTNERS)

    def test_preserves_original_fields(self):
        """Health enrichment should not remove original partner fields."""
        result = filter_by_health(TEST_PARTNERS)
        for partner in result:
            assert "partner_id" in partner
            assert "partner_name" in partner
            assert "partner_type" in partner


# ─── Step 4: Proximity ──────────────────────────────────────────────────────

class TestProximity:
    def test_returns_stub_status(self):
        """Proximity is blocked — should return 'unavailable' status."""
        result = rank_by_proximity(TEST_PARTNERS)
        assert result["proximity_status"] == "unavailable"
        assert len(result["known_gaps"]) > 0

    def test_passes_through_all_partners(self):
        """Stub should pass through all partners unchanged."""
        result = rank_by_proximity(TEST_PARTNERS)
        assert len(result["partners"]) == len(TEST_PARTNERS)

    def test_discloses_nbfc_gap(self):
        """Must disclose the NBFC-MFI IFSC gap."""
        result = rank_by_proximity(TEST_PARTNERS)
        gaps_text = " ".join(result["known_gaps"])
        assert "NBFC-MFI" in gaps_text


# ─── Full Pipeline Integration ──────────────────────────────────────────────

class TestFullPipeline:
    def test_end_to_end_karnataka_term_loan(self):
        """
        Real test case: Karnataka user, Term Loan (SCA+PSB+RRB).
        Should get Karnataka SCA + all PSBs + all RRBs.
        """
        # Step 1: Capability
        step1 = filter_by_capability(
            scheme_channel_partners=["SCA", "PSB", "RRB"],
            partners=TEST_PARTNERS,
        )
        assert len(step1) >= 3

        # Step 2: Eligibility (Karnataka)
        step2 = filter_by_eligibility(step1, user_state="Karnataka")
        ids = {p["partner_id"] for p in step2}
        assert "sca_karnataka" in ids
        assert "sca_tamil_nadu" not in ids

        # Step 3: Health
        step3 = filter_by_health(step2)
        assert len(step3) == len(step2)  # Mocked = all healthy

        # Step 4: Proximity
        result = rank_by_proximity(step3)
        assert result["proximity_status"] == "unavailable"
        assert len(result["partners"]) > 0
