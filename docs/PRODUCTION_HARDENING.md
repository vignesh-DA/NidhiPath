# Production Hardening Checklist — NidhiPath

These items are real production requirements. None of them block a working demo, and building them during the hackathon is scope creep. They are listed here for completeness and post-hackathon planning.

---

## Critical (Must-Have Before Real Users)

| # | Item | Requirement | Status |
|---|------|-------------|--------|
| 1 | **NPA/Utilization Data** | Real feed via formal NSFDC data-sharing agreement. Mocked data cannot ship to real users. | ❌ Mocked |
| 2 | **Sensitive Data (DPDP Act)** | Caste/income are DPDP-Act-covered. Implement: encryption at rest, RLS, explicit consent flow, retention policy, audit logging. | ❌ Not implemented |
| 3 | **Flagged Records** | Live-checked (see "Known Data Flags" below): 5 scheme records carry `needs_review` in the staged corpus; `channel_partners.json` carries no `data_quality` field at all. The historical "25 scheme flags + 8 partner flags" counts describe an audit-pipeline run whose artifacts were never ported into this repo. | ⚠️ Claim corrected, flags unresolved |
| 4 | **Multi-lingual Review** | Hindi/regional translations of income thresholds, eligibility text, document requirements need native-speaker review. A mistranslated income threshold is not a cosmetic bug. | ❌ Machine-generated |
| 5 | **SMS OTP** | TRAI DLT sender-ID registration mandatory for real SMS delivery in India. | ❌ Not registered |

## High Priority

| # | Item | Requirement | Status |
|---|------|-------------|--------|
| 6 | **Geocoding** | Full address geocoding, not pincode-centroid. Required for Module 3 proximity ranking. | ❌ Blocked |
| 7 | **IFSC Refresh** | Scheduled monthly job against live RBI source. IFSC data goes stale. | ❌ Not implemented |
| 8 | **Income Cap Sync** | Scheduled live-sync from nsfdc.nic.in with change alerts. Currently hardcoded to ₹5,00,000. | ❌ Hardcoded |
| 9 | **Embedding Refresh** | Versioned pipeline triggered on content updates, not manual re-runs. | ❌ Manual |

## Operational

| # | Item | Requirement | Status |
|---|------|-------------|--------|
| 10 | **Environment Split** | Staging/production separation, automated backups, monitoring. | ❌ Single env |
| 11 | **Error Monitoring** | Sentry or equivalent for both frontend and backend error tracking. | ❌ Not set up |
| 12 | **Rate Limiting** | API rate limiting to prevent abuse, especially on LLM endpoints. | ❌ Not implemented |
| 13 | **Logging & Audit** | Structured logging with request tracing. Audit trail for all eligibility decisions. | ❌ Basic only |
| 14 | **Load Testing** | Verify performance under concurrent users, especially Module 4 LLM calls. | ❌ Not tested |

---

## Known Data Flags to Resolve

### channel_partners.json (8 of 92 flagged — HISTORICAL COUNT)

> **Repo status (live-checked):** the `channel_partners.json` in this repo has NO
> `data_quality` field at all — the 8-flag count refers to an audit pipeline
> (`docx_extraction_pipeline.py`, `validation/report` + `review_required.json`
> outputs) that was never ported into this repo. **Do not cite "8 flags" as a
> current fact.** The underlying artifacts themselves are still visible in the
> data: zero-width-joiner/encoding debris persists in `address_raw` values
> (e.g., record `NBFCMFI_01`).
- **Zero-width-joiner characters** splitting "Nth Floor" into phantom records
- **Two-column PDF bleed** merging adjacent entries
- Fix before Module 3 ships past demo stage

### schemes_production_deduped.json (25 flagged — HISTORICAL; 5 LIVE `needs_review`)

> **Repo status (live-checked):** of 377 records, `data_quality.field_validation_status`
> is `passed_with_warnings` on 366, `passed` on 6, and **`needs_review` on 5**:
> `funeral-assistance-scheme-madhya-pradesh-*`, `4-direct-lending-scheme-punjab`,
> `empowering-schedule-tribe-...-goa`, `reimbursement-of-tution-fee-...-delhi`
> (50 warnings), `burial-ground-...-tamil-nadu`. All records are still loaded
> and served with their flags intact — nothing is suppressed or resolved.
- 24 cosmetic issues
- 1 real: `credit-enhancement-guarantee-scheme...`'s department field needs a second look

### IFSC.csv
- `BANK` column is blank on many rows
- Fuzzy-matching partner names against it will miss records
- Key off the IFSC prefix instead where possible

### NBFC-MFIs
- Absent from IFSC.csv entirely
- Will always resolve to a single HQ pin, never real branch-level proximity
- Must be disclosed in UI (currently implemented)
