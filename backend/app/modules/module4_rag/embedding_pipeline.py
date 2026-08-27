"""
Module 4 — Batch embedding pipeline (versioned, precomputed).

Contextual prefix: prepend `scheme_name + region + section` at embed-time
only — it is NOT stored in the raw chunk text. This stops near-identical
eligibility bullets across states from collapsing in vector space.

Embeddings are a deterministic hashed n-gram vector (no extra ML deps).
At ~2,600 chunks, this plus keyword overlap is sufficient — do not add
rerankers or multi-query retrieval.

When Supabase/pgvector is configured, embeddings are also upserted.
They are never computed on-request for static scheme content (AD-8).
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Optional

from app.modules.module4_rag.models import SchemeChunk

EMBEDDING_VERSION = "hash-v1"
EMBEDDING_DIM = 384

_TOKEN = re.compile(r"[\w₹]+", re.UNICODE)


def _hash_to_index_sign(payload: bytes, algo: str) -> tuple[int, float]:
    digest = hashlib.md5(payload).digest() if algo == "md5" else hashlib.sha1(payload).digest()
    integer = int.from_bytes(digest[:8], "big")
    index = integer % EMBEDDING_DIM
    sign = 1.0 if (integer >> 8) & 1 else -1.0
    return index, sign


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def contextual_prefix(chunk: SchemeChunk) -> str:
    """Embed-time prefix only — never written into chunk.text."""
    region = chunk.region or "National"
    return f"{chunk.scheme_name} | {region} | {chunk.section}: "


def embed_text(text: str) -> list[float]:
    """Hashed unigram + character-trigram embedding, L2-normalized."""
    vec = [0.0] * EMBEDDING_DIM
    normalized = (text or "").lower()
    if not normalized.strip():
        return vec

    for token in _TOKEN.findall(normalized):
        index, sign = _hash_to_index_sign(token.encode("utf-8"), "md5")
        vec[index] += sign

    compact = re.sub(r"\s+", " ", normalized)
    for i in range(len(compact) - 2):
        gram = compact[i : i + 3]
        index, sign = _hash_to_index_sign(gram.encode("utf-8"), "sha1")
        vec[index] += 0.5 * sign

    return _l2_normalize(vec)


def embed_chunk(chunk: SchemeChunk) -> SchemeChunk:
    """Embed one chunk with the contextual prefix. Mutates a copy."""
    prefixed = contextual_prefix(chunk) + chunk.text
    chunk.embedding = embed_text(prefixed)
    chunk.embedding_version = EMBEDDING_VERSION
    return chunk


def embed_chunks(chunks: list[SchemeChunk]) -> list[SchemeChunk]:
    """Batch-embed. Pure CPU, no network."""
    return [embed_chunk(c) for c in chunks]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))  # already L2-normalized


# ─── In-memory index (precomputed at process start / first request) ──────────

_index: Optional[list[SchemeChunk]] = None


def reset_index() -> None:
    """Clear the in-memory index — used by tests."""
    global _index
    _index = None


def get_index() -> Optional[list[SchemeChunk]]:
    return _index


def set_index(chunks: list[SchemeChunk]) -> list[SchemeChunk]:
    global _index
    _index = chunks
    return chunks


def build_index(
    nsfdc_schemes: Optional[list[dict]] = None,
    welfare_schemes: Optional[list[dict]] = None,
    *,
    persist_to_supabase: bool = False,
) -> list[SchemeChunk]:
    """
    Chunk + embed the corpora and hold them in memory.

    Loads JSON files when scheme lists are not passed in.
    """
    from app.modules.module4_rag.chunking import chunk_schemes

    if nsfdc_schemes is None:
        try:
            from app.modules.module1_recommender.credit_engine import load_nsfdc_schemes
            nsfdc_schemes = load_nsfdc_schemes()
        except FileNotFoundError:
            nsfdc_schemes = []

    if welfare_schemes is None:
        try:
            from app.modules.module1_recommender.welfare_engine import load_welfare_schemes
            welfare_schemes = load_welfare_schemes()
        except FileNotFoundError:
            welfare_schemes = []

    chunks = embed_chunks(chunk_schemes(nsfdc_schemes, welfare_schemes))
    set_index(chunks)

    if persist_to_supabase:
        persist_index_to_supabase(chunks)

    return chunks


def ensure_index() -> list[SchemeChunk]:
    """Lazy-build on first use. Safe to call from request handlers."""
    existing = get_index()
    if existing is not None:
        return existing
    return build_index()


def persist_index_to_supabase(chunks: list[SchemeChunk]) -> int:
    """
    Optional upsert into scheme_chunks (pgvector). No-op if Supabase is
    not configured. Failures are swallowed so the in-memory path still works.
    """
    from app.db.session import get_supabase_client

    client = get_supabase_client()
    if client is None:
        return 0

    rows = [
        {
            "chunk_id": c.chunk_id,
            "scheme_id": c.scheme_id,
            "scheme_name": c.scheme_name,
            "region": c.region,
            "section": c.section,
            "section_index": c.section_index,
            "sibling_count": c.sibling_count,
            "was_subsplit": c.was_subsplit,
            "text": c.text,
            "embedding": c.embedding,
            "embedding_version": c.embedding_version,
            "source": c.source,
        }
        for c in chunks
    ]

    # Upsert in batches of 200 to stay under payload limits.
    written = 0
    batch_size = 200
    try:
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            client.table("scheme_chunks").upsert(batch, on_conflict="chunk_id").execute()
            written += len(batch)
    except Exception:
        return written
    return written
