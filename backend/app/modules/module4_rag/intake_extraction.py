"""
Module 4 — Free-text intake extraction.

Maps a natural-language need onto the same 4 structured fields Module 1
consumes. Extracted fields are ALWAYS shown back for confirmation —
never auto-trusted, never fed silently into the recommender.

If Groq is unavailable, a deterministic heuristic extractor is used so
the free-text path still works (AI enhances, never gates).
"""

from __future__ import annotations

import re
from typing import Any, Optional

from app.modules.module4_rag.llm import GroqUnavailable, groq_available, groq_json
from app.modules.module4_rag.models import IntakeExtractResult

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

EDUCATION_KEYWORDS = (
    "education", "college", "university", "course", "admission", "tuition",
    "study", "studies", "student", "degree", "diploma", "शिक्षा", "पढ़ाई",
    "कॉलेज", "दाखिला", "कोर्स",
)
BUSINESS_KEYWORDS = (
    "business", "shop", "kirana", "enterprise", "self employment",
    "self-employment", "startup", "factory", "workshop", "vehicle",
    "tailor", "farm", "व्यापार", "दुकान", "उद्यम", "रोजगार", "किराना",
)
ADMISSION_KEYWORDS = (
    "admission secured", "got admission", "offer letter", "admitted",
    "प्रवेश मिल", "एडमिशन",
)
ENROLLED_KEYWORDS = (
    "currently enrolled", "already studying", "pursuing", "enrolled",
    "पढ़ रहा", "नामांकित",
)

EXTRACT_SYSTEM = """You extract structured loan-intake fields from a beneficiary's free-text description for NSFDC/MoSJE schemes.

Return a JSON object with EXACTLY these keys:
{
  "estimated_cost": number or null,          // project/education cost in INR
  "income_level": number or null,            // annual family income in INR
  "project_type": "business_self_employment" or "education" or null,
  "education_status": "admission_secured" or "currently_enrolled" or null,
  "user_state": string or null,              // Indian state/UT name
  "caste_scope": ["SC"] or null,
  "confidence": number between 0 and 1,
  "notes": string                            // what was ambiguous or assumed
}

Rules:
- Indian number words: lakh/lac = 100000, crore = 10000000. "1.4 lakh" = 140000.
- Never invent values the user did not state. Use null when unknown.
- "income" / "earn" / "salary" nearby a number → income_level.
- "cost" / "project" / "need" / "loan of" nearby a number → estimated_cost.
- If only one amount is given and context is a project/loan need, treat it as estimated_cost.
- caste_scope defaults to ["SC"] only if the user mentions SC / scheduled caste; otherwise null.
- education_status is only set when project_type is education.
"""


def _parse_indian_amount(raw: str) -> Optional[float]:
    """Parse '1.4 lakh', '₹50,000', '2 crore', '5 लाख' into a float rupee amount."""
    text = raw.lower().replace(",", "").replace("₹", "").replace("rs.", "").replace("rs", "")
    text = text.replace("लाख", "lakh").replace("करोड़", "crore")
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(lakh|lac|lakhs|crore|crores)?",
        text,
    )
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2) or ""
    if unit.startswith("lakh") or unit == "lac":
        value *= 100_000
    elif unit.startswith("crore"):
        value *= 10_000_000
    return value


def _amounts_with_context(text: str) -> list[tuple[float, str]]:
    """Return (amount, surrounding_context) pairs."""
    pattern = re.compile(
        r"((?:₹|rs\.?\s*)?\d[\d,]*(?:\.\d+)?\s*(?:lakh|lac|lakhs|crore|crores|लाख|करोड़)?)",
        re.IGNORECASE,
    )
    found: list[tuple[float, str]] = []
    for match in pattern.finditer(text):
        amount = _parse_indian_amount(match.group(1))
        if amount is None or amount <= 0:
            continue
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        found.append((amount, text[start:end].lower()))
    return found


def _detect_state(text: str) -> Optional[str]:
    lowered = text.lower()
    for state in INDIAN_STATES:
        if state.lower() in lowered:
            return state
    aliases = {
        "bengaluru": "Karnataka",
        "bangalore": "Karnataka",
        "mumbai": "Maharashtra",
        "chennai": "Tamil Nadu",
        "hyderabad": "Telangana",
        "kolkata": "West Bengal",
        "ncr": "Delhi",
        "new delhi": "Delhi",
    }
    for alias, state in aliases.items():
        if alias in lowered:
            return state
    return None


def heuristic_extract(text: str) -> IntakeExtractResult:
    """Deterministic extractor used when Groq is unavailable or as a merge base."""
    raw = (text or "").strip()
    lowered = raw.lower()

    project_type: Optional[str] = None
    if any(k in lowered for k in EDUCATION_KEYWORDS):
        project_type = "education"
    elif any(k in lowered for k in BUSINESS_KEYWORDS):
        project_type = "business_self_employment"

    education_status: Optional[str] = None
    if project_type == "education":
        if any(k in lowered for k in ADMISSION_KEYWORDS):
            education_status = "admission_secured"
        elif any(k in lowered for k in ENROLLED_KEYWORDS):
            education_status = "currently_enrolled"

    income_level: Optional[float] = None
    estimated_cost: Optional[float] = None
    income_hints = ("income", "earn", "salary", "आय", "कमाई", "family income")
    cost_hints = ("cost", "project", "need", "loan", "want", "require", "खर्च", "लागत", "कर्ज", "लोन")

    for amount, ctx in _amounts_with_context(raw):
        if any(h in ctx for h in income_hints) and income_level is None:
            income_level = amount
        elif any(h in ctx for h in cost_hints) and estimated_cost is None:
            estimated_cost = amount
        elif estimated_cost is None:
            estimated_cost = amount

    caste_scope: Optional[list[str]] = None
    if re.search(r"\bsc\b|scheduled caste|अनुसूचित जाति", lowered):
        caste_scope = ["SC"]

    user_state = _detect_state(raw)

    missing: list[str] = []
    if estimated_cost is None:
        missing.append("estimated_cost")
    if income_level is None:
        missing.append("income_level")
    if project_type is None:
        missing.append("project_type")
    if project_type == "education" and education_status is None:
        missing.append("education_status")

    filled = 4 - len([f for f in ("estimated_cost", "income_level", "project_type") if f in missing])
    confidence = round(max(0.15, filled / 4), 2)

    notes_parts = []
    if missing:
        notes_parts.append("Missing: " + ", ".join(missing) + ". Please confirm or fill these in.")
    else:
        notes_parts.append("All core fields were found. Please confirm before continuing.")

    return IntakeExtractResult(
        estimated_cost=estimated_cost,
        income_level=income_level,
        project_type=project_type,
        education_status=education_status,
        user_state=user_state,
        caste_scope=caste_scope,
        confidence=confidence,
        missing_fields=missing,
        notes=" ".join(notes_parts),
        source="heuristic",
        needs_confirmation=True,
        raw_text=raw,
    )


def _coerce_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _from_llm_payload(payload: dict[str, Any], raw_text: str) -> IntakeExtractResult:
    project_type = payload.get("project_type")
    if project_type not in ("business_self_employment", "education"):
        project_type = None
    education_status = payload.get("education_status")
    if education_status not in ("admission_secured", "currently_enrolled"):
        education_status = None
    if project_type != "education":
        education_status = None

    caste = payload.get("caste_scope")
    caste_scope: Optional[list[str]] = None
    if isinstance(caste, list) and caste:
        caste_scope = [str(c) for c in caste]
    elif isinstance(caste, str) and caste.strip():
        caste_scope = [caste.strip()]

    estimated_cost = _coerce_float(payload.get("estimated_cost"))
    income_level = _coerce_float(payload.get("income_level"))

    missing: list[str] = []
    if estimated_cost is None:
        missing.append("estimated_cost")
    if income_level is None:
        missing.append("income_level")
    if project_type is None:
        missing.append("project_type")
    if project_type == "education" and education_status is None:
        missing.append("education_status")

    try:
        confidence = float(payload.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    notes = str(payload.get("notes") or "").strip()
    if not notes:
        notes = "Please confirm the extracted fields before continuing."

    return IntakeExtractResult(
        estimated_cost=estimated_cost,
        income_level=income_level,
        project_type=project_type,
        education_status=education_status,
        user_state=(str(payload.get("user_state")).strip() if payload.get("user_state") else None),
        caste_scope=caste_scope,
        confidence=confidence,
        missing_fields=missing,
        notes=notes,
        source="llm",
        needs_confirmation=True,
        raw_text=raw_text,
    )


def extract_intake(text: str) -> IntakeExtractResult:
    """
    Extract structured intake fields from free text.

    Prefers Groq; falls back to the heuristic extractor. The result always
    has needs_confirmation=True.
    """
    raw = (text or "").strip()
    if not raw:
        return IntakeExtractResult(
            missing_fields=["estimated_cost", "income_level", "project_type"],
            notes="Empty description. Please type your need or use the form.",
            source="heuristic",
            needs_confirmation=True,
            raw_text="",
            confidence=0.0,
        )

    if groq_available():
        try:
            payload = groq_json(
                [
                    {"role": "system", "content": EXTRACT_SYSTEM},
                    {"role": "user", "content": raw},
                ]
            )
            result = _from_llm_payload(payload, raw)
            # Fill obvious gaps from the heuristic so a partial LLM parse
            # still surfaces numbers the user typed.
            fallback = heuristic_extract(raw)
            if result.estimated_cost is None:
                result.estimated_cost = fallback.estimated_cost
            if result.income_level is None:
                result.income_level = fallback.income_level
            if result.project_type is None:
                result.project_type = fallback.project_type
            if result.education_status is None:
                result.education_status = fallback.education_status
            if result.user_state is None:
                result.user_state = fallback.user_state
            result.missing_fields = [
                f for f in (
                    "estimated_cost", "income_level", "project_type",
                    *(["education_status"] if result.project_type == "education" else []),
                )
                if getattr(result, f) is None
            ]
            result.needs_confirmation = True
            return result
        except GroqUnavailable:
            pass

    return heuristic_extract(raw)
