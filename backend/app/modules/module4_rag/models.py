"""
Module 4 — Shared Pydantic models.

RAG is used ONLY for open-ended narrative questions, never for the
yes/no eligibility decision itself (AD-1).
"""

from typing import Optional
from pydantic import BaseModel, Field


class SchemeChunk(BaseModel):
    """One retrieval unit. A section may produce multiple sibling chunks."""

    chunk_id: str
    scheme_id: str
    scheme_name: str
    region: str = ""
    section: str
    section_index: int = 0
    sibling_count: int = 1
    was_subsplit: bool = False
    text: str
    source: str = "welfare"  # "nsfdc" | "welfare"
    embedding: list[float] = Field(default_factory=list)
    embedding_version: str = ""


class SourceChunk(BaseModel):
    """Chunk citation returned to the client (no embedding)."""

    chunk_id: str
    scheme_id: str
    scheme_name: str
    section: str
    text: str
    score: float = 0.0


class IntakeExtractResult(BaseModel):
    """Free-text → structured fields. NEVER auto-trusted — UI must confirm."""

    estimated_cost: Optional[float] = None
    income_level: Optional[float] = None
    project_type: Optional[str] = None  # business_self_employment | education
    education_status: Optional[str] = None  # admission_secured | currently_enrolled
    user_state: Optional[str] = None
    caste_scope: Optional[list[str]] = None
    confidence: float = 0.0
    missing_fields: list[str] = Field(default_factory=list)
    notes: str = ""
    source: str = "heuristic"  # "llm" | "heuristic"
    needs_confirmation: bool = True
    raw_text: str = ""


class QAResult(BaseModel):
    """Scheme-scoped Q&A response."""

    answer: str
    intent: str  # "structured" | "narrative"
    intent_field: Optional[str] = None
    scheme_id: Optional[str] = None
    scheme_name: Optional[str] = None
    sources: list[SourceChunk] = Field(default_factory=list)
    language: str = "en"
    used_llm: bool = False
    disclaimer: str = (
        "This answer is grounded in scheme documentation. "
        "It is not an eligibility decision — use the form-based recommender "
        "for exact NSFDC credit-scheme matching."
    )
