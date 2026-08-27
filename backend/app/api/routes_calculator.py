"""
API Routes — Financial Calculator (Module 2)

POST /api/v1/calculate-emi
    Accepts scheme_id + user-specific inputs, returns EMI breakdown with
    cap transparency.

Integrity rule (non-negotiable): the interest rate is SCHEME-OWNED and
NEVER user-editable. When scheme_id matches a known NSFDC scheme, all
scheme-owned parameters (rate, max loan, coverage %, tenure, moratorium)
are resolved SERVER-SIDE from the authoritative record. Client-supplied
values for those fields are accepted for backward compatibility but are
OVERRIDDEN whenever the scheme resolves — a tampered client cannot buy a
cheaper rate.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.module1_recommender.credit_engine import load_nsfdc_schemes
from app.modules.module2_calculator.emi import calculate_emi, EmiBreakdown


router = APIRouter()


class EmiRequest(BaseModel):
    """Request body for EMI calculation.

    User-specific inputs (required):
        scheme_id, requested_amount, requested_months, project_cost

    Scheme-owned inputs (optional — resolved server-side when scheme_id
    matches a known NSFDC scheme; used only as fallback otherwise):
        interest_rate_pct, max_loan_amount, project_cost_coverage_pct,
        tenure_years, moratorium_months
    """
    scheme_id: str = Field(..., description="Scheme identifier (from Module 1 output)")
    requested_amount: float = Field(..., gt=0, description="Loan amount requested in ₹")
    requested_months: int = Field(..., gt=0, description="Repayment tenure in months")
    project_cost: float = Field(..., gt=0, description="User's estimated project/education cost in ₹")
    include_schedule: bool = Field(False, description="Include month-by-month amortization?")

    # Scheme-owned values — optional; server resolves them from scheme_id.
    interest_rate_pct: Optional[float] = Field(None, ge=0, description="Ignored when scheme resolves server-side")
    max_loan_amount: Optional[float] = Field(None, description="Ignored when scheme resolves server-side")
    project_cost_coverage_pct: Optional[float] = Field(None, description="Ignored when scheme resolves server-side")
    tenure_years: Optional[float] = Field(None, description="Ignored when scheme resolves server-side")
    moratorium_months: Optional[int] = Field(None, description="Ignored when scheme resolves server-side")


class EmiResponse(EmiBreakdown):
    """EMI breakdown plus provenance of the scheme parameters used."""
    scheme_resolved: bool = Field(False, description="Were scheme params resolved server-side from scheme_id?")
    scheme_name: Optional[str] = None
    resolution_note: str = ""


def _normalize_id(sid: str) -> str:
    return sid.lower().replace("-", "").replace("_", "").strip()


def _resolve_scheme(scheme_id: str) -> tuple[Optional[dict], bool]:
    """Look up a scheme by id in the authoritative NSFDC record set."""
    try:
        schemes = load_nsfdc_schemes()
    except FileNotFoundError:
        return None, False
    target = _normalize_id(scheme_id)
    for scheme in schemes:
        sid = _normalize_id(str(scheme.get("scheme_id", "")))
        name = _normalize_id(str(scheme.get("scheme_name", "")))
        if sid == target or target in sid or (len(target) > 3 and target in name):
            return scheme, True
    return None, False


@router.post("/calculate-emi", response_model=EmiResponse)
async def calculate_emi_endpoint(request: EmiRequest):
    """
    Financial Calculator — EMI with scheme-enforced caps.

    Pure math, zero LLM, <10ms response time.
    Interest rate is scheme-owned, NEVER user-editable: when scheme_id
    matches an NSFDC record, rate/limits/tenure/moratorium are taken from
    that record server-side, regardless of what the client sent.

    Explicit assumption stated in response:
        Interest does NOT accrue during moratorium period.
    """
    scheme, resolved = _resolve_scheme(request.scheme_id)

    if resolved and scheme:
        rate = scheme.get("interest_rate_pct", {})
        interest_rate = float(rate.get("beneficiary", 0)) if isinstance(rate, dict) else float(rate or 0)
        max_loan = scheme.get("max_loan_amount")
        coverage = float(scheme.get("project_cost_coverage_pct", 90))
        tenure = scheme.get("tenure_years")
        moratorium = scheme.get("moratorium_months")
        scheme_name = scheme.get("scheme_name")
        note = (
            "Scheme-owned parameters (interest rate, max loan, coverage, tenure, "
            "moratorium) were resolved server-side from the authoritative NSFDC "
            "record. Client-supplied values for these fields were overridden."
        )
    else:
        # Fallback: scheme unknown (e.g., welfare-corpus calculator use).
        # Require the client to have supplied the minimum needed values.
        if request.interest_rate_pct is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Unknown scheme_id '{request.scheme_id}' and no interest_rate_pct "
                    "provided. Scheme-owned parameters must come from a known scheme."
                ),
            )
        interest_rate = request.interest_rate_pct
        max_loan = request.max_loan_amount
        coverage = request.project_cost_coverage_pct if request.project_cost_coverage_pct is not None else 90.0
        tenure = request.tenure_years
        moratorium = request.moratorium_months
        scheme_name = None
        note = (
            "scheme_id did not match an NSFDC record; client-supplied scheme "
            "parameters were used as-is."
        )

    breakdown = calculate_emi(
        scheme_id=request.scheme_id,
        requested_amount=request.requested_amount,
        requested_months=request.requested_months,
        interest_rate_pct=interest_rate,
        max_loan_amount=max_loan,
        project_cost=request.project_cost,
        project_cost_coverage_pct=coverage,
        tenure_years=tenure,
        moratorium_months=moratorium,
        include_schedule=request.include_schedule,
    )

    return EmiResponse(
        **breakdown.model_dump(),
        scheme_resolved=resolved,
        scheme_name=scheme_name,
        resolution_note=note,
    )