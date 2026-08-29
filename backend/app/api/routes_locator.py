"""
API Routes — Partner Locator (Module 3)

POST /api/v1/locate-partners
    Pipeline: capability → eligibility → health → proximity (stub)
    Exact query order is non-negotiable — proximity is deliberately last.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.module3_locator.capability_filter import filter_by_capability
from app.modules.module3_locator.eligibility_filter import filter_by_eligibility
from app.modules.module3_locator.health_filter import filter_by_health
from app.modules.module3_locator.proximity import rank_by_proximity


router = APIRouter()


class LocateRequest(BaseModel):
    """Request body for partner location."""
    scheme_channel_partners: list[str] = Field(
        ...,
        description='Partner types from the matched scheme (e.g., ["SCA", "PSB", "RRB"])',
    )
    user_state: Optional[str] = Field(
        None,
        description="User's state for SCA/RRB eligibility filter",
    )
    user_district: Optional[str] = Field(
        None,
        description="User's district for proximity tier ranking",
    )
    user_lat: Optional[float] = Field(None, description="User's latitude")
    user_lon: Optional[float] = Field(None, description="User's longitude")


class LocateResponse(BaseModel):
    """Response with filtered and ranked partners."""
    partners: list[dict] = []
    pipeline_summary: dict = {}
    proximity_status: str = "unavailable"
    proximity_note: str = ""
    known_gaps: list[str] = []
    total_results: int = 0


@router.post("/locate-partners", response_model=LocateResponse)
async def locate_partners(request: LocateRequest):
    """
    Partner Locator — 4-step pipeline.

    1. Capability filter: partner_type IN scheme.channel_partners[]
    2. Eligibility filter: SCA→state match, others→national
    3. Health filter: deprioritize (never exclude) unhealthy partners
    4. Proximity rank: STUB (blocked on geocoding)

    Query order is non-negotiable and follows the verified architecture.
    """
    # Step 1: Capability filter
    try:
        step1 = filter_by_capability(request.scheme_channel_partners)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    step1_count = len(step1)

    # Step 2: Eligibility filter
    step2 = filter_by_eligibility(step1, request.user_state)
    step2_count = len(step2)

    # Step 3: Health filter
    step3 = filter_by_health(step2)
    step3_count = len(step3)

    # Step 4: Proximity ranking (tier-based)
    result = rank_by_proximity(
        step3,
        user_state=request.user_state,
        user_district=request.user_district,
        user_lat=request.user_lat,
        user_lon=request.user_lon,
    )

    return LocateResponse(
        partners=result["partners"],
        pipeline_summary={
            "step1_capability": {
                "input": "all partners",
                "filter": f"partner_type IN {request.scheme_channel_partners}",
                "output": step1_count,
            },
            "step2_eligibility": {
                "input": step1_count,
                "filter": f"SCA→state='{request.user_state}', others→national",
                "output": step2_count,
            },
            "step3_health": {
                "input": step2_count,
                "filter": "deprioritize (not exclude) above-threshold NPA/utilization",
                "output": step3_count,
            },
            "step4_proximity": {
                "input": step3_count,
                "status": result["proximity_status"],
                "ranking": result.get("ranking_summary", {}),
            },
        },
        proximity_status=result["proximity_status"],
        proximity_note=result["proximity_note"],
        known_gaps=result["known_gaps"],
        total_results=len(result["partners"]),
    )
