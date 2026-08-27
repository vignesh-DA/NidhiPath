"""
Module 4 — Q&A orchestrator.

Flow:
    1. Route intent (structured vs narrative)
    2. Structured → direct lookup on NSFDC / welfare records, zero LLM
    3. Narrative → metadata-prefiltered retrieval + generation
    4. Session stickiness: when scheme_id is provided, never leave that scheme

Eligibility yes/no is never produced here.
"""

from __future__ import annotations

from typing import Any, Optional

from app.modules.module4_rag.generation import extractive_answer, generate_answer
from app.modules.module4_rag.intent_router import route_intent
from app.modules.module4_rag.models import QAResult, SourceChunk
from app.modules.module4_rag.retrieval import retrieve_as_sources


def _load_nsfdc() -> list[dict]:
    try:
        from app.modules.module1_recommender.credit_engine import load_nsfdc_schemes
        return load_nsfdc_schemes()
    except FileNotFoundError:
        return []


def _load_welfare() -> list[dict]:
    try:
        from app.modules.module1_recommender.welfare_engine import load_welfare_schemes
        return load_welfare_schemes()
    except FileNotFoundError:
        return []


def _scheme_id_of(scheme: dict) -> str:
    raw = scheme.get("scheme_id")
    if raw is None or raw == "":
        raw = scheme.get("canonical_scheme_id") or ""
    return str(raw)


def find_scheme(
    scheme_id: Optional[str],
    nsfdc: Optional[list[dict]] = None,
    welfare: Optional[list[dict]] = None,
) -> tuple[Optional[dict], str]:
    """Return (scheme_record, source) where source is nsfdc|welfare|''."""
    if not scheme_id:
        return None, ""
    sid = str(scheme_id)
    for scheme in (nsfdc if nsfdc is not None else _load_nsfdc()):
        if _scheme_id_of(scheme) == sid:
            return scheme, "nsfdc"
    for scheme in (welfare if welfare is not None else _load_welfare()):
        if _scheme_id_of(scheme) == sid or str(scheme.get("canonical_scheme_id") or "") == sid:
            return scheme, "welfare"
    return None, ""


def _inr(value: Any) -> str:
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "not specified"


def _structured_from_nsfdc(scheme: dict, field: str, language: str) -> str:
    name = scheme.get("scheme_name") or "This NSFDC scheme"
    rate = scheme.get("interest_rate_pct") or {}
    beneficiary = rate.get("beneficiary") if isinstance(rate, dict) else rate
    cost = scheme.get("project_cost") or {}
    hi = language == "hi"

    if field == "interest_rate":
        return (
            f"{name} की लाभार्थी ब्याज दर {beneficiary}% प्रति वर्ष है। यह दर योजना द्वारा तय है, आवेदक इसे नहीं बदल सकता।"
            if hi else
            f"The beneficiary interest rate for {name} is {beneficiary}% per annum. "
            "This rate is scheme-owned and cannot be changed by the applicant."
        )
    if field == "income_cap":
        cap = scheme.get("max_annual_income", 500000)
        live = scheme.get("_max_annual_income_nsfdc_live", 300000)
        return (
            f"{name} के लिए वार्षिक पारिवारिक आय सीमा {_inr(cap)} है (समस्या विवरण के अनुसार)। "
            f"NSFDC की वर्तमान आधिकारिक सीमा {_inr(live)} है — दोनों अंक संग्रहीत हैं, कोई चुपचाप ओवरराइड नहीं किया गया।"
            if hi else
            f"The annual family income cap for {name} is {_inr(cap)} "
            "(Problem Statement baseline). The live NSFDC figure is "
            f"{_inr(live)} — both are stored; neither is silently overridden."
        )
    if field == "max_loan":
        max_loan = scheme.get("max_loan_amount")
        coverage = scheme.get("project_cost_coverage_pct", 90)
        if max_loan is None:
            body = (
                f"{name} has no fixed rupee cap; the disbursable amount is derived from "
                f"project cost × {coverage}% coverage."
            )
        else:
            body = f"The maximum loan amount for {name} is {_inr(max_loan)} ({coverage}% of project cost, whichever is lower)."
        return body
    if field == "tenure":
        tenure = scheme.get("tenure_years")
        return (
            f"{name} की अधिकतम अवधि {tenure} वर्ष है।"
            if hi else
            f"The maximum tenure for {name} is {tenure} years."
        )
    if field == "moratorium":
        months = scheme.get("moratorium_months")
        months_text = "0 (source null treated as 0)" if months is None else str(months)
        return (
            f"{name} की स्थगन अवधि {months_text} महीने है। इस अवधि में ब्याज नहीं लगता "
            "(हमारा प्रलेखित अनुमान — स्रोत स्पष्ट नहीं करता)।"
            if hi else
            f"The moratorium for {name} is {months_text} month(s). "
            "Interest does NOT accrue during moratorium — this is our documented assumption "
            "because the source data does not specify either way. EMI starts at month "
            f"{(months or 0) + 1}."
        )
    if field == "documents":
        docs = scheme.get("required_documents") or []
        listed = ", ".join(str(d).replace("_", " ") for d in docs) or "see scheme guidelines"
        return (
            f"{name} के लिए आवश्यक दस्तावेज: {listed}।"
            if hi else
            f"Typical documents for {name}: {listed}. "
            "Carry originals for verification at the channel partner."
        )
    if field == "coverage":
        coverage = scheme.get("project_cost_coverage_pct", 90)
        cmin = cost.get("min", 0) if isinstance(cost, dict) else 0
        cmax = cost.get("max", 0) if isinstance(cost, dict) else 0
        return (
            f"{name} covers {coverage}% of project cost. Eligible project cost range: "
            f"{_inr(cmin)}–{_inr(cmax)}."
        )
    if field == "channel_partners":
        partners = scheme.get("channel_partners") or []
        return (
            f"{name} is processed by: {', '.join(str(p) for p in partners)}. "
            "Use the Partner Locator for state-bound SCA matching. "
            "NBFC-MFIs have no IFSC branch geo — they resolve to HQ only."
        )
    if field == "eligibility":
        cats = scheme.get("allowed_social_categories") or ["sc"]
        cap = scheme.get("max_annual_income", 500000)
        purpose = scheme.get("purpose") or ""
        return (
            f"{name} is for {', '.join(str(c).upper() for c in cats)} beneficiaries "
            f"with annual family income up to {_inr(cap)}, purpose={purpose}. "
            "This is a description of the rule, not a decision on your case. "
            "Use the form-based recommender for an exact match."
        )
    return f"No structured field '{field}' is defined for {name}."


def _structured_from_welfare(scheme: dict, field: str) -> str:
    name = scheme.get("scheme_name") or "This scheme"
    if field == "documents":
        docs = scheme.get("documents_required") or []
        if isinstance(docs, list):
            listed = "; ".join(str(d) for d in docs[:12])
        else:
            listed = str(docs)
        return f"Documents listed for {name}: {listed or 'see issuing authority guidelines'}."
    if field == "eligibility":
        criteria = scheme.get("education_criteria") or scheme.get("eligibility") or []
        if isinstance(criteria, list):
            listed = " ".join(str(c) for c in criteria[:6])
        else:
            listed = str(criteria)
        return (
            f"Eligibility notes for {name} (approximate, unstructured): {listed}. "
            "Verify with the issuing authority. This is not an NSFDC credit-scheme decision."
        )
    if field == "income_cap":
        criteria = scheme.get("income_criteria") or []
        if isinstance(criteria, list) and criteria:
            bits = []
            for item in criteria:
                if isinstance(item, dict) and item.get("amount") is not None:
                    bits.append(f"{item.get('operator', 'less_than')} {_inr(item.get('amount'))}")
            if bits:
                return f"Income criteria for {name}: {'; '.join(bits)}. Treat as approximate."
        return f"No structured income cap is recorded for {name}."
    if field == "max_loan":
        loan = (scheme.get("loan_details") or {}).get("loan_amount") if isinstance(scheme.get("loan_details"), dict) else None
        if isinstance(loan, dict) and loan.get("maximum") is not None:
            return f"Recorded loan ceiling for {name}: {_inr(loan.get('maximum'))}."
        benefits = scheme.get("benefits") or []
        if isinstance(benefits, list):
            amounts = [
                f"{b.get('description')} ({_inr(b.get('amount'))})"
                for b in benefits if isinstance(b, dict) and b.get("amount") is not None
            ]
            if amounts:
                return f"Benefit amounts for {name}: " + "; ".join(amounts)
        return f"No structured loan ceiling is recorded for {name}."
    return (
        f"{name} is a welfare-corpus scheme (approximate match, not an NSFDC credit scheme). "
        "Ask a more specific question, or open the scheme Q&A after a recommendation."
    )


def _structured_across_nsfdc(field: str, language: str, nsfdc: list[dict]) -> str:
    if not nsfdc:
        return "NSFDC scheme data is not loaded."
    lines = [_structured_from_nsfdc(scheme, field, language) for scheme in nsfdc]
    header = (
        "NSFDC credit schemes (authoritative, rule-verified records):\n\n"
        if language != "hi" else
        "NSFDC ऋण योजनाएं (आधिकारिक):\n\n"
    )
    return header + "\n\n".join(f"• {line}" for line in lines)


def answer_structured(
    field: str,
    *,
    scheme_id: Optional[str],
    language: str,
    nsfdc: Optional[list[dict]] = None,
    welfare: Optional[list[dict]] = None,
) -> tuple[str, Optional[str], Optional[str]]:
    """Returns (answer, scheme_id, scheme_name)."""
    nsfdc = nsfdc if nsfdc is not None else _load_nsfdc()
    welfare = welfare if welfare is not None else _load_welfare()
    scheme, source = find_scheme(scheme_id, nsfdc, welfare)
    if scheme and source == "nsfdc":
        return _structured_from_nsfdc(scheme, field, language), _scheme_id_of(scheme), scheme.get("scheme_name")
    if scheme and source == "welfare":
        return _structured_from_welfare(scheme, field), _scheme_id_of(scheme), scheme.get("scheme_name")
    return _structured_across_nsfdc(field, language, nsfdc), None, None


def answer_question(
    question: str,
    *,
    scheme_id: Optional[str] = None,
    language: str = "en",
    nsfdc_schemes: Optional[list[dict]] = None,
    welfare_schemes: Optional[list[dict]] = None,
    chunks: Optional[list] = None,
) -> QAResult:
    """Main Q&A entry point. Unit-testable with injected corpora."""
    routed = route_intent(question)
    nsfdc = nsfdc_schemes if nsfdc_schemes is not None else _load_nsfdc()
    welfare = welfare_schemes if welfare_schemes is not None else _load_welfare()
    scheme, source = find_scheme(scheme_id, nsfdc, welfare)
    scheme_name = scheme.get("scheme_name") if scheme else None

    if routed.kind == "structured" and routed.field:
        answer, sid, sname = answer_structured(
            routed.field,
            scheme_id=scheme_id,
            language=language,
            nsfdc=nsfdc,
            welfare=welfare,
        )
        return QAResult(
            answer=answer,
            intent="structured",
            intent_field=routed.field,
            scheme_id=sid,
            scheme_name=sname,
            sources=[],
            language=language,
            used_llm=False,
        )

    sources: list[SourceChunk] = retrieve_as_sources(
        question,
        scheme_id=scheme_id if scheme else None,
        source=source or ("nsfdc" if not scheme_id else None),
        top_k=5,
        chunks=chunks,
    )
    # If the user didn't pin a scheme and NSFDC retrieval is thin, widen to welfare.
    if not scheme_id and len(sources) < 2:
        wider = retrieve_as_sources(question, top_k=5, chunks=chunks)
        if wider:
            sources = wider

    answer, used_llm = generate_answer(
        question,
        sources,
        language=language,
        scheme_name=scheme_name,
    )
    if not sources and not used_llm:
        answer = extractive_answer(question, sources, language=language)

    return QAResult(
        answer=answer,
        intent="narrative",
        intent_field=None,
        scheme_id=_scheme_id_of(scheme) if scheme else None,
        scheme_name=scheme_name,
        sources=sources,
        language=language,
        used_llm=used_llm,
    )
