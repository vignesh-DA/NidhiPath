"""
Module 3 — Proximity Ranking (Step 4 of 4)

3-tier ranking based on location match (no geocoding required):
    Tier 1: District match (partner.district == user.district)
    Tier 2: State match (partner.state == user.state)
    Tier 3: National (genuinely national types — PSB/NBFC-MFI/SFB/etc.)

In production: PostGIS `<->` KNN on a `geom` column.
For now: tier-based ranking using state/district string matching.

Known permanent gap:
    NBFC-MFIs are absent from IFSC.csv entirely — they will always resolve
    to a single HQ pin, never real branch-level proximity.
    This must be disclosed in the UI, not hidden.
"""

from typing import Optional


# Partner types that are genuinely national — no location specificity
NATIONAL_PARTNER_TYPES = {"PSB", "NBFC-MFI", "COOPERATIVE", "COOPERATIVE BANK",
                          "COOPERATIVE SOCIETY", "SFB", "OTHER", "OTHER AGENCY"}


def rank_by_proximity(
    partners: list[dict],
    user_state: Optional[str] = None,
    user_district: Optional[str] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
) -> dict:
    """
    Step 4: Proximity ranking via location tiers.

    Tier 1: District match → shown first (if district data exists)
    Tier 2: State match → shown second
    Tier 3: National partners → shown last, labeled "National — not location-specific"

    Args:
        partners: Pre-filtered partner list (from Step 3 health filter)
        user_state: User's state (e.g., "Karnataka")
        user_district: User's district (e.g., "Bengaluru Urban")
        user_lat: User's latitude (stored, not used for ranking yet)
        user_lon: User's longitude (stored, not used for ranking yet)

    Returns:
        Dict with ranked partners list and proximity metadata
    """
    tier1_district = []
    tier2_state = []
    tier3_national = []

    user_state_lower = user_state.strip().lower() if user_state else None
    user_district_lower = user_district.strip().lower() if user_district else None

    for partner in partners:
        partner_type = partner.get("partner_type", "").strip().upper()
        partner_state = partner.get("state", "").strip().lower()
        partner_district = partner.get("district", "").strip().lower()

        enriched = {**partner}

        if partner_type in NATIONAL_PARTNER_TYPES or not partner_state:
            # Genuinely national or no state data — Tier 3
            enriched["rank_tier"] = 3
            enriched["location_label"] = "National — not location-specific"
            tier3_national.append(enriched)
        elif user_district_lower and partner_district and partner_district == user_district_lower:
            # District match — Tier 1
            enriched["rank_tier"] = 1
            enriched["location_label"] = f"District match — {user_district}"
            tier1_district.append(enriched)
        elif user_state_lower and partner_state == user_state_lower:
            # State match — Tier 2
            enriched["rank_tier"] = 2
            enriched["location_label"] = f"State match — {user_state}"
            tier2_state.append(enriched)
        else:
            # State-bound partner but different state — should have been
            # filtered out by eligibility filter. Include as Tier 3 fallback.
            enriched["rank_tier"] = 3
            enriched["location_label"] = f"Other region — {partner.get('state', 'Unknown')}"
            tier3_national.append(enriched)

    ranked = tier1_district + tier2_state + tier3_national

    # Determine proximity status
    has_location = user_state is not None
    proximity_status = "tier_ranking" if has_location else "unavailable"

    return {
        "partners": ranked,
        "proximity_status": proximity_status,
        "proximity_note": (
            f"Ranked by location tier: {len(tier1_district)} district match, "
            f"{len(tier2_state)} state match, {len(tier3_national)} national. "
            "Full geocoding integration is pending."
            if has_location else
            "No user location provided. Partners listed without location ranking. "
            "Provide state to enable tier-based ranking."
        ),
        "ranking_summary": {
            "tier1_district_match": len(tier1_district),
            "tier2_state_match": len(tier2_state),
            "tier3_national": len(tier3_national),
        },
        "known_gaps": [
            "NBFC-MFIs are absent from IFSC.csv — they resolve to HQ location only, "
            "never real branch-level proximity.",
            "District-level matching requires district field in partner data (not yet populated for most partners).",
        ],
        "user_location": {
            "state": user_state,
            "district": user_district,
            "latitude": user_lat,
            "longitude": user_lon,
            "provided": has_location,
        },
    }
