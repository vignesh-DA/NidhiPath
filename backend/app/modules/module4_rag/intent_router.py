"""
Module 4 — Intent router.

Structured questions ("what's the interest rate") are answered from
scheme records with zero LLM calls.

Only narrative questions ("why don't I qualify", "how does moratorium
work") reach retrieval + generation.

This runs BEFORE retrieval. Eligibility yes/no is never an LLM judgment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

NARRATIVE_MARKERS = (
    "why",
    "explain",
    "how does",
    "how do",
    "how is",
    "difference",
    "compare",
    "versus",
    "vs ",
    "tell me about",
    "what happens",
    "क्यों",
    "क्या फर्क",
    "समझाओ",
    "कैसे काम",
)

# field -> keyword patterns (English + common Hindi)
STRUCTURED_PATTERNS: dict[str, tuple[str, ...]] = {
    "interest_rate": (
        "interest rate", "interest", "roi", "ब्याज", "ब्याज दर",
        "rate of interest", "% p.a", "per annum",
    ),
    "income_cap": (
        "income cap", "income limit", "maximum income", "max income",
        "annual income", "family income", "आय सीमा", "आय की सीमा",
        "income eligibility", "income criteria",
    ),
    "max_loan": (
        "max loan", "maximum loan", "loan amount", "loan limit",
        "how much can i get", "how much loan", "ceiling",
        "अधिकतम ऋण", "लोन राशि",
    ),
    "tenure": (
        "tenure", "repayment period", "how many years", "loan period",
        "अवधि", "चुकौती",
    ),
    "moratorium": (
        "moratorium", "holiday period", "repayment holiday",
        "स्थगन", "मोरेटोरियम",
    ),
    "documents": (
        "document", "documents", "papers", "what do i need",
        "kyc", "aadhaar", "caste certificate",
        "दस्तावेज", "कागजात",
    ),
    "coverage": (
        "coverage", "how much of the cost", "project cost coverage",
        "90%", "percent of project",
    ),
    "channel_partners": (
        "channel partner", "where to apply", "which bank", "sca",
        "nbfc", "partner", "who processes",
        "चैनल पार्टनर",
    ),
    "eligibility": (
        "eligibility criteria", "who is eligible", "who can apply",
        "पात्रता", "कौन आवेदन",
    ),
}


@dataclass(frozen=True)
class RoutedIntent:
    kind: str  # "structured" | "narrative"
    field: Optional[str] = None
    reason: str = ""


def _normalize(question: str) -> str:
    return re.sub(r"\s+", " ", (question or "").strip().lower())


def route_intent(question: str) -> RoutedIntent:
    """
    Classify a user question.

    Narrative markers win: "why is the interest rate so high" is narrative
    even though it contains "interest rate".
    """
    text = _normalize(question)
    if not text:
        return RoutedIntent(kind="narrative", reason="empty question")

    if any(marker in text for marker in NARRATIVE_MARKERS):
        return RoutedIntent(
            kind="narrative",
            reason="question asks for explanation, comparison, or causation",
        )

    # First matching structured field (more specific patterns are listed first
    # within each field; fields themselves are ordered by typical precision).
    for field, patterns in STRUCTURED_PATTERNS.items():
        if any(p in text for p in patterns):
            return RoutedIntent(
                kind="structured",
                field=field,
                reason=f"direct lookup of {field}",
            )

    return RoutedIntent(kind="narrative", reason="no structured field matched")
