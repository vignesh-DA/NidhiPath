"""
Data Pipeline: Patch partner states in channel_partners.json

1. Extract state from RRB names (e.g., "Bihar Gramin Bank" → "Bihar")
2. Normalize SCA state values (fix \\n artifacts, match canonical INDIAN_STATES)
3. Remove phantom "th Floor" records (PDF multi-line address artifacts) using
   an explicit denylist; merge PSB_05's continuation address/pincode into the
   kept record before removal
4. Write patched data back to data/staging/channel_partners.json

Run: python data/pipelines/patch_partner_states.py
"""

import json
from pathlib import Path

# Canonical Indian states/UTs — must match frontend INDIAN_STATES list exactly
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

# ─── RRB Name → State Mapping ────────────────────────────────────────────────
# Every Indian RRB is named after its state/UT. This mapping covers all 26 RRBs
# in the dataset. Verified against RBI's RRB list.

RRB_NAME_TO_STATE: dict[str, str] = {
    "Bihar Gramin Bank": "Bihar",
    "Jharkhand Gramin Bank": "Jharkhand",
    "Gujarat Gramin Bank": "Gujarat",
    "Rajasthan Gramin Bank": "Rajasthan",
    "Kerala Grameena Bank": "Kerala",
    "Tripura Gramin Bank": "Tripura",
    "Assam Gramin Bank": "Assam",
    "Punjab Gramin Bank": "Punjab",
    "Madhaya Pradesh Gramin Bank": "Madhya Pradesh",  # Typo in source data
    "Puducherry Grama Bank": "Puducherry",
    "Chhattisgarh Gramin Bank": "Chhattisgarh",
    "Meghalaya Rural Bank": "Meghalaya",
    "Maharashtra Gramin Bank": "Maharashtra",
    "Haryana Gramin Bank": "Haryana",
    "Telangana Grameena Bank": "Telangana",
    "Uttar Pradesh Gramin Bank": "Uttar Pradesh",
    "Uttarakhand Gramin Bank": "Uttarakhand",
    "Karnataka Grameena Bank": "Karnataka",
    "Andhra Pradesh Grameena Bank": "Andhra Pradesh",
    "Tamil Nadu Grama Bank": "Tamil Nadu",
    "Himachal Pradesh Gramin Bank": "Himachal Pradesh",
    "West Bengal Gramin Bank": "West Bengal",
    "Manipur Rural Bank": "Manipur",
    "J&K Grameen Bank": "Jammu and Kashmir",
    "Odisha Grameen Bank": "Odisha",
    "Mizoram Rural Bank": "Mizoram",
}

# ─── SCA State Normalization ─────────────────────────────────────────────────
# Fix known data artifacts (newlines, abbreviations)

SCA_STATE_FIXES: dict[str, str] = {
    "Dadra & Nagar\nHaveli, Daman\n& Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Himachal\nPradesh": "Himachal Pradesh",
    "Jammu &\nKashmir": "Jammu and Kashmir",
}


# ─── Phantom Record Cleanup (PDF parsing artifacts) ─────────────────────────
# Multi-line addresses in the source PDF were split into separate records whose
# partner_name is the line fragment "th Floor" (from "4th Floor" / "7th Floor").
# Cleanup uses an EXPLICIT DENYLIST, not a length heuristic — a length rule
# (e.g. name < 10 chars) would also hit legitimate short-named partners such
# as "UCO Bank" (PSB_11) and "Sakar-II" (CooperativeBank_109).

PHANTOM_RECORDS: set[tuple[str, str]] = {
    ("PSB_05", "th Floor"),  # continuation of Punjab & Sind Bank's address
    ("PSB_07", "th Floor"),  # Vadodara fragment; the kept PSB_07 record (Indian
    #                          Bank Corporate Office, Chennai) is already complete
}

# Phantom records whose address/pincode continue the kept record's address and
# must therefore be merged into it before removal.
PHANTOM_MERGE_INTO_KEPT: set[str] = {"PSB_05"}


def dedupe_phantom_records(partners: list[dict]) -> tuple[list[dict], dict]:
    """Remove phantom "th Floor" records; merge PSB_05's continuation address.

    Returns (cleaned_list, stats). Idempotent: re-running on already-clean
    data removes nothing and merges nothing.
    """
    stats = {"phantoms_removed": 0, "phantoms_merged": 0}

    def is_phantom(p: dict) -> bool:
        return (p.get("partner_id", ""), p.get("partner_name", "")) in PHANTOM_RECORDS

    # Index legitimate records by partner_id so phantom fragments can merge in.
    kept_by_id: dict[str, dict] = {
        p.get("partner_id", ""): p for p in partners if not is_phantom(p)
    }

    for partner in partners:
        if not is_phantom(partner):
            continue
        stats["phantoms_removed"] += 1
        pid = partner.get("partner_id", "")
        kept = kept_by_id.get(pid)
        if kept is None or pid not in PHANTOM_MERGE_INTO_KEPT:
            continue
        phantom_addr = partner.get("address_raw", "").strip()
        kept_addr = kept.get("address_raw", "").strip()
        if phantom_addr and phantom_addr not in kept_addr:
            kept["address_raw"] = (
                f"{kept_addr}, {phantom_addr}" if kept_addr else phantom_addr
            )
            stats["phantoms_merged"] += 1
        phantom_pin = partner.get("pincode", "").strip()
        if phantom_pin and not kept.get("pincode", "").strip():
            kept["pincode"] = phantom_pin

    cleaned = [p for p in partners if not is_phantom(p)]
    return cleaned, stats


def patch_partners(input_path: Path) -> tuple[list[dict], dict]:
    """Patch partner records. Returns (patched_list, stats)."""
    with open(input_path, "r", encoding="utf-8") as f:
        partners = json.load(f)

    # ── Phantom cleanup first, so the state-patching loop never sees them ──
    partners, phantom_stats = dedupe_phantom_records(partners)

    stats = {
        "rrb_patched": 0,
        "sca_normalized": 0,
        "total": len(partners),
        **phantom_stats,
    }

    for partner in partners:
        ptype = partner.get("partner_type", "").strip()
        pname = partner.get("partner_name", "").strip()
        current_state = partner.get("state", "").strip()

        # ── RRB: extract state from name ──
        if ptype == "RRB":
            if not current_state and pname in RRB_NAME_TO_STATE:
                partner["state"] = RRB_NAME_TO_STATE[pname]
                stats["rrb_patched"] += 1
            elif not current_state:
                print(f"  ⚠ RRB not in mapping: '{pname}' (partner_id={partner.get('partner_id')})")

        # ── SCA: normalize state ──
        elif ptype == "SCA":
            if current_state in SCA_STATE_FIXES:
                partner["state"] = SCA_STATE_FIXES[current_state]
                stats["sca_normalized"] += 1
            elif current_state and current_state not in INDIAN_STATES:
                print(f"  ⚠ SCA state not in canonical list: '{current_state}' → '{pname}'")

    return partners, stats


def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "staging" / "channel_partners.json"

    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}")
        return

    print(f"[READ] Reading: {input_path}")
    patched, stats = patch_partners(input_path)

    # Write back
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(patched, f, indent=2, ensure_ascii=False)

    print(f"[OK] Patched {stats['rrb_patched']} RRB states, normalized {stats['sca_normalized']} SCA states")
    print(
        f"[OK] Removed {stats['phantoms_removed']} phantom records, "
        f"merged {stats['phantoms_merged']} continuation address(es)"
    )
    print(f"   Total partners: {stats['total']}")
    print(f"[WRITE] Written to: {input_path}")


if __name__ == "__main__":
    main()
