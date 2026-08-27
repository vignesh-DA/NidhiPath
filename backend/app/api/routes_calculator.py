"""
API Routes — Financial Calculator (Module 2)

POST /api/v1/calculate-emi
    Accepts scheme + amount + months, returns EMI breakdown with cap transparency.
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.modules.module2_calculator.emi import calculate_emi, EmiBreakdown


router = APIRouter()


class EmiRequest(BaseModel):
    """Request body for EMI calculation."""
    scheme_id: str = Field(..., description="Scheme identifier (from Module 1 output)")
    requested_amount: float = Field(..., gt=0, description="Loan amount requested in ₹")
    requested_months: int = Field(..., gt=0, description="Repayment tenure in months")

    # Scheme-owned values (passed through from Module 1 output)
    interest_rate_pct: float = Field(..., ge=0, description="Beneficiary interest rate (annual %)")
    max_loan_amount: Optional[float] = Field(None, description="Scheme max loan limit")
    project_cost: float = Field(..., gt=0, description="Estimated project cost in ₹")
    project_cost_coverage_pct: float = Field(90.0, description="% of cost scheme covers")
    tenure_years: Optional[float] = Field(None, description="Max tenure in years")
    moratorium_months: Optional[int] = Field(None, description="Moratorium months (null=0)")
    include_schedule: bool = Field(False, description="Include month-by-month amortization?")


@router.post("/calculate-emi", response_model=EmiBreakdown)
async def calculate_emi_endpoint(request: EmiRequest):
    """
    Financial Calculator — EMI with scheme-enforced caps.

    Pure math, zero LLM, <10ms response time.
    Interest rate is scheme-owned, NEVER user-editable.

    Explicit assumption stated in response:
        Interest does NOT accrue during moratorium period.
    """
    return calculate_emi(
        scheme_id=request.scheme_id,
        requested_amount=request.requested_amount,
        requested_months=request.requested_months,
        interest_rate_pct=request.interest_rate_pct,
        max_loan_amount=request.max_loan_amount,
        project_cost=request.project_cost,
        project_cost_coverage_pct=request.project_cost_coverage_pct,
        tenure_years=request.tenure_years,
        moratorium_months=request.moratorium_months,
        include_schedule=request.include_schedule,
    )
