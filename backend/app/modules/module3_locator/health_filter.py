"""
Module 3 — Health Filter (Step 3 of 4)

Query mocked partner_health(partner_id, npa_ratio, utilization_pct) table.

DEPRIORITIZE, do not hard-exclude above-threshold partners.
Hard exclusion risks a zero-result state in the demo.

In production, this uses a real NPA/utilization feed via formal NSFDC
data-sharing agreement. For the hackathon, data is mocked.
"""

from typing import Optional
from pydantic import BaseModel

# ─── Thresholds ──────────────────────────────────────────────────────────────

# Partners with NPA ratio above this are deprioritized (not excluded)
NPA_THRESHOLD = 10.0  # %

# Partners with utilization above this are deprioritized (not excluded)
UTILIZATION_THRESHOLD = 90.0  # %


# ─── Mocked Health Data ─────────────────────────────────────────────────────
# In production: replaced by real database table partner_health
# For demo: returns moderate/healthy values for most partners

class PartnerHealth(BaseModel):
    """Health metrics for a channel partner."""
    partner_id: str
    npa_ratio: float = 5.0  # % Non-Performing Assets
    utilization_pct: float = 60.0  # % of sanctioned fund utilized
    is_healthy: bool = True
    health_note: str = ""


def get_partner_health(partner_id: str) -> PartnerHealth:
    """
    Get health metrics for a partner.

    Currently mocked — returns moderate values.
    Production: query partner_health table in Supabase.
    """
    # Mocked: all partners are moderately healthy
    # In a real system, this queries the partner_health table
    return PartnerHealth(
        partner_id=partner_id,
        npa_ratio=5.0,
        utilization_pct=60.0,
        is_healthy=True,
        health_note="Health data is mocked for demo. "
                    "Production requires real NPA/utilization feed via NSFDC data-sharing agreement.",
    )


# ─── Filter ──────────────────────────────────────────────────────────────────

def filter_by_health(
    partners: list[dict],
    npa_threshold: float = NPA_THRESHOLD,
    utilization_threshold: float = UTILIZATION_THRESHOLD,
) -> list[dict]:
    """
    Step 3: Health filter.

    DEPRIORITIZE (never hard-exclude) partners above NPA/utilization thresholds.
    Adds health_status and health_priority fields to each partner record.

    Args:
        partners: Pre-filtered partner list (from Step 2 eligibility filter)
        npa_threshold: NPA ratio threshold (%)
        utilization_threshold: Utilization threshold (%)

    Returns:
        List of partners with health metadata, sorted: healthy first, then deprioritized
    """
    healthy = []
    deprioritized = []

    for partner in partners:
        partner_id = partner.get("partner_id", partner.get("id", "unknown"))
        health = get_partner_health(partner_id)

        # Enrich partner record with health data
        enriched = {
            **partner,
            "health": {
                "npa_ratio": health.npa_ratio,
                "utilization_pct": health.utilization_pct,
                "is_healthy": health.is_healthy,
                "note": health.health_note,
            },
        }

        if health.npa_ratio > npa_threshold or health.utilization_pct > utilization_threshold:
            enriched["health"]["is_healthy"] = False
            enriched["health"]["deprioritized_reason"] = []
            if health.npa_ratio > npa_threshold:
                enriched["health"]["deprioritized_reason"].append(
                    f"NPA ratio ({health.npa_ratio}%) exceeds threshold ({npa_threshold}%)"
                )
            if health.utilization_pct > utilization_threshold:
                enriched["health"]["deprioritized_reason"].append(
                    f"Utilization ({health.utilization_pct}%) exceeds threshold ({utilization_threshold}%)"
                )
            deprioritized.append(enriched)
        else:
            healthy.append(enriched)

    # Healthy first, then deprioritized — never excluded
    return healthy + deprioritized
