"""
Module 3 — Proximity Ranking (Step 4 of 4)

BLOCKED on geocoding + IFSC join. Build this last.

In production: PostGIS `<->` KNN on a `geom` column.
For the demo: returns partners unsorted by distance with a status message.

Known permanent gap:
    NBFC-MFIs are absent from IFSC.csv entirely — they will always resolve
    to a single HQ pin, never real branch-level proximity.
    This must be disclosed in the UI, not hidden.
"""

from typing import Optional


def rank_by_proximity(
    partners: list[dict],
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
) -> dict:
    """
    Step 4: Proximity ranking (STUB).

    Currently blocked — returns partners unsorted with status info.
    Production: PostGIS KNN query against geocoded partner locations.

    Args:
        partners: Pre-filtered partner list (from Step 3 health filter)
        user_lat: User's latitude
        user_lon: User's longitude

    Returns:
        Dict with partners list and proximity status
    """
    return {
        "partners": partners,
        "proximity_status": "unavailable",
        "proximity_note": (
            "Proximity ranking is not yet available. Partners are listed without "
            "distance ordering. Full geocoding integration is pending."
        ),
        "known_gaps": [
            "NBFC-MFIs are absent from IFSC.csv — they resolve to HQ location only, "
            "never real branch-level proximity.",
        ],
        "user_location": {
            "latitude": user_lat,
            "longitude": user_lon,
            "provided": user_lat is not None and user_lon is not None,
        },
    }
