"""
Module 4 — Retrieval.

1. Metadata pre-filter to the matched scheme_id FIRST (2,600 → 5–7 chunks)
2. Only then rank by embedding similarity + keyword overlap
3. Sibling-chunk fetch: if a section was sub-split, always fetch ALL
   sibling chunks for that section once one is deemed relevant.
   Never trust top-1 similarity alone. This failed silently on a real
   example during testing; the fix is mandatory.

At this corpus size, plain keyword match is nearly as good as vector
search — the hybrid score uses both.
"""

from __future__ import annotations

import re
from typing import Optional

from app.modules.module4_rag.embedding_pipeline import (
    cosine_similarity,
    embed_text,
    ensure_index,
)
from app.modules.module4_rag.models import SchemeChunk, SourceChunk

_TOKEN = re.compile(r"[\w₹]+", re.UNICODE)

NSFDC_BOOST = 0.12
KEYWORD_WEIGHT = 0.4
VECTOR_WEIGHT = 0.6


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text or "") if len(t) > 1}


def _keyword_overlap(query: str, chunk_text: str) -> float:
    q = _tokenize(query)
    if not q:
        return 0.0
    c = _tokenize(chunk_text)
    return len(q & c) / len(q)


def _score(query: str, query_vec: list[float], chunk: SchemeChunk) -> float:
    vector = cosine_similarity(query_vec, chunk.embedding) if chunk.embedding else 0.0
    keyword = _keyword_overlap(query, f"{chunk.scheme_name} {chunk.section} {chunk.text}")
    score = VECTOR_WEIGHT * vector + KEYWORD_WEIGHT * keyword
    if chunk.source == "nsfdc":
        score += NSFDC_BOOST
    return score


def prefilter(
    chunks: list[SchemeChunk],
    scheme_id: Optional[str] = None,
    source: Optional[str] = None,
) -> list[SchemeChunk]:
    """Metadata pre-filter. scheme_id is applied first when present."""
    filtered = chunks
    if scheme_id:
        sid = str(scheme_id)
        filtered = [c for c in filtered if c.scheme_id == sid]
    if source:
        filtered = [c for c in filtered if c.source == source]
    return filtered


def fetch_siblings(hits: list[SchemeChunk], corpus: list[SchemeChunk]) -> list[SchemeChunk]:
    """
    Expand each hit to the full section when that section was sub-split.
    Preserves first-seen section order; de-duplicates by chunk_id.
    """
    by_key: dict[tuple[str, str], list[SchemeChunk]] = {}
    for chunk in corpus:
        by_key.setdefault((chunk.scheme_id, chunk.section), []).append(chunk)
    for siblings in by_key.values():
        siblings.sort(key=lambda c: c.section_index)

    seen_sections: set[tuple[str, str]] = set()
    seen_ids: set[str] = set()
    expanded: list[SchemeChunk] = []

    for hit in hits:
        key = (hit.scheme_id, hit.section)
        if key in seen_sections:
            continue
        seen_sections.add(key)
        group = by_key.get(key, [hit])
        # Always take the full section group if any member was sub-split.
        take = group if (hit.was_subsplit or any(c.was_subsplit for c in group)) else [hit]
        for chunk in take:
            if chunk.chunk_id in seen_ids:
                continue
            seen_ids.add(chunk.chunk_id)
            expanded.append(chunk)
    return expanded


def retrieve(
    query: str,
    *,
    scheme_id: Optional[str] = None,
    source: Optional[str] = None,
    top_k: int = 5,
    chunks: Optional[list[SchemeChunk]] = None,
) -> list[tuple[SchemeChunk, float]]:
    """
    Retrieve ranked chunks.

    When scheme_id is set, the candidate set is that scheme's 5–7 chunks
    and ranking is almost a formality. Sibling expansion still runs.
    """
    corpus = chunks if chunks is not None else ensure_index()
    candidates = prefilter(corpus, scheme_id=scheme_id, source=source)
    if not candidates:
        return []

    query_vec = embed_text(query)
    ranked = sorted(
        ((chunk, _score(query, query_vec, chunk)) for chunk in candidates),
        key=lambda pair: pair[1],
        reverse=True,
    )

    # Take a slightly wider window so sibling expansion can fill a section.
    window = [chunk for chunk, _score_val in ranked[: max(top_k, 3)]]
    expanded = fetch_siblings(window, candidates)
    score_map = {chunk.chunk_id: score for chunk, score in ranked}
    return [(chunk, score_map.get(chunk.chunk_id, 0.0)) for chunk in expanded]


def retrieve_as_sources(
    query: str,
    *,
    scheme_id: Optional[str] = None,
    source: Optional[str] = None,
    top_k: int = 5,
    chunks: Optional[list[SchemeChunk]] = None,
) -> list[SourceChunk]:
    hits = retrieve(
        query,
        scheme_id=scheme_id,
        source=source,
        top_k=top_k,
        chunks=chunks,
    )
    return [
        SourceChunk(
            chunk_id=chunk.chunk_id,
            scheme_id=chunk.scheme_id,
            scheme_name=chunk.scheme_name,
            section=chunk.section,
            text=chunk.text,
            score=round(score, 4),
        )
        for chunk, score in hits
    ]
