"""
Module 1 — Welfare Scheme Filter Engine

Filters the 377-scheme welfare corpus (schemes_production_deduped.json).
This is the SECONDARY recommendation — clearly labeled as "related schemes
you may qualify for", broader/less-precise matches.

NEVER merge welfare results into the same ranked list as NSFDC credit schemes.
A user must always be able to tell which answer is exact (NSFDC) and which
is exploratory (welfare).

Filtering:
    1. issuing_state match OR central scheme
    2. income_criteria amount check (mind the {operator, amount} structure)
    3. caste_or_target_scope overlap

Known limitation:
    education_criteria is unstructured text — keyword match only until a
    structured extraction pass is done. Do NOT present this filter to the
    user as exact when it isn't.
"""

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─── Models ──────────────────────────────────────────────────────────────────

class WelfareSchemeMatch(BaseModel):
    """A matched welfare scheme with summary info."""
    scheme_id: str
    scheme_name: str
    issuing_state: str = ""  # null in JSON → empty string
    benefits: str = ""
    eligibility_summary: str = ""
    match_confidence: str = "approximate"  # Always approximate for welfare schemes
    match_reasons: list[str] = []


class WelfareRecommendationResult(BaseModel):
    """Output of the welfare scheme filter."""
    matches: list[WelfareSchemeMatch] = []
    total_matches: int = 0
    disclaimer: str = (
        "These are broader welfare schemes you may qualify for, identified by "
        "approximate matching on state, income, and target group criteria. "
        "Verify eligibility details directly with the issuing authority."
    )


# ─── Data Loader ─────────────────────────────────────────────────────────────

_welfare_cache: Optional[list[dict]] = None


def load_welfare_schemes(data_dir: Optional[Path] = None) -> list[dict]:
    """Load welfare schemes from JSON. Caches in-memory after first load."""
    global _welfare_cache
    if _welfare_cache is not None:
        return _welfare_cache

    if data_dir is None:
        from app.config import settings
        data_dir = settings.DATA_DIR

    path = data_dir / "staging" / "schemes_production_deduped.json"
    if not path.exists():
        raise FileNotFoundError(
            f"schemes_production_deduped.json not found at {path}. "
            f"Place your data file in data/staging/"
        )

    with open(path, "r", encoding="utf-8") as f:
        _welfare_cache = json.load(f)

    return _welfare_cache


def clear_welfare_cache():
    """Clear cached schemes — useful for testing."""
    global _welfare_cache
    _welfare_cache = None


# ─── Filter Helpers ──────────────────────────────────────────────────────────

def _matches_state(scheme: dict, user_state: Optional[str]) -> bool:
    """
    Check if scheme is available to user's state.
    Central schemes always match. State schemes match only if states align.
    """
    issuing_state = (scheme.get("issuing_state") or "").strip().lower()

    # Central schemes match everyone
    if issuing_state in ("central", "all india", "all_india", "india", ""):
        return True

    # If user didn't specify state, only return central schemes
    if user_state is None:
        return False

    return issuing_state == user_state.strip().lower()


def _check_income_criterion(criterion: dict, user_income: float) -> bool:
    """Check a single income criterion dict."""
    operator = criterion.get("operator", "less_than")
    amount = criterion.get("amount")

    if amount is None:
        return True

    amount = float(amount)

    if operator in ("less_than", "lt", "<"):
        return user_income < amount
    elif operator in ("less_than_or_equal", "lte", "<="):
        return user_income <= amount
    elif operator in ("greater_than", "gt", ">"):
        return user_income > amount
    elif operator in ("greater_than_or_equal", "gte", ">="):
        return user_income >= amount
    elif operator in ("equal", "eq", "=="):
        return user_income == amount
    elif operator in ("between",):
        max_amount = criterion.get("max_amount", float("inf"))
        return amount <= user_income <= float(max_amount)
    else:
        return True  # Unknown operator — include


def _matches_income(scheme: dict, user_income: float) -> bool:
    """
    Check income criteria.
    Real JSON has income_criteria as a LIST of criterion dicts.
    Also handles legacy dict/scalar/string formats.
    If no income criteria, assume the scheme is open to all income levels.
    """
    income_criteria = scheme.get("income_criteria")

    if not income_criteria:  # None or empty list
        return True

    # Real format: list of criterion dicts — user must satisfy ANY one
    if isinstance(income_criteria, list):
        if not income_criteria:
            return True
        # Filter to annual_family_income type only; others (e.g. assets) are irrelevant here
        income_items = [
            c for c in income_criteria
            if isinstance(c, dict) and c.get("type", "") in (
                "annual_family_income", "annual_income", ""
            )
        ] or income_criteria  # fallback: use all if none typed
        # User passes if they satisfy at least one income criterion
        return any(
            _check_income_criterion(c, user_income)
            for c in income_items
            if isinstance(c, dict)
        )

    # Legacy: single dict
    if isinstance(income_criteria, dict):
        return _check_income_criterion(income_criteria, user_income)

    # Legacy: simple numeric
    if isinstance(income_criteria, (int, float)):
        return user_income <= float(income_criteria)

    # Legacy: unparseable string — include and let user verify
    return True


def _matches_target_scope(scheme: dict, user_caste_scope: Optional[list[str]] = None) -> bool:
    """
    Check caste/target scope overlap.
    If user provides caste categories, check for overlap with scheme's target list.
    If scheme has no target restriction, it matches everyone.
    """
    target_scope = scheme.get("caste_or_target_scope", [])

    # No restriction = open to all
    if not target_scope:
        return True

    # Normalize to list
    if isinstance(target_scope, str):
        target_scope = [target_scope]

    # If user didn't specify, be inclusive (show the scheme)
    if user_caste_scope is None:
        return True

    # Check overlap
    target_lower = {t.strip().lower() for t in target_scope if t}
    user_lower = {c.strip().lower() for c in user_caste_scope if c}

    # Common aliases
    aliases = {
        "sc": {"sc", "scheduled caste", "scheduled castes"},
        "st": {"st", "scheduled tribe", "scheduled tribes"},
        "obc": {"obc", "other backward class", "other backward classes"},
        "general": {"general", "all"},
    }

    # Expand both sets with aliases
    expanded_target = set()
    for t in target_lower:
        expanded_target.add(t)
        for key, alias_set in aliases.items():
            if t in alias_set:
                expanded_target.update(alias_set)

    expanded_user = set()
    for c in user_lower:
        expanded_user.add(c)
        for key, alias_set in aliases.items():
            if c in alias_set:
                expanded_user.update(alias_set)

    return bool(expanded_target & expanded_user)


def _keyword_match_education(scheme: dict, education_keywords: Optional[list[str]] = None) -> bool:
    """
    Keyword match on unstructured education_criteria text.
    THIS IS APPROXIMATE — do not present to user as exact.
    """
    if education_keywords is None:
        return True

    criteria_raw = scheme.get("education_criteria", "")
    # Real JSON: list of strings — join them for keyword search
    if isinstance(criteria_raw, list):
        criteria_text = " ".join(str(c) for c in criteria_raw)
    else:
        criteria_text = str(criteria_raw or "")

    if not criteria_text.strip():
        return True  # No education restriction

    criteria_lower = criteria_text.lower()
    return any(kw.lower() in criteria_lower for kw in education_keywords)


# ─── Core Engine ─────────────────────────────────────────────────────────────

def filter_welfare_schemes(
    income_level: float,
    user_state: Optional[str] = None,
    caste_scope: Optional[list[str]] = None,
    education_keywords: Optional[list[str]] = None,
    schemes: Optional[list[dict]] = None,
    data_dir: Optional[Path] = None,
    max_results: int = 20,
) -> WelfareRecommendationResult:
    """
    Filter the 377-scheme welfare corpus by state, income, caste scope,
    and optional education keywords.

    This is the SECONDARY recommendation — clearly labeled as approximate.
    Never present these results at the same confidence level as NSFDC credit schemes.

    Args:
        income_level: Annual family income in ₹
        user_state: User's state (e.g., "Karnataka", "Tamil Nadu")
        caste_scope: User's caste categories (e.g., ["SC"])
        education_keywords: Keywords to match against education_criteria text
        schemes: Pre-loaded schemes list (for testing)
        data_dir: Data directory path override
        max_results: Maximum number of results to return

    Returns:
        WelfareRecommendationResult with matched schemes and disclaimer
    """
    if schemes is None:
        schemes = load_welfare_schemes(data_dir)

    matched: list[WelfareSchemeMatch] = []

    for scheme in schemes:
        reasons: list[str] = []

        # 1. State filter
        if not _matches_state(scheme, user_state):
            continue
        state = scheme.get("issuing_state", "Central")
        reasons.append(f"Available in: {state}")

        # 2. Income filter
        if not _matches_income(scheme, income_level):
            continue
        reasons.append("Income criteria met (approximate)")

        # 3. Caste/target scope filter
        if not _matches_target_scope(scheme, caste_scope):
            continue
        if caste_scope:
            reasons.append(f"Target group match: {', '.join(caste_scope)}")

        # 4. Education keyword filter (approximate)
        if not _keyword_match_education(scheme, education_keywords):
            continue
        if education_keywords:
            reasons.append("Education criteria keyword match (approximate)")

        # scheme_id may be int — coerce to str
        raw_id = scheme.get("scheme_id") or scheme.get("canonical_scheme_id") or scheme.get("id", "")
        scheme_id_str = str(raw_id)

        # benefits may be a list of dicts — flatten to a summary string
        raw_benefits = scheme.get("benefits", "")
        if isinstance(raw_benefits, list):
            benefits_str = "; ".join(
                b.get("description", "") for b in raw_benefits if isinstance(b, dict)
            )[:500]
        else:
            benefits_str = str(raw_benefits or "")[:500]

        # eligibility may be a list of strings
        raw_eligibility = scheme.get("eligibility", scheme.get("education_criteria", ""))
        if isinstance(raw_eligibility, list):
            eligibility_str = " ".join(str(e) for e in raw_eligibility)[:500]
        else:
            eligibility_str = str(raw_eligibility or "")[:500]

        matched.append(WelfareSchemeMatch(
            scheme_id=scheme_id_str,
            scheme_name=scheme.get("scheme_name") or scheme.get("name") or "Unknown",
            issuing_state=scheme.get("issuing_state") or "Central",
            benefits=benefits_str,
            eligibility_summary=eligibility_str,
            match_reasons=reasons,
        ))

        if len(matched) >= max_results:
            break

    return WelfareRecommendationResult(
        matches=matched,
        total_matches=len(matched),
    )
