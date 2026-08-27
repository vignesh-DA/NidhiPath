"""
API Routes — Module 4: LLM Intake + RAG Q&A

POST /api/v1/intake/extract
    Free-text → structured intake fields. NEVER auto-trusted: the result
    always carries needs_confirmation=True and the UI must show it back
    for user confirmation before feeding Module 1.

POST /api/v1/qa
    Scheme-scoped Q&A. Intent routing happens first: structured questions
    ("what's the interest rate") are answered directly from the scheme
    records with ZERO LLM calls; only narrative questions ("why don't I
    qualify") reach retrieval + generation.

Architecture rules honored here (non-negotiable):
    - RAG is used ONLY for open-ended narrative questions, never for the
      yes/no eligibility decision itself.
    - If Groq is unavailable, both endpoints still work (heuristic
      extraction, extractive answers). AI enhances; it never gates.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.module4_rag.intake_extraction import extract_intake
from app.modules.module4_rag.models import IntakeExtractResult, QAResult
from app.modules.module4_rag.qa_service import answer_question


router = APIRouter()


# ─── Intake Extraction ───────────────────────────────────────────────────────

class IntakeExtractRequest(BaseModel):
    """Free-text description of the beneficiary's need."""
    text: str = Field(..., min_length=1, description="User's free-text need description")


class IntakeExtractResponse(IntakeExtractResult):
    """Extraction result — must be confirmed by the user before use."""
    message: str = (
        "Confirm these fields before continuing. Extracted values are "
        "never auto-trusted."
    )


@router.post("/intake/extract", response_model=IntakeExtractResponse)
async def extract_intake_endpoint(request: IntakeExtractRequest):
    """
    LLM Intake — free-text → {estimated_cost, income_level, project_type,
    education_status, ...}.

    Uses Groq when configured; falls back to a deterministic heuristic
    extractor otherwise. The result ALWAYS requires user confirmation.
    """
    try:
        result = extract_intake(request.text)
    except Exception as exc:  # never let intake extraction 500 the flow
        raise HTTPException(
            status_code=503,
            detail=f"Intake extraction failed: {exc}",
        )
    return IntakeExtractResponse(**result.model_dump())


# ─── Q&A ─────────────────────────────────────────────────────────────────────

class QARequest(BaseModel):
    """A user question, optionally scoped to a matched scheme."""
    question: str = Field(..., min_length=1, description="User's question")
    scheme_id: Optional[str] = Field(
        None,
        description="Matched scheme id — session-scoped stickiness when present",
    )
    language: str = Field(
        "en",
        description="Answer language code (en, hi, ta, te, kn, mr)",
    )


@router.post("/qa", response_model=QAResult)
async def qa_endpoint(request: QARequest):
    """
    RAG Q&A — grounded, scheme-scoped answers.

    Structured questions are answered from Postgres/JSON records with zero
    LLM calls. Narrative questions use metadata-prefiltered retrieval and
    (when Groq is configured) generation directly in the user's language.

    This endpoint NEVER produces an eligibility yes/no decision.
    """
    try:
        return answer_question(
            request.question,
            scheme_id=request.scheme_id,
            language=request.language,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Q&A failed: {exc}",
        )