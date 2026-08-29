"""
Tests for Module 3 — Partner Locator

Test cases cover:
    - Capability filtering by partner type
    - SCA + RRB state-bound eligibility (RRB is now state-filtered)
    - National eligibility for PSB/NBFC-MFI/etc.
    - Health deprioritization (not exclusion)
    - Proximity tier ranking (district → state → national)
    - Full pipeline integration
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
        "state": "",
        "contact": "+91-11-23345678",
    },
    {
        "partner_id": "rrb_karnataka",
        "partner_name": "Karnataka Grameena Bank",
        "partner_type": "RRB",
        "state": "Karnataka",
        "contact": "+91-80-22445678",
    },
    {
        "partner_id": "rrb_tamil_nadu",
        "partner_name": "Tamil Nadu Grama Bank",
        "partner_type": "RRB",
        "state": "Tamil Nadu",
        "contact": "+91-44-22445678",
    },
    {
        "partner_id": "nbfc_mfi_1",
        "partner_name": "Bandhan Financial Services",
        "partner_type": "NBFC-MFI",
        "state": "",
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

    def test_rrb_state_match(self):
        """RRBs should only match when user's state matches (core bug fix)."""
        result = filter_by_eligibility(TEST_PARTNERS, user_state="Karnataka")

        ids = {p["partner_id"] for p in result}
        assert "rrb_karnataka" in ids
        assert "rrb_tamil_nadu" not in ids

    def test_rrb_excluded_without_state(self):
        """RRBs should be excluded when no user state is provided."""
        result = filter_by_eligibility(TEST_PARTNERS, user_state=None)
        types = {p["partner_type"] for p in result}
        assert "RRB" not in types

    def test_sca_excluded_without_state(self):
        """SCAs should be excluded when no user state is provided."""
        result = filter_by_eligibility(TEST_PARTNERS, user_state=None)
        types = {p["partner_type"] for p in result}
        assert "SCA" not in types

    def test_national_always_eligible(self):
        """PSB, NBFC-MFI should always be eligible regardless of state."""
        result = filter_by_eligibility(TEST_PARTNERS, user_state="Kerala")
        national_types = {p["partner_type"] for p in result if p["partner_type"] not in ("SCA", "RRB")}
        assert "PSB" in national_types
        assert "NBFC-MFI" in national_types

    def test_rrb_no_longer_national(self):
        """RRB should NOT appear when user is from a different state."""
        result = filter_by_eligibility(TEST_PARTNERS, user_state="Kerala")
        rrb_ids = {p["partner_id"] for p in result if p["partner_type"] == "RRB"}
        # Neither Karnataka nor Tamil Nadu RRBs should appear for Kerala user
        assert len(rrb_ids) == 0


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


# ─── Step 4: Proximity Tier Ranking ─────────────────────────────────────────

class TestProximityRanking:
    def test_tier_ranking_with_state(self):
        """Partners with matching state get tier 2, national types get tier 3."""
        partners = [
            {"partner_id": "sca_1", "partner_type": "SCA", "state": "Karnataka"},
            {"partner_id": "psb_1", "partner_type": "PSB", "state": ""},
        ]
        result = rank_by_proximity(partners, user_state="Karnataka")

        assert result["proximity_status"] == "tier_ranking"
        assert result["partners"][0]["rank_tier"] == 2  # State match first
        assert result["partners"][1]["rank_tier"] == 3  # National last

    def test_tier_ranking_without_state(self):
        """Without user state, status should be 'unavailable'."""
        partners = [
            {"partner_id": "psb_1", "partner_type": "PSB", "state": ""},
        ]
        result = rank_by_proximity(partners, user_state=None)
        assert result["proximity_status"] == "unavailable"

    def test_district_match_tier_1(self):
        """Partners with matching district get tier 1 (highest priority)."""
        partners = [
            {"partner_id": "p1", "partner_type": "SCA", "state": "Karnataka", "district": "Bengaluru Urban"},
            {"partner_id": "p2", "partner_type": "SCA", "state": "Karnataka", "district": "Mysuru"},
        ]
        result = rank_by_proximity(partners, user_state="Karnataka", user_district="Bengaluru Urban")

        assert result["partners"][0]["partner_id"] == "p1"
        assert result["partners"][0]["rank_tier"] == 1  # District match
        assert result["partners"][1]["partner_id"] == "p2"
        assert result["partners"][1]["rank_tier"] == 2  # State match only

    def test_passes_through_all_partners(self):
        """All partners should be included in output."""
        result = rank_by_proximity(TEST_PARTNERS, user_state="Karnataka")
        assert len(result["partners"]) == len(TEST_PARTNERS)

    def test_ranking_summary_present(self):
        """Ranking summary should contain tier counts."""
        result = rank_by_proximity(TEST_PARTNERS, user_state="Karnataka")
        assert "ranking_summary" in result
        assert "tier1_district_match" in result["ranking_summary"]
        assert "tier2_state_match" in result["ranking_summary"]
        assert "tier3_national" in result["ranking_summary"]

    def test_discloses_nbfc_gap(self):
        """Must disclose the NBFC-MFI IFSC gap."""
        result = rank_by_proximity(TEST_PARTNERS, user_state="Karnataka")
        gaps_text = " ".join(result["known_gaps"])
        assert "NBFC-MFI" in gaps_text

    def test_location_label_assigned(self):
        """Every partner should get a location_label."""
        result = rank_by_proximity(TEST_PARTNERS, user_state="Karnataka")
        for p in result["partners"]:
            assert "location_label" in p
            assert p["location_label"] != ""


# ─── Full Pipeline Integration ──────────────────────────────────────────────

class TestFullPipeline:
    def test_end_to_end_karnataka_term_loan(self):
        """
        Real test case: Karnataka user, Term Loan (SCA+PSB+RRB).
        Should get Karnataka SCA + Karnataka RRB + all PSBs.
        Tamil Nadu SCA and RRB should be filtered out.
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
        assert "rrb_karnataka" in ids
        assert "rrb_tamil_nadu" not in ids
        assert "psb_sbi" in ids

        # Step 3: Health
        step3 = filter_by_health(step2)
        assert len(step3) == len(step2)  # Mocked = all healthy

        # Step 4: Proximity — tier-based ranking
        result = rank_by_proximity(step3, user_state="Karnataka")
        assert result["proximity_status"] == "tier_ranking"
        assert len(result["partners"]) > 0

        # State-bound partners should be tier 2, PSB should be tier 3
        for p in result["partners"]:
            if p["partner_type"] in ("SCA", "RRB"):
                assert p["rank_tier"] == 2  # State match
            elif p["partner_type"] == "PSB":
                assert p["rank_tier"] == 3  # National

    def test_end_to_end_no_state(self):
        """
        Without user state: SCAs and RRBs excluded, only national types remain.
        """
        step1 = filter_by_capability(
            scheme_channel_partners=["SCA", "PSB", "RRB", "NBFC-MFI"],
            partners=TEST_PARTNERS,
        )
        step2 = filter_by_eligibility(step1, user_state=None)
        types = {p["partner_type"] for p in step2}
        assert "SCA" not in types
        assert "RRB" not in types
        assert "PSB" in types
        assert "NBFC-MFI" in types
