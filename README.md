<div align="center">

# NidhiPath

**AI-Driven Scheme Matching for Marginalized Entrepreneurs**

Concessional credit discovery, transparent repayment planning, and partner routing
for Scheduled Caste beneficiaries — built for the
**Ministry of Social Justice and Empowerment (MoSJE)**.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16%20App%20Router-000000?logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?logo=typescript&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Postgres-3FCF8E?logo=supabase&logoColor=white)
![Tests](https://img.shields.io/badge/pytest-100%20passing-16A34A)

</div>

---

## Why NidhiPath Exists

A beneficiary with a business idea faces three questions the current system answers poorly:

1. **"Which scheme is mine?"** — NSFDC operates multiple concessional credit schemes with
   overlapping cost ranges, income caps, and purpose rules, alongside hundreds of state and
   central welfare schemes with their own eligibility criteria.
2. **"What will repayment actually look like?"** — published terms (max loan, cost coverage,
   moratorium, installment cadence) rarely translate into a personal number a borrower can plan around.
3. **"Where do I physically apply?"** — credit is disbursed through authorized channel partners
   (SCAs, PSBs, RRBs, NBFC-MFIs), and finding the right one for a given state and scheme is opaque.

NidhiPath answers all three in a single guided flow, in multiple languages — and it does so
with **auditable, deterministic logic** wherever money or eligibility is involved.

## Design Principles

These are architectural commitments, not aspirations (rationale in
[docs/ARCHITECTURE_DECISIONS.md](docs/ARCHITECTURE_DECISIONS.md), AD-1 through AD-12):

| # | Principle | In practice |
|---|-----------|-------------|
| 1 | **Deterministic eligibility, never ML** | Modules 1–2 are pure rule engines. No model decides who qualifies for a scheme. |
| 2 | **Two tiers, never merged** | NSFDC credit matches (exact) and welfare matches (approximate) are always structurally and visually separate. |
| 3 | **Ranked lists, never a single match** | Cost ranges overlap — output is always a ranked list with human-readable match reasons. |
| 4 | **Scheme-owned parameters, server-enforced** | Interest rate, loan caps, tenure, moratorium, and installment cadence are resolved server-side from the authoritative record; a tampered client cannot buy a cheaper rate. |
| 5 | **Graceful degradation** | Modules 1–3 run with zero AI dependency. If the LLM is down, the financial-inclusion path still works end-to-end. |
| 6 | **Disclosed assumptions** | Every calculation ships its assumptions inside the response — moratorium interest treatment, payment cadence, derived caps. No silent math. |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Next.js 16 (App Router)                   │
│   /intake → /recommendation → /calculator → /locator         │
│   /qa (scheme-scoped RAG chat)          i18n: en · hi        │
└─────────────────────────────┬────────────────────────────────┘
                              │ REST / JSON
┌─────────────────────────────▼────────────────────────────────┐
│                     FastAPI  ·  /api/v1                      │
│                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐  │
│  │  Module 1  │ │  Module 2  │ │  Module 3  │ │  Module 4 │  │
│  │ Recommender│ │ Calculator │ │  Locator   │ │ LLM + RAG │  │
│  │rule engine │ │ pure math  │ │  filters   │ │   Groq    │  │
│  └──────┬─────┘ └──────┬─────┘ └──────┬─────┘ └─────┬─────┘  │
└─────────┼──────────────┼──────────────┼─────────────┼────────┘
          ▼              ▼              ▼             ▼
    data/staging    scheme-owned    partners +    chunk index +
    382 schemes     params (rate,   IFSC ref.     Groq gpt-oss-120b
    (5 credit +     caps, cadence)  90 records    (Module 4 only)
    377 welfare)
```

**The one thing to remember:** AI is a convenience layer on top of a deterministic core,
never a dependency of it.

---

## Modules

| Module | What it does | AI dependency | Key guarantee |
|--------|--------------|:---:|---------------|
| **1 · Scheme Recommender** | Matches a user profile (income, state, caste, project type, education status) against 5 NSFDC credit schemes (primary tier) and 377 welfare schemes (secondary tier) | ❌ None | Ranked matches with per-match reasons; tiers never merged; income cap enforced |
| **2 · Financial Calculator** | EMI / quarterly installment calculation with scheme-enforced caps, moratorium handling, and full amortization schedule | ❌ None | Interest rate is scheme-owned and never user-editable; every assumption disclosed in the response |
| **3 · Partner Locator** | Shortlists authorized channel partners via a 4-step pipeline: scheme capability → state eligibility → portfolio health → location-tier ranking (district / state / national) | ❌ None | Deterministic pipeline; every step's outcome, rank tier, and known gaps disclosed in the response |
| **4 · AI Intake + Q&A** | Free-text → structured profile extraction (cost, income, project type) and scheme-scoped Q&A with cited sources | ✅ Groq | LLM output is validated and heuristic-backed; extractive fallback when LLM unavailable |

### Repayment cadence, handled correctly

NSFDC's Micro Finance Scheme officially repays in **quarterly installments** — the calculator
treats cadence as a scheme-owned parameter: MFS resolves to quarterly (periodic rate =
annual/4, whole-quarter month mapping), everything else to monthly, and any monthly-cadence
result explicitly discloses the limitation in its `assumption_note`. Golden value pinned by
test: ₹1,00,000 @ 6.5% p.a. / 3 years → **₹9,239.54/quarter** (12 installments), not 3 × ₹3,064.90.
See [AD-11](docs/ARCHITECTURE_DECISIONS.md).

---

## API Reference

All endpoints live under `/api/v1`. Interactive docs at
[localhost:8000/docs](http://localhost:8000/docs) (Swagger) and `/redoc` once the backend runs.

| Method | Endpoint | Purpose | AI |
|:---:|----------|---------|:---:|
| `POST` | `/api/v1/recommend` | Two-tier scheme matching (NSFDC credit + welfare) from a structured profile | ❌ |
| `POST` | `/api/v1/calculate-emi` | EMI with scheme-enforced caps, moratorium, quarterly/monthly cadence, optional amortization schedule | ❌ |
| `POST` | `/api/v1/locate-partners` | Partner shortlist: capability → eligibility → health → location-tier ranking | ❌ |
| `POST` | `/api/v1/intake/extract` | Free-text story → structured profile (cost, income, state, caste, project type) | ✅ |
| `POST` | `/api/v1/qa` | Scheme-scoped Q&A with cited, section-level sources | ✅ |

**Integrity rule (calculator):** when `scheme_id` matches an NSFDC record, all scheme-owned
parameters — rate, max loan, coverage %, tenure, moratorium, cadence — are resolved
server-side and client-supplied values are overridden.

---

## Quick Start

**Prerequisites:** Python 3.11+ · Node.js 18+ · (optional) a Supabase project ·
a Groq API key — required only for Module 4.

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: [http://localhost:3000](http://localhost:3000)

### Environment

```bash
cp .env.example .env   # then fill in your values
```

| Variable | Required | Purpose |
|----------|:---:|---------|
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY` | — | Supabase Postgres connection |
| `DATABASE_URL` | — | Direct Postgres fallback (used if Supabase is not configured) |
| `GROQ_API_KEY` | Module 4 only | LLM intake extraction + RAG Q&A + translation |
| `GROQ_MODEL` | — | Defaults to `gpt-oss-120b` when unset |
| `CORS_ORIGINS` | — | Allowed frontend origins (default: `localhost:3000`) |
| `APP_ENV` | — | `development` / `production` |
| `DATA_DIR` | — | Data root (default: `../data`) |

> Modules 1–3 run fully with an empty `.env` — no database or API key needed for the core demo path.

### Data Files

Place these before starting the backend (see [data/](data/)):

| File | Records | Role |
|------|:---:|------|
| `data/staging/nsfdc_schemes.json` | 5 | Primary tier — NSFDC credit schemes (rate, caps, moratorium, cadence, `purpose` tags) |
| `data/staging/schemes_production_deduped.json` | 377 | Secondary tier — state & central welfare schemes with structured income/caste/state criteria |
| `data/staging/channel_partners.json` | 90 | Locator — SCA / PSB / RRB / NBFC-MFI partners |
| `data/reference/ifsc.csv` | 182K+ | Bank branch reference (keyed by IFSC prefix, not BANK column) |

> **Data governance:** welfare-scheme records flagged `needs_review` (5 live) are served
> intact with their flags — nothing suppressed, nothing silently "fixed". Data cleanup runs
> are audited with before/after scripts rather than trusted — e.g.
> `data/pipelines/validation/verify_phantom_dedup.py` prints the full record-level
> diff for the phantom-artifact dedup. Rules: never edit `data/staging/` by hand;
> patch scripts are idempotent and re-runnable.

---

## Project Structure

```
NidhiPath/
├── backend/                      # FastAPI (Python 3.11+, typed, Pydantic)
│   └── app/
│       ├── main.py               # App entrypoint — mounts /api/v1 routers
│       ├── config.py             # Environment configuration
│       ├── api/                  # Route handlers (thin — no business logic)
│       │   ├── routes_recommender.py
│       │   ├── routes_calculator.py
│       │   ├── routes_locator.py
│       │   └── routes_rag.py
│       ├── modules/              # Business logic — one dir per module, each
│       │   ├── module1_recommender/   #   with its own tests/
│       │   ├── module2_calculator/
│       │   ├── module3_locator/
│       │   └── module4_rag/
│       ├── db/                   # Session + migrations (Supabase / Postgres)
│       └── translation/          # Batch translation pipeline (en → hi)
├── frontend/                     # Next.js 16 App Router (TypeScript strict)
│   ├── app/                      # intake · recommendation · calculator ·
│   │                             # locator · qa · login
│   ├── lib/                      # Typed API client + shared types
│   └── messages/                 # i18n dictionaries (en, hi)
├── data/
│   ├── staging/                  # Audited production JSON — do not edit manually
│   ├── reference/                # IFSC CSV
│   ├── pipelines/                # Extraction + patch scripts (re-runnable, idempotent)
│   │   └── validation/           # Audit scripts (e.g. verify_phantom_dedup.py)
├── docs/
│   ├── ARCHITECTURE_DECISIONS.md # AD-1 … AD-12, each with rationale (+ falsifiers)
│   ├── PRODUCTION_HARDENING.md   # Gap register + known data flags
│   └── LOCATOR_MANUAL_VERIFICATION.md  # 9-scenario browser test protocol
└── .env.example
```

---

## Testing

```bash
cd backend
python -m pytest -v          # full suite
python -m pytest -q          # quiet
```

**100 tests across Modules 1–4**, all passing. Highlights:

- **Module 1** — credit-engine routing (`purpose` tags, income cap, cost coverage) and the
  welfare rule engine (state/central matching, income operators incl. boundary cases,
  caste aliasing, education keywords) plus a smoke test against the real 377-scheme corpus.
- **Module 2** — golden-value EMI tests, cap/moratorium/tenure behavior, amortization
  schedule integrity, and the quarterly-installment suite for the Micro Finance Scheme
  (₹9,239.54 golden value + the mandated monthly-cadence disclosure line).
- **Module 3** — pipeline stage disclosure and location-tier ranking contracts
  (district / state / national ordering, `proximity_status` states, health deprioritization).
- **Module 4** — chunking, sibling-chunk retrieval, heuristic fallback when the LLM is down.

The welfare-engine tests double as the guard for the *no-RAG-for-eligibility* rule:
every eligibility assertion exercises a deterministic rule, never a similarity score.

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/ARCHITECTURE_DECISIONS.md](docs/ARCHITECTURE_DECISIONS.md) | AD-1 … AD-12 — income cap (₹5,00,000 per problem statement), deterministic eligibility, sibling-chunk retrieval, quarterly cadence (AD-11), and location precedence + TTL with an explicit falsifier clause (AD-12) |
| [docs/PRODUCTION_HARDENING.md](docs/PRODUCTION_HARDENING.md) | Gap register with live-checked status — what is production-ready, what is disclosed-stub, which data flags are real vs historical, and tracked lint debt |
| [docs/LOCATOR_MANUAL_VERIFICATION.md](docs/LOCATOR_MANUAL_VERIFICATION.md) | 9-scenario browser protocol for what automated checks can't reach: permission prompts, TTL expiry, and the legacy-cache regression test |

---

## Known Limitations

Stated plainly, because a demo that hides its edges is worth less than one that knows them:

- **Partner proximity ranking is tier-based, not true geo-distance** — `rank_by_proximity()`
  ranks partners into disclosed tiers (district match → state match → national) and reports
  `proximity_status: "tier_ranking"`; without a user state it reports `"unavailable"`. True
  lat/long KNN (PostGIS `<->`) stays blocked on geocoding and is deliberately built last,
  per the project's build order.
- **Partner portfolio-health metrics are mocked** — every partner currently reports fixed
  NPA/utilization values; the filter pipeline is real, the data behind step 3 is not yet.
- **5 welfare-scheme records carry live `needs_review` flags** and are still served with them
  (nothing suppressed, nothing silently fixed). The channel-partner file carries no
  `data_quality` field — the historical "25 + 8 flags" audit artifacts were never ported
  into this repo. Details in [PRODUCTION_HARDENING.md](docs/PRODUCTION_HARDENING.md).
- **Embeddings are deterministic hash-based (`hash-v1`), held in memory** — a deliberate
  zero-dependency choice for the demo; a pgvector migration is the planned upgrade path.

---

## License

TBD

---

## Acknowledgments

- **NSFDC** — National Scheduled Castes Finance and Development Corporation
- **MoSJE** — Ministry of Social Justice and Empowerment
- **PM-SURAJ Portal** — the actual loan application processing destination
- **Groq** — LLM inference for Module 4
---

## Demo Script

The frontend guides the user through the exact flow the problem statement describes:

1. **/intake** — tell your story in free text (any language). Module 4's LLM extracts
   cost, income, state, caste, and project type; if the LLM is unavailable, the form path
   takes over automatically.
2. **/recommendation** — see the two-tier result: exact NSFDC credit matches on top
   (with EMI-relevant terms), approximate welfare matches below, clearly labeled as such.
   Pick a scheme.
3. **/calculator** — watch the number: scheme-owned rate/limits applied server-side,
   moratorium handled, and for the Micro Finance Scheme a **quarterly installment**
   (₹9,239.54 on the golden config), with caps and assumptions shown, never hidden.
4. **/locator** — get the partner shortlist for your state and scheme, with every filter
   stage disclosed.
5. **/qa** — ask anything about the selected scheme; answers cite section-level sources
   fetched with the sibling-chunk rule, so no half-sentence context ever reaches the LLM.

Every step feeds the next: intake → recommend → calculate → locate → ask.
