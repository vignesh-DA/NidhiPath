"""
Module 2 — Financial Calculator (EMI Engine)

Pure math, zero LLM dependency. Unit-testable standalone.

Formula:
    EMI = P × r × (1+r)^n / ((1+r)^n − 1)
    r = interest_rate_pct.beneficiary / 12 / 100  (scheme-owned, NEVER user-editable)
    P = min(user_requested_amount, max_loan_amount, project_cost × project_cost_coverage_pct)
    n = min(user_requested_months, tenure_years × 12)

Payment cadence (scheme-owned, like the interest rate):
    NSFDC's Micro Finance Scheme officially "repaid in quarterly instalments
    within 4 years" (verified from the live NSFDC scheme page). Quarterly
    cadence is applied automatically for that scheme (see
    resolve_payment_frequency); every other scheme uses standard monthly
    installments. Whenever a result is shown on monthly cadence while NSFDC's
    official structure is quarterly, the assumption_note MUST say so
    explicitly — silence on this is the one failure mode to avoid.
Moratorium:
    EMI payments begin at month moratorium_months + 1.

Explicit documented assumption:
    Interest does NOT accrue during moratorium. Source data doesn't specify
    either way — this is our documented choice. Must be stated in UI, not hidden.

Null handling:
    - max_loan_amount: null → derive cap from project_cost × project_cost_coverage_pct
    - moratorium_months: null → treat as 0
"""

import math
from typing import Literal, Optional
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
    payment_frequency: Literal["monthly", "quarterly"] = Field(
        "monthly", description="Installment cadence — scheme-owned for NSFDC schemes"
    )


class EmiBreakdown(BaseModel):
    """Detailed EMI calculation result."""
    scheme_id: str

    # Effective values (after scheme cap enforcement)
    effective_loan_amount: float  # P — actual disbursable amount
    effective_tenure_months: int  # n — actual repayment months
    effective_interest_rate_annual: float  # annual % (for display)
    effective_interest_rate_monthly: float  # r — monthly decimal (for transparency)
    effective_interest_rate_periodic: float = 0.0  # r per installment period (decimal)
    installments_per_year: int = 12  # 12 = monthly, 4 = quarterly
    payment_frequency: str = "monthly"  # "monthly" | "quarterly"

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


# ─── Payment Cadence Resolver (scheme-owned, like the interest rate) ─────────

# NSFDC's Micro Finance Scheme officially "repaid in quarterly instalments
# within 4 years" (verified from the live NSFDC scheme page). Quarterly
# cadence applies automatically to this scheme; everything else stays monthly.
QUARTERLY_SCHEME_IDS = frozenset({"nsfdc-mfs-001", "nsfdc_mfs_001", "nsfdcmfs001"})
QUARTERLY_SCHEME_NAME_KEYWORDS = ("micro finance", "micro-finance")


def resolve_payment_frequency(scheme_id: str, scheme_name: str = "") -> str:
    """
    Resolve the scheme-owned repayment cadence. Pure function — no I/O.

    Returns "quarterly" for NSFDC's Micro Finance Scheme (matched by id or
    name keyword), "monthly" for everything else.
    """
    sid = (scheme_id or "").lower().replace("-", "").replace("_", "").strip()
    if sid and sid in {s.replace("-", "").replace("_", "") for s in QUARTERLY_SCHEME_IDS}:
        return "quarterly"
    name = (scheme_name or "").lower()
    if any(kw in name for kw in QUARTERLY_SCHEME_NAME_KEYWORDS):
        return "quarterly"
    return "monthly"


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
    payment_frequency: Literal["monthly", "quarterly"] = "monthly",
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
        payment_frequency: Installment cadence. Scheme-owned for NSFDC schemes —
            resolved via resolve_payment_frequency() (Micro Finance Scheme →
            "quarterly"). Unknown/welfare schemes default to "monthly".

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

    # ── Step 2.5: Resolve payment cadence ──
    if payment_frequency not in ("monthly", "quarterly"):
        raise ValueError(
            f"payment_frequency must be 'monthly' or 'quarterly', got '{payment_frequency}'"
        )
    payment_frequency = payment_frequency.lower()

    installments_per_year = 4 if payment_frequency == "quarterly" else 12
    months_per_period = 3 if payment_frequency == "quarterly" else 1

    if payment_frequency == "quarterly":
        caps_applied.append(
            "Quarterly repayment cadence applied: one installment every 3 months "
            "(NSFDC Micro Finance Scheme officially repays in quarterly installments)"
        )

    # ── Step 3: Calculate periodic interest rate (decimal) ──
    periodic_rate = interest_rate_pct / installments_per_year / 100
    r = interest_rate_pct / 12 / 100  # monthly-equivalent, kept for backward compat

    # ── Step 4: Number of installments ──
    # Monthly: one installment per month. Quarterly: months rounded UP to
    # whole quarters (a partial quarter still ends with a full installment).
    n_installments = math.ceil(effective_months / months_per_period)

    actual_moratorium = moratorium_months if moratorium_months is not None else 0
    if payment_frequency == "quarterly":
        # Moratorium rounded up to whole quarters — installments land on
        # quarter boundaries only.
        actual_moratorium = math.ceil(actual_moratorium / 3) * 3

    # ── Step 5: Calculate installment amount ──
    # Installment = P × r × (1+r)^n / ((1+r)^n − 1)   (r = periodic rate)
    if periodic_rate == 0:
        installment = effective_loan / n_installments
    else:
        compound = (1 + periodic_rate) ** n_installments
        installment = effective_loan * periodic_rate * compound / (compound - 1)

    installment = round(installment, 2)

    # ── Step 6: Totals ──
    total_payment = round(installment * n_installments, 2)
    total_interest = round(total_payment - effective_loan, 2)

    # ── Step 7: Timing ──
    first_emi_month = actual_moratorium + months_per_period
    total_duration = actual_moratorium + n_installments * months_per_period

    # ── Step 8: Assumption note — always explicit, never silent ──
    if payment_frequency == "quarterly":
        assumption_note = (
            f"Repayment calculated on QUARTERLY cadence: {n_installments} quarterly "
            f"installments at {interest_rate_pct}% p.a. compounded quarterly. "
            "Interest does NOT accrue during the moratorium period — documented "
            "assumption (source data does not specify either way). Matches NSFDC's "
            "official Micro Finance Scheme repayment structure (repaid in quarterly "
            "installments within 4 years)."
        )
    else:
        assumption_note = (
            "Interest does NOT accrue during the moratorium period — documented "
            "assumption (source data does not specify either way). "
            "Documented limitation: this schedule uses monthly installments with "
            "monthly compounding. NSFDC's Micro Finance Scheme officially repays in "
            "QUARTERLY installments within 4 years — that scheme is switched to "
            "quarterly cadence automatically when selected; every other scheme here "
            "is shown on monthly cadence."
        )

    # ── Step 9: Amortization schedule (optional) ──
    schedule: list[dict] = []
    if include_schedule:
        balance = effective_loan
        moratorium_periods = actual_moratorium // months_per_period
        total_periods = moratorium_periods + n_installments
        for period_num in range(1, total_periods + 1):
            month_num = period_num * months_per_period
            if period_num <= moratorium_periods:
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
                if periodic_rate == 0:
                    interest_component = 0
                    principal_component = installment
                else:
                    interest_component = round(balance * periodic_rate, 2)
                    principal_component = round(installment - interest_component, 2)

                balance = round(balance - principal_component, 2)

                # Fix floating point on last period
                if period_num == total_periods:
                    principal_component = round(principal_component + balance, 2)
                    balance = 0

                schedule.append({
                    "month": month_num,
                    "type": "repayment",
                    "emi": installment,
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
        effective_interest_rate_periodic=round(periodic_rate, 8),
        installments_per_year=installments_per_year,
        payment_frequency=payment_frequency,
        emi_amount=installment,
        total_payment=total_payment,
        total_interest=total_interest,
        moratorium_months=actual_moratorium,
        first_emi_month=first_emi_month,
        total_duration_months=total_duration,
        caps_applied=caps_applied,
        assumption_note=assumption_note,
        schedule=schedule,
    )
