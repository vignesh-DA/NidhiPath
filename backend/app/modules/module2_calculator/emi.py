"""
Module 2 — Financial Calculator (EMI Engine)

Pure math, zero LLM dependency. Unit-testable standalone.

Formula:
    EMI = P × r × (1+r)^n / ((1+r)^n − 1)
    r = interest_rate_pct.beneficiary / 12 / 100  (scheme-owned, NEVER user-editable)
    P = min(user_requested_amount, max_loan_amount, project_cost × project_cost_coverage_pct)
    n = min(user_requested_months, tenure_years × 12)

Moratorium:
    EMI payments begin at month moratorium_months + 1.

Explicit documented assumption:
    Interest does NOT accrue during moratorium. Source data doesn't specify
    either way — this is our documented choice. Must be stated in UI, not hidden.

Null handling:
    - max_loan_amount: null → derive cap from project_cost × project_cost_coverage_pct
    - moratorium_months: null → treat as 0
"""

from typing import Optional
from pydantic import BaseModel, Field


# ─── Models ──────────────────────────────────────────────────────────────────

class EmiInput(BaseModel):
    """Input for EMI calculation."""
    scheme_id: str = Field(..., description="Scheme identifier")
    requested_amount: float = Field(..., gt=0, description="Loan amount requested in ₹")
    requested_months: int = Field(..., gt=0, description="Repayment tenure requested in months")

    # Scheme-owned values (from Module 1 output, not user-editable)
    interest_rate_pct: float = Field(..., ge=0, description="Annual interest rate (beneficiary) in %")
    max_loan_amount: Optional[float] = Field(None, description="Scheme's max loan limit in ₹ (null = derive from cost)")
    project_cost: float = Field(..., gt=0, description="Estimated project cost in ₹")
    project_cost_coverage_pct: float = Field(90.0, gt=0, le=100, description="% of project cost the scheme covers")
    tenure_years: Optional[float] = Field(None, description="Maximum tenure in years")
    moratorium_months: Optional[int] = Field(None, ge=0, description="Moratorium period in months (null = 0)")


class EmiBreakdown(BaseModel):
    """Detailed EMI calculation result."""
    scheme_id: str

    # Effective values (after scheme cap enforcement)
    effective_loan_amount: float  # P — actual disbursable amount
    effective_tenure_months: int  # n — actual repayment months
    effective_interest_rate_annual: float  # annual % (for display)
    effective_interest_rate_monthly: float  # r — monthly decimal (for transparency)

    # EMI result
    emi_amount: float  # Monthly EMI in ₹
    total_payment: float  # EMI × n
    total_interest: float  # total_payment - effective_loan_amount

    # Moratorium
    moratorium_months: int
    first_emi_month: int  # moratorium_months + 1
    total_duration_months: int  # moratorium + repayment

    # Cap enforcement transparency
    caps_applied: list[str]  # Human-readable list of which caps kicked in

    # Documented assumption
    assumption_note: str = (
        "Interest does NOT accrue during the moratorium period. "
        "This is our documented assumption — source data does not specify either way."
    )

    # Amortization schedule (optional, for UI display)
    schedule: list[dict] = Field(default_factory=list, description="Month-by-month repayment schedule")


# ─── Core Engine ─────────────────────────────────────────────────────────────

def calculate_emi(
    scheme_id: str,
    requested_amount: float,
    requested_months: int,
    interest_rate_pct: float,
    max_loan_amount: Optional[float],
    project_cost: float,
    project_cost_coverage_pct: float = 90.0,
    tenure_years: Optional[float] = None,
    moratorium_months: Optional[int] = None,
    include_schedule: bool = False,
) -> EmiBreakdown:
    """
    Calculate EMI with scheme-enforced caps.

    This is pure math — no external dependencies, no LLM, no database calls.

    Args:
        scheme_id: Identifier for the scheme
        requested_amount: User's requested loan amount in ₹
        requested_months: User's requested tenure in months
        interest_rate_pct: Annual interest rate (beneficiary) — scheme-owned, NEVER user-editable
        max_loan_amount: Scheme's max loan limit (None = derive from cost × coverage)
        project_cost: Estimated project/education cost in ₹
        project_cost_coverage_pct: % of project cost the scheme covers
        tenure_years: Max tenure in years (None = no tenure cap)
        moratorium_months: Moratorium period in months (None = 0)
        include_schedule: Whether to include month-by-month amortization schedule

    Returns:
        EmiBreakdown with all calculated values and transparency info
    """
    caps_applied: list[str] = []

    # ── Step 1: Calculate effective loan amount P ──
    # P = min(user_requested_amount, max_loan_amount, project_cost × coverage%)
    cost_derived_cap = project_cost * (project_cost_coverage_pct / 100)

    candidates = [requested_amount]

    if max_loan_amount is not None:
        candidates.append(max_loan_amount)
    else:
        # max_loan_amount is null → use cost-derived cap as the binding limit
        caps_applied.append(
            f"No explicit loan limit — derived cap from project cost: "
            f"₹{project_cost:,.0f} × {project_cost_coverage_pct}% = ₹{cost_derived_cap:,.0f}"
        )

    candidates.append(cost_derived_cap)

    effective_loan = min(candidates)

    # Track which cap bound
    if effective_loan < requested_amount:
        if max_loan_amount is not None and effective_loan == max_loan_amount:
            caps_applied.append(
                f"Requested ₹{requested_amount:,.0f} capped to scheme max: ₹{max_loan_amount:,.0f}"
            )
        elif effective_loan == cost_derived_cap:
            caps_applied.append(
                f"Requested ₹{requested_amount:,.0f} capped to {project_cost_coverage_pct}% of "
                f"project cost: ₹{cost_derived_cap:,.0f}"
            )

    # ── Step 2: Calculate effective tenure n ──
    max_months = None
    if tenure_years is not None:
        max_months = int(tenure_years * 12)

    if max_months is not None:
        effective_months = min(requested_months, max_months)
        if effective_months < requested_months:
            caps_applied.append(
                f"Requested {requested_months} months capped to scheme max: "
                f"{max_months} months ({tenure_years} years)"
            )
    else:
        effective_months = requested_months

    # ── Step 3: Calculate r (monthly interest rate as decimal) ──
    r = interest_rate_pct / 12 / 100

    # ── Step 4: Calculate EMI ──
    if r == 0:
        # Zero interest = simple division
        emi = effective_loan / effective_months
    else:
        # EMI = P × r × (1+r)^n / ((1+r)^n − 1)
        compound = (1 + r) ** effective_months
        emi = effective_loan * r * compound / (compound - 1)

    emi = round(emi, 2)

    # ── Step 5: Totals ──
    total_payment = round(emi * effective_months, 2)
    total_interest = round(total_payment - effective_loan, 2)

    # ── Step 6: Moratorium ──
    actual_moratorium = moratorium_months if moratorium_months is not None else 0
    first_emi_month = actual_moratorium + 1
    total_duration = actual_moratorium + effective_months

    # ── Step 7: Amortization schedule (optional) ──
    schedule: list[dict] = []
    if include_schedule:
        balance = effective_loan
        for month_num in range(1, total_duration + 1):
            if month_num <= actual_moratorium:
                # Moratorium period — no payment, no interest accrual (documented assumption)
                schedule.append({
                    "month": month_num,
                    "type": "moratorium",
                    "emi": 0,
                    "principal": 0,
                    "interest": 0,
                    "balance": round(balance, 2),
                })
            else:
                if r == 0:
                    interest_component = 0
                    principal_component = emi
                else:
                    interest_component = round(balance * r, 2)
                    principal_component = round(emi - interest_component, 2)

                balance = round(balance - principal_component, 2)

                # Fix floating point on last month
                if month_num == total_duration:
                    principal_component = round(principal_component + balance, 2)
                    balance = 0

                schedule.append({
                    "month": month_num,
                    "type": "repayment",
                    "emi": emi,
                    "principal": principal_component,
                    "interest": interest_component,
                    "balance": max(balance, 0),
                })

    return EmiBreakdown(
        scheme_id=scheme_id,
        effective_loan_amount=round(effective_loan, 2),
        effective_tenure_months=effective_months,
        effective_interest_rate_annual=interest_rate_pct,
        effective_interest_rate_monthly=round(r, 8),
        emi_amount=emi,
        total_payment=total_payment,
        total_interest=total_interest,
        moratorium_months=actual_moratorium,
        first_emi_month=first_emi_month,
        total_duration_months=total_duration,
        caps_applied=caps_applied,
        schedule=schedule,
    )
