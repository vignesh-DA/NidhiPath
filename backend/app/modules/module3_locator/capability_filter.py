"""
Module 3 — Capability Filter (Step 1 of 4)

Direct pass-through from Module 1 output: filter partners whose
partner_type is in the matched scheme's channel_partners[] list.

Zero ambiguity — already verified working against a real
Karnataka/Term Loan test case.
"""

import json
from pathlib import Path
from typing import Optional


_partners_cache: Optional[list[dict]] = None


def load_channel_partners(data_dir: Optional[Path] = None) -> list[dict]:
    """Load channel partners from JSON. Caches in-memory after first load."""
    global _partners_cache
    if _partners_cache is not None:
        return _partners_cache

    if data_dir is None:
        from app.config import settings
        data_dir = settings.DATA_DIR

    path = data_dir / "staging" / "channel_partners.json"
    if not path.exists():
        raise FileNotFoundError(
            f"channel_partners.json not found at {path}. "
            f"Place your data file in data/staging/"
        )

    with open(path, "r", encoding="utf-8") as f:
        _partners_cache = json.load(f)

    return _partners_cache


def clear_partners_cache():
    """Clear cached partners — useful for testing."""
    global _partners_cache
    _partners_cache = None


def filter_by_capability(
    scheme_channel_partners: list[str],
    partners: Optional[list[dict]] = None,
    data_dir: Optional[Path] = None,
) -> list[dict]:
    """
    Step 1: Capability filter.

    Filter partners by partner_type IN matched_scheme.channel_partners[].
    Direct pass-through from Module 1 output.

    Args:
        scheme_channel_partners: List of partner types from the matched scheme
                                 (e.g., ["SCA", "PSB", "RRB"])
        partners: Pre-loaded partners list (for testing)
        data_dir: Data directory path override

    Returns:
        List of partner records whose partner_type is in the scheme's list
    """
    if partners is None:
        partners = load_channel_partners(data_dir)

    # Normalize to uppercase for consistent matching
    allowed_types = {t.strip().upper() for t in scheme_channel_partners}

    return [
        p for p in partners
        if p.get("partner_type", "").strip().upper() in allowed_types
    ]
