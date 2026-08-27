"""
API Routes — Scheme Recommender (Module 1)

POST /api/v1/recommend
    Accepts user intake fields, returns primary (NSFDC) + secondary (welfare) recommendations.
    Two-tier recommendation, NEVER merged into one ranked list.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.module1_recommender.credit_engine import (
    filter_and_rank_credit_schemes,
    CreditRecommendationResult,
    ProjectType,
    EducationStatus,
)
from app.modules.module1_recommender.welfare_engine import (
    filter_welfare_schemes,
    WelfareRecommendationResult,
)


router = APIRouter()


class RecommendRequest(BaseModel):
    """Request body for scheme recommendation."""
    estimated_cost: float = Field(..., gt=0, description="Estimated project/education cost in ₹")
    income_level: float = Field(..., ge=0, description="Annual family income in ₹")
    project_type: ProjectType = Field(..., description="Purpose: business_self_employment or education")
    education_status: Optional[EducationStatus] = Field(
        None, description="Required when project_type=education"
    )
    # Optional fields for welfare matching
    user_state: Optional[str] = Field(None, description="User's state (e.g., Karnataka)")
    caste_scope: Optional[list[str]] = Field(None, description='Caste categories (e.g., ["SC"])')


class RecommendResponse(BaseModel):
    """Combined response with primary (NSFDC) + secondary (welfare) recommendations."""
    primary: CreditRecommendationResult
    secondary: WelfareRecommendationResult
    meta: dict = {}


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_schemes(request: RecommendRequest):
    """
    Smart Scheme Recommender — takes basic user inputs and recommends schemes.

    Primary block: NSFDC ranked list (deterministic, exact, <100ms, zero LLM calls)
    Secondary block: Welfare corpus matches (approximate, clearly labeled as broader)

    Two-tier output is a non-negotiable architecture decision.
    """
    # Validate education path
    if request.project_type == ProjectType.EDUCATION and request.education_status is None:
        raise HTTPException(
            status_code=422,
            detail="education_status is required when project_type is 'education'. "
                   "Provide 'admission_secured' or 'currently_enrolled'."
        )

    # Module 1A — NSFDC credit schemes (deterministic)
    try:
        primary = filter_and_rank_credit_schemes(
            estimated_cost=request.estimated_cost,
            income_level=request.income_level,
            project_type=request.project_type.value,
            education_status=request.education_status.value if request.education_status else None,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Module 1B — Welfare schemes (approximate)
    try:
        secondary = filter_welfare_schemes(
            income_level=request.income_level,
            user_state=request.user_state,
            caste_scope=request.caste_scope,
        )
    except FileNotFoundError:
        # Welfare data not available — gracefully degrade
        secondary = WelfareRecommendationResult()

    return RecommendResponse(
        primary=primary,
        secondary=secondary,
        meta={
            "primary_source": "NSFDC credit schemes (5 records, deterministic match)",
            "secondary_source": "Welfare corpus (377 records, approximate match)",
            "note": "Primary results are exact rule-verified matches. "
                    "Secondary results are broader matches — verify with issuing authority.",
        },
    )
