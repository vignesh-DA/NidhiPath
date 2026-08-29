"""
Module 3 — Eligibility Filter (Step 2 of 4)

SCA/RRB → hard state match (partner.state = user.state).
    SCAs are state-bound by charter — no fuzzy proximity.
    RRBs are named by state and operate regionally — same state logic applies.

PSB/NBFC-MFI/Cooperative/SFB/Other → nationally eligible, no state constraint.
"""

from typing import Optional

# Partner types that are state-bound
STATE_BOUND_TYPES = {"SCA", "RRB"}

# Partner types that are nationally eligible
NATIONAL_TYPES = {"PSB", "NBFC-MFI", "COOPERATIVE", "SFB", "OTHER"}


def filter_by_eligibility(
    partners: list[dict],
    user_state: Optional[str] = None,
) -> list[dict]:
    """
    Step 2: Eligibility filter.

    SCA partners: hard state match against user's state.
    All other types: nationally eligible, always pass.

    Args:
        partners: Pre-filtered partner list (from Step 1 capability filter)
        user_state: User's state (e.g., "Karnataka"). If None, SCAs are excluded.

    Returns:
        List of eligible partner records
    """
    eligible = []

    for partner in partners:
        partner_type = partner.get("partner_type", "").strip().upper()

        if partner_type in STATE_BOUND_TYPES:
            # SCA — hard state match, no fuzzy proximity
            if user_state is None:
                continue  # Can't match SCA without knowing user's state

            partner_state = partner.get("state", "").strip().lower()
            if partner_state == user_state.strip().lower():
                eligible.append(partner)
        else:
            # PSB, RRB, NBFC-MFI, etc. — nationally eligible
            eligible.append(partner)

    return eligible
