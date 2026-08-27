"""
NidhiPath — Offline Batch Translation (Groq gpt-oss-120b)

Batch-translate scheme content ONCE per language and store the results.
Never translate live per-request (AD: precompute, never compute-on-request).

What gets translated:
    Scheme content fields (name, benefits, eligibility, documents, etc.)
    from both the NSFDC credit records and the welfare corpus.

What does NOT get translated here:
    - UI chrome (buttons/labels/menus): static i18n JSON files live in
      frontend/messages/ — never LLM-translated.
    - Module 4 Q&A answers: generated directly in the user's language in
      one call (see module4_rag/generation.py) — not English-then-translate.

Usage:
    python -m app.translation.batch_translate --lang hi
    python -m app.translation.batch_translate --lang hi --source nsfdc
    python -m app.translation.batch_translate --lang hi --dry-run

Storage:
    Supabase table `scheme_translations (scheme_id, lang, field, text,
    reviewed)` when configured; otherwise data/translations/<lang>.json.

Note: income thresholds and eligibility text MUST get a native-speaker
review pass before production — a mistranslated income cap is not a
cosmetic bug. Translated rows are written with reviewed=false.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

from app.config import settings
from app.modules.module4_rag.llm import GroqUnavailable, groq_available, groq_json

SUPPORTED_LANGS = ("en", "hi", "ta", "te", "kn", "mr")

LANG_NAMES = {
    "hi": "Hindi (Devanagari script)",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "mr": "Marathi (Devanagari script)",
}

# Fields translated per scheme record. Kept deliberately small — these are
# the fields a beneficiary actually reads.
NSFDC_FIELDS = ("scheme_name",)
WELFARE_FIELDS = ("scheme_name",)

TRANSLATE_SYSTEM = """You are a government-scheme translator for Indian languages.
Translate the given JSON fields to {lang}. Rules:
- Keep numbers, currency amounts (₹), percentages, and scheme IDs EXACTLY as-is.
- Keep proper nouns of institutions (NSFDC, MoSJE, bank names) as-is.
- Translate meaning faithfully; do not simplify or omit conditions.
- Return a JSON object with the same keys, values translated.
"""


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


def _extract_fields(scheme: dict, fields: tuple[str, ...]) -> dict[str, str]:
    """Pull translatable string fields; stringify short lists (tags, docs)."""
    out: dict[str, str] = {}
    for field in fields:
        value = scheme.get(field)
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            out[field] = value.strip()
        elif isinstance(value, list) and value and all(isinstance(v, str) for v in value):
            joined = "; ".join(value)
            if joined.strip():
                out[field] = joined
    return out


def _translate_batch(items: dict[str, str], lang: str) -> Optional[dict[str, str]]:
    """Translate one scheme's fields in a single Groq call. None on failure."""
    if not items:
        return None
    lang_name = LANG_NAMES.get(lang, lang)
    try:
        payload = groq_json(
            [
                {"role": "system", "content": TRANSLATE_SYSTEM.format(lang=lang_name)},
                {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
            ],
            temperature=0.0,
        )
    except GroqUnavailable:
        return None
    # Keep only keys we asked for, with non-empty string values.
    return {
        k: str(v).strip()
        for k, v in payload.items()
        if k in items and str(v).strip()
    } or None


def _save_json(lang: str, rows: list[dict]) -> Path:
    out_dir = settings.DATA_DIR / "translations"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{lang}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return out_path


def _save_supabase(rows: list[dict]) -> int:
    """Upsert into scheme_translations. Returns rows written (0 if no Supabase)."""
    from app.db.session import get_supabase_client

    client = get_supabase_client()
    if client is None:
        return 0
    written = 0
    try:
        for i in range(0, len(rows), 200):
            batch = rows[i : i + 200]
            client.table("scheme_translations").upsert(
                batch, on_conflict="scheme_id,lang,field"
            ).execute()
            written += len(batch)
    except Exception:
        return written
    return written


def run(
    lang: str,
    source: str = "all",
    dry_run: bool = False,
    limit: Optional[int] = None,
) -> int:
    """Translate scheme fields for one language. Returns rows produced."""
    if lang not in SUPPORTED_LANGS or lang == "en":
        print(f"Language '{lang}' is not translatable (supported: {SUPPORTED_LANGS[1:]})")
        return 0
    if not groq_available():
        print("GROQ_API_KEY is not configured — batch translation requires Groq.")
        return 0

    jobs: list[tuple[str, dict[str, str]]] = []  # (scheme_id, fields)

    if source in ("all", "nsfdc"):
        for scheme in _load_nsfdc():
            fields = _extract_fields(scheme, NSFDC_FIELDS)
            if fields:
                jobs.append((_scheme_id_of(scheme), fields))

    if source in ("all", "welfare"):
        for scheme in _load_welfare():
            fields = _extract_fields(scheme, WELFARE_FIELDS)
            if fields:
                jobs.append((_scheme_id_of(scheme), fields))

    if limit:
        jobs = jobs[:limit]

    print(f"Translating {len(jobs)} scheme record(s) → {lang}"
          f"{' (dry run)' if dry_run else ''}")

    rows: list[dict] = []
    failed = 0
    for i, (scheme_id, fields) in enumerate(jobs, 1):
        translated = _translate_batch(fields, lang)
        if translated is None:
            failed += 1
            print(f"  [{i}/{len(jobs)}] FAILED {scheme_id}")
            continue
        for field, text in translated.items():
            rows.append({
                "scheme_id": scheme_id,
                "lang": lang,
                "field": field,
                "text": text,
                "reviewed": False,
            })
        print(f"  [{i}/{len(jobs)}] ok {scheme_id}")
        time.sleep(0.2)  # be gentle with the API

    if dry_run:
        print(f"Dry run complete — {len(rows)} rows would be written, {failed} failed.")
        return len(rows)

    if rows:
        json_path = _save_json(lang, rows)
        print(f"JSON written: {json_path}")
        written = _save_supabase(rows)
        if written:
            print(f"Supabase upserted: {written} rows")
        else:
            print("Supabase not configured — JSON file is the source of truth.")

    print(f"Done. {len(rows)} rows, {failed} failures. "
          "REMEMBER: reviewed=false — income/eligibility text needs native-speaker review.")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline batch scheme translation")
    parser.add_argument("--lang", required=True, choices=SUPPORTED_LANGS)
    parser.add_argument("--source", choices=("all", "nsfdc", "welfare"), default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Translate only N schemes")
    args = parser.parse_args()
    run(args.lang, source=args.source, dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    sys.exit(0 if main() is not None else 1)