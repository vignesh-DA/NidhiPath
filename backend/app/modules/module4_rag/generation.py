"""
Module 4 — Answer generation.

Narrative answers are generated in the user's target language in ONE call.
Do not generate English then translate as a second step.

If Groq is down, fall back to an extractive answer from retrieved chunks
so Q&A still works (AI enhances, never gates).

This module must NEVER issue an eligibility yes/no judgment.
"""

from __future__ import annotations

from typing import Optional

from app.modules.module4_rag.llm import GroqUnavailable, groq_available, groq_chat
from app.modules.module4_rag.models import SourceChunk

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "mr": "Marathi (मराठी)",
    "ml": "Malayalam (മലയാളം)",
}

SYSTEM_PROMPT = """You are NidhiPath, a government scheme assistant for NSFDC and MoSJE.

Rules:
- Answer ONLY from the provided scheme chunks. If they do not contain the answer, say so.
- Answer in {language}. Do not answer in English first and then translate.
- Do NOT decide whether the user is eligible. Eligibility is a deterministic rule-engine decision, not yours. Point them to the form-based scheme recommender for yes/no matching.
- Do not invent interest rates, income caps, loan amounts, or document lists.
- Cite the section name (benefits, eligibility, documents_required, etc.) you used.
- Be concise and practical. Use rupee amounts as written in the source.
- If chunks cover more than one scheme, say so clearly and do not merge them.
"""


def _format_context(sources: list[SourceChunk]) -> str:
    blocks = []
    for i, src in enumerate(sources, 1):
        blocks.append(
            f"[{i}] scheme={src.scheme_name} (id={src.scheme_id}) "
            f"section={src.section}\n{src.text}"
        )
    return "\n\n".join(blocks) if blocks else "(no scheme chunks retrieved)"


def extractive_answer(
    question: str,
    sources: list[SourceChunk],
    language: str = "en",
) -> str:
    """
    LLM-free fallback: return the most relevant chunk text with a header.
    Hindi gets a short prefix; other languages stay in source language
    (scheme text is English in the corpus).
    """
    if not sources:
        if language == "hi":
            return (
                "इस प्रश्न का उत्तर आधिकारिक योजना पाठ में नहीं मिला। "
                "कृपया योजना का नाम चुनें या फॉर्म-आधारित सुझाव का उपयोग करें।"
            )
        return (
            "I could not find this in the official scheme text. "
            "Select a matched scheme or use the form-based recommender for exact eligibility."
        )

    top = sources[0]
    header_en = (
        f"From {top.scheme_name} ({top.section.replace('_', ' ')}):\n\n"
    )
    header_hi = (
        f"{top.scheme_name} ({top.section.replace('_', ' ')}) से:\n\n"
    )
    header = header_hi if language == "hi" else header_en
    body = top.text.strip()
    # Include sibling chunks of the same section when present.
    extras = [
        s.text.strip()
        for s in sources[1:]
        if s.scheme_id == top.scheme_id and s.section == top.section and s.text.strip() != body
    ]
    if extras:
        body = body + "\n\n" + "\n\n".join(extras)
    note = (
        "\n\nThis is an extractive answer from scheme documentation "
        "(LLM generation unavailable). It is not an eligibility decision."
    )
    if language == "hi":
        note = (
            "\n\nयह योजना दस्तावेज़ से लिया गया उत्तर है "
            "(LLM उपलब्ध नहीं)। यह पात्रता का निर्णय नहीं है।"
        )
    return header + body + note


def generate_answer(
    question: str,
    sources: list[SourceChunk],
    *,
    language: str = "en",
    scheme_name: Optional[str] = None,
) -> tuple[str, bool]:
    """
    Returns (answer, used_llm).
    """
    lang_name = LANGUAGE_NAMES.get(language, LANGUAGE_NAMES["en"])
    if not groq_available():
        return extractive_answer(question, sources, language=language), False

    scoped = f" The user is asking about: {scheme_name}." if scheme_name else ""
    user_prompt = (
        f"Question: {question}\n"
        f"{scoped}\n\n"
        f"Scheme chunks:\n{_format_context(sources)}"
    )
    try:
        answer = groq_chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT.format(language=lang_name)},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=700,
        )
        return answer, True
    except GroqUnavailable:
        return extractive_answer(question, sources, language=language), False
