"""
Module 4 — Hierarchical chunker.

Order (mandatory):
    1. Scheme boundary
    2. Section boundary (Details / Benefits / Eligibility / Exclusions /
       Application Process / Documents Required)
    3. Sub-split only if a section exceeds ~1200 chars
    4. Never split mid-unit (never split a table row or a numbered step)

Scale: ~377 schemes × 5–7 chunks ≈ 2,600 chunks. Do not over-engineer.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from app.modules.module4_rag.models import SchemeChunk

SECTION_CHAR_LIMIT = 1200

SECTION_ORDER = (
    "details",
    "benefits",
    "eligibility",
    "exclusions",
    "application_process",
    "documents_required",
)

# Split *before* a numbered step, "Step N", or a bullet — never through one.
_UNIT_SPLIT = re.compile(
    r"(?m)(?=^\s*(?:"
    r"\d+[.)]\s+"
    r"|\[\s*\d+\s*\]"
    r"|Step\s+\d+[:.\s]"
    r"|[-*•]\s+"
    r"))"
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _as_text(value: Any) -> str:
    """Flatten structured JSON fields into readable section text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts: list[str] = []
        for i, item in enumerate(value, 1):
            if isinstance(item, dict):
                if "description" in item:
                    step = item.get("step", i)
                    parts.append(f"{step}. {item['description']}")
                elif "raw_text" in item:
                    parts.append(str(item["raw_text"]))
                else:
                    inner = "; ".join(
                        f"{k}: {v}" for k, v in item.items() if v not in (None, "", [], {})
                    )
                    if inner:
                        parts.append(f"{i}. {inner}")
            else:
                text = str(item).strip()
                if text:
                    parts.append(f"{i}. {text}" if len(value) > 1 else text)
        return "\n".join(parts)
    if isinstance(value, dict):
        if "steps" in value:
            modes = value.get("modes") or []
            header = f"Application modes: {', '.join(str(m) for m in modes)}\n" if modes else ""
            return (header + _as_text(value["steps"])).strip()
        parts = []
        for key, val in value.items():
            flattened = _as_text(val)
            if flattened:
                parts.append(f"{key.replace('_', ' ').title()}: {flattened}")
        return "\n".join(parts)
    return str(value).strip()


def split_into_units(text: str) -> list[str]:
    """
    Split a section into atomic units (steps, bullets, paragraphs, sentences).
    A unit is never broken further except as a last resort on sentence bounds.
    """
    text = (text or "").strip()
    if not text:
        return []

    numbered = [u.strip() for u in _UNIT_SPLIT.split(text) if u.strip()]
    if len(numbered) >= 2:
        return numbered

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) >= 2:
        return paragraphs

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if len(lines) >= 2:
        return lines

    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    return sentences or [text]


def pack_units(units: list[str], limit: int = SECTION_CHAR_LIMIT) -> list[str]:
    """Pack atomic units into chunks of at most `limit` chars. Never splits a unit."""
    chunks: list[str] = []
    current = ""

    for unit in units:
        unit = unit.strip()
        if not unit:
            continue

        if len(unit) > limit:
            if current:
                chunks.append(current.strip())
                current = ""
            # Last resort: sentence-split an oversized unit. Still never mid-sentence.
            sentences = [s.strip() for s in _SENTENCE_SPLIT.split(unit) if s.strip()]
            if len(sentences) <= 1:
                chunks.append(unit)  # keep the oversized unit intact
            else:
                chunks.extend(pack_units(sentences, limit))
            continue

        candidate = f"{current}\n\n{unit}".strip() if current else unit
        if len(candidate) <= limit:
            current = candidate
        else:
            chunks.append(current.strip())
            current = unit

    if current:
        chunks.append(current.strip())
    return chunks


def subsplit_section(text: str, limit: int = SECTION_CHAR_LIMIT) -> list[str]:
    """Sub-split a section only when it exceeds the char limit."""
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]
    return pack_units(split_into_units(text), limit)


def _scheme_id_of(scheme: dict) -> str:
    raw = scheme.get("scheme_id")
    if raw is None or raw == "":
        raw = scheme.get("canonical_scheme_id") or scheme.get("id") or ""
    return str(raw)


def _region_of(scheme: dict) -> str:
    return (
        scheme.get("issuing_state")
        or scheme.get("region")
        or ("National" if scheme.get("purpose") else "")
        or "Central"
    )


def _nsfdc_sections(scheme: dict) -> dict[str, str]:
    """Compose canonical sections from an NSFDC credit-scheme record."""
    name = scheme.get("scheme_name") or "NSFDC scheme"
    purpose = scheme.get("purpose") or ""
    cost = scheme.get("project_cost") or {}
    cost_min = cost.get("min", 0) if isinstance(cost, dict) else 0
    cost_max = cost.get("max", 0) if isinstance(cost, dict) else 0
    rate = scheme.get("interest_rate_pct") or {}
    beneficiary = rate.get("beneficiary") if isinstance(rate, dict) else rate
    channel = rate.get("channel_partner") if isinstance(rate, dict) else None
    max_loan = scheme.get("max_loan_amount")
    coverage = scheme.get("project_cost_coverage_pct", 90)
    tenure = scheme.get("tenure_years")
    moratorium = scheme.get("moratorium_months")
    income_cap = scheme.get("max_annual_income", 500000)
    live_cap = scheme.get("_max_annual_income_nsfdc_live", 300000)
    docs = scheme.get("required_documents") or []
    partners = scheme.get("channel_partners") or []
    categories = scheme.get("allowed_social_categories") or ["sc"]

    max_loan_text = (
        f"₹{max_loan:,.0f}" if isinstance(max_loan, (int, float)) else
        "derived from project cost × coverage % (no fixed rupee cap)"
    )
    moratorium_text = (
        "0 months (null in source treated as 0)"
        if moratorium is None else
        f"{moratorium} months. Interest does NOT accrue during moratorium "
        "(documented assumption — source data does not specify either way)."
    )

    details = (
        f"Scheme: {name}\n"
        f"Scheme ID: {_scheme_id_of(scheme)}\n"
        f"Issuing authority: NSFDC (National Scheduled Castes Finance and Development Corporation)\n"
        f"Purpose: {purpose}\n"
        f"Project cost range: ₹{cost_min:,.0f}–₹{cost_max:,.0f}\n"
        f"Official source: {scheme.get('official_source_url') or 'https://nsfdc.nic.in/scheme'}"
    )
    benefits = (
        f"Maximum loan amount: {max_loan_text}\n"
        f"Project cost coverage: {coverage}%\n"
        f"Beneficiary interest rate: {beneficiary}% per annum (scheme-owned, not user-editable)\n"
        + (f"Channel partner interest rate: {channel}% per annum\n" if channel is not None else "")
        + f"Tenure: {tenure} years\n"
        f"Moratorium: {moratorium_text}"
    )
    eligibility = (
        f"Target group: {', '.join(str(c).upper() for c in categories)} beneficiaries\n"
        f"Annual family income cap: ₹{income_cap:,.0f} (Problem Statement baseline)\n"
        f"Live NSFDC income figure (annotated alternate, not silently overridden): ₹{live_cap:,.0f}\n"
        f"Purpose must be: {purpose}\n"
        "Direct loan applications are not entertained — funds are routed through channel partners."
    )
    application = (
        "Apply through an authorized NSFDC channel partner, then complete the "
        "application on the PM-SURAJ Portal. NidhiPath does not process applications.\n"
        f"Authorized channel partner types: {', '.join(str(p) for p in partners) or 'see scheme guidelines'}."
    )
    documents = _as_text(docs) or "Aadhaar, caste certificate, income certificate, bank account details."

    return {
        "details": details,
        "benefits": benefits,
        "eligibility": eligibility,
        "application_process": application,
        "documents_required": documents,
    }


def _welfare_sections(scheme: dict) -> dict[str, str]:
    """Prefer raw_sections when present; otherwise compose from structured fields."""
    raw = scheme.get("raw_sections") if isinstance(scheme.get("raw_sections"), dict) else {}
    composed = {
        "details": raw.get("details") or "\n".join(
            p for p in [
                f"Scheme: {scheme.get('scheme_name') or 'Unknown'}",
                f"Issuing state: {scheme.get('issuing_state') or 'Central'}",
                f"Issuing body: {scheme.get('issuing_body') or scheme.get('ministry') or scheme.get('department') or 'Not specified'}",
                f"Category: {scheme.get('scheme_category') or ''}",
            ] if p
        ),
        "benefits": raw.get("benefits") or _as_text(
            scheme.get("benefits") or scheme.get("financial_assistance")
        ),
        "eligibility": raw.get("eligibility") or "\n".join(
            p for p in [
                _as_text(scheme.get("education_criteria")),
                _as_text(scheme.get("income_criteria")),
                _as_text(scheme.get("caste_or_target_scope")),
                _as_text(scheme.get("residency_criteria")),
                _as_text(scheme.get("eligibility")),
            ] if p
        ),
        "exclusions": raw.get("exclusions") or _as_text(
            scheme.get("exclusions") or scheme.get("restrictions")
        ),
        "application_process": raw.get("application_process") or _as_text(
            scheme.get("application_process")
        ),
        "documents_required": raw.get("documents_required") or _as_text(
            scheme.get("documents_required")
        ),
    }
    return {k: v.strip() for k, v in composed.items() if v and str(v).strip()}


def extract_sections(scheme: dict, source: str) -> dict[str, str]:
    if source == "nsfdc":
        return {k: v for k, v in _nsfdc_sections(scheme).items() if v.strip()}
    return _welfare_sections(scheme)


def chunk_scheme(scheme: dict, source: str = "welfare") -> list[SchemeChunk]:
    """Chunk a single scheme. Scheme boundary is the outer unit."""
    scheme_id = _scheme_id_of(scheme)
    scheme_name = scheme.get("scheme_name") or scheme.get("name") or "Unknown"
    region = str(_region_of(scheme) or "")
    sections = extract_sections(scheme, source)

    chunks: list[SchemeChunk] = []
    for section_name in SECTION_ORDER:
        text = sections.get(section_name, "")
        if not text:
            continue
        parts = subsplit_section(text)
        sibling_count = len(parts)
        was_subsplit = sibling_count > 1
        for index, part in enumerate(parts):
            chunks.append(
                SchemeChunk(
                    chunk_id=f"{scheme_id}::{section_name}::{index}",
                    scheme_id=scheme_id,
                    scheme_name=scheme_name,
                    region=region,
                    section=section_name,
                    section_index=index,
                    sibling_count=sibling_count,
                    was_subsplit=was_subsplit,
                    text=part,
                    source=source,
                )
            )
    return chunks


def chunk_schemes(
    nsfdc_schemes: Optional[list[dict]] = None,
    welfare_schemes: Optional[list[dict]] = None,
) -> list[SchemeChunk]:
    """Chunk NSFDC credit schemes first, then the welfare corpus."""
    chunks: list[SchemeChunk] = []
    for scheme in nsfdc_schemes or []:
        chunks.extend(chunk_scheme(scheme, source="nsfdc"))
    for scheme in welfare_schemes or []:
        chunks.extend(chunk_scheme(scheme, source="welfare"))
    return chunks
