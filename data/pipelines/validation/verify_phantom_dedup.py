"""
Verification: phantom "th Floor" dedup in channel_partners.json.

Prints a full before/after audit (counts, removed records, merged fields,
short-name survivors, and the complete record list) so the dedup can be
eyeballed like the RRB state-extraction table — nothing is trusted blindly.

Usage:
    python data/pipelines/validation/verify_phantom_dedup.py <before.json> <after.json>
    python data/pipelines/validation/verify_phantom_dedup.py <file.json>            # single snapshot

Exit codes: 0 = audit consistent, 1 = integrity check failed.
"""

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Must mirror PHANTOM_RECORDS in data/pipelines/patch_partner_states.py
PHANTOM_RECORDS = {
    ("PSB_05", "th Floor"),
    ("PSB_07", "th Floor"),
}
KNOWN_LEGITIMATE_SHORT_NAMES = {
    ("PSB_11", "UCO Bank"),
    ("CooperativeBank_109", "Sakar-II"),
}


def load(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def key(p: dict) -> tuple[str, str]:
    return (p.get("partner_id", ""), p.get("partner_name", ""))


def counts_by_type(records: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for p in records:
        t = p.get("partner_type", "?")
        out[t] = out.get(t, 0) + 1
    return dict(sorted(out.items()))


def snapshot_table(records: list[dict], title: str) -> None:
    print(f"\n--- {title}: full record list ({len(records)}) ---")
    print(f"{'#':>3}  {'partner_id':<24} {'partner_name':<40} {'type':<18} {'state':<15} pincode")
    for i, p in enumerate(records, 1):
        marker = "  <-- PHANTOM" if key(p) in PHANTOM_RECORDS else ""
        print(
            f"{i:>3}  {p.get('partner_id', ''):<24} {p.get('partner_name', ''):<40} "
            f"{p.get('partner_type', ''):<18} {p.get('state', ''):<15} {p.get('pincode', '')}{marker}"
        )


def main() -> int:
    problems = 0
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1

    before = load(Path(args[0]))
    after = load(Path(args[1])) if len(args) > 1 else None

    print("=" * 100)
    print("PHANTOM 'th Floor' DEDUP — BEFORE/AFTER AUDIT")
    print("=" * 100)

    print(f"\nRecords before: {len(before)}")
    if after is not None:
        print(f"Records after:  {len(after)}  (delta: {len(after) - len(before)})")

    removed = [p for p in before if key(p) in PHANTOM_RECORDS]
    print(f"\nPhantom records present before: {len(removed)}")
    for p in removed:
        print(
            f"  REMOVE {p['partner_id']:<8} name={p['partner_name']!r} "
            f"address={p.get('address_raw', '')!r} pincode={p.get('pincode', '')!r}"
        )
    if after is not None:
        remaining = [p for p in after if key(p) in PHANTOM_RECORDS]
        print(f"Phantom records remaining after: {len(remaining)}")

    if after is not None:
        print("\n--- Per-type counts (before → after) ---")
        cb, ca = counts_by_type(before), counts_by_type(after)
        for t in sorted(set(cb) | set(ca)):
            print(f"  {t:<22} {cb.get(t, 0):>3} → {ca.get(t, 0):>3}")

    print("\n--- Short-named records (<10 chars) — the length heuristic would touch these, the denylist must not ---")
    snapshots = [("before", before)] + ([("after", after)] if after else [])
    for label, records in snapshots:
        print(f"  [{label}]")
        for p in records:
            if len(p.get("partner_name", "")) < 10:
                k = key(p)
                if k in PHANTOM_RECORDS:
                    tag = "PHANTOM (denylisted)"
                elif k in KNOWN_LEGITIMATE_SHORT_NAMES:
                    tag = "legitimate (known short name) — kept"
                else:
                    tag = "legitimate — kept"
                    if label == "after":
                        problems += 1
                print(f"    {p.get('partner_id', ''):<24} {p.get('partner_name', '')!r:<12} → {tag}")

    if after is not None:
        # Field-level diffs: any after-record with no exact before-twin changed.
        print("\n--- Changed records (expected: only the PSB_05 merge) ---")
        before_exact: list[dict] = list(before)
        for a in after:
            if a in before_exact:
                continue
            print(f"  CHANGED {a.get('partner_id')} — {a.get('partner_name')}")
            print(f"    address_raw: {a.get('address_raw')!r}")
            print(f"    pincode:     {a.get('pincode')!r}")

        # Integrity: every after record must exist identically in before,
        # except the documented PSB_05 merge target.
        print("\n--- Integrity check: every after-record exists unchanged in before ---")
        before_by_key: dict[tuple[str, str], list[dict]] = {}
        for p in before:
            before_by_key.setdefault(key(p), []).append(p)
        for a in after:
            k = key(a)
            if any(c == a for c in before_by_key.get(k, [])):
                continue
            if k == ("PSB_05", "Punjab & Sind Bank"):
                continue  # expected merge target
            problems += 1
            print(f"  UNEXPECTED DIFF: {k}")
        if problems == 0:
            print("  OK — only the documented PSB_05 merge differs.")
        else:
            print(f"  {problems} unexpected difference(s)!")

    if after is not None:
        snapshot_table(before, "BEFORE")
        snapshot_table(after, "AFTER")

    print("\nAudit complete.")
    return 1 if problems > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
