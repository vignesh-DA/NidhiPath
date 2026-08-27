### This is the problem statemnt

AI-Driven Scheme Matching for Marginalized Entrepreneurs
Organisation: Ministry of Social Justice and Empowerment (MoSJE) | Department: Department of Social Justice and
Empowerment
• Background To promote the socio-economic empowerment of the Scheduled Caste (SC) population, the
government provides concessional financial assistance and educational loans. Beneficiaries with an annual
family income of up to ?5.00 Lakhs are eligible for various tailored financial products covering up to 90% of
their project or education costs at highly concessional interest rates (typically 6.5% to 8% per annum).
However, direct loan applications are not entertained. Instead, funds are routed through a 'Channel Finance
System' comprising over 100 Channel Partners, including State Channelizing Agencies (SCAs), Public Sector
Banks (PSBs), Regional Rural Banks (RRBs), and NBFC-MFIs. • Challenge Citizens often lack awareness
regarding which specific credit scheme fits their needs—such as distinguishing between a Micro Finance
Scheme for small projects (up to ?1.40 lakh), a Term Loan for larger projects (up to ?50.00 lakh), or an
Educational Loan Scheme. Furthermore,applicants face difficulties identifying and locating the nearest
authorized Channel Partner equipped to process their specific loan category. This fragmentation leads to
offline confusion,misrouted applications, and delays in disbursement.The challenge is to develop an intelligent,
multi-lingual digital platform or mobile application that bridges the gap between the beneficiaries and the
channelizing agencies. • Expected Solution Participants are expected to develop a comprehensive platform
that includes: 1. Smart Scheme Recommender: An AI/rule-based engine that takes basic user inputs (project
type, estimated cost, income level, education status) and automatically recommends the most suitable credit or
educational loan scheme. 2. Financial Calculator: A dynamic tool to calculate projected EMIs, accounting for
specific scheme guidelines like maximum loan limits, interest rates (e.g., 6.5% to 15% depending on the
scheme), and moratorium periods (3 to 12 months). 3. Geo-Spatial Partner Locator & Router: Integration of a
mapping service to identify the nearest eligible Channel Partner (SCA/Bank/NBFC-MFI) based on the user's
location and the partner's current fund utilization eligibility (ensuring applications aren't sent to partners with
high NPAs or overdues). • Impact Goals • Enhance financial literacy among the target demographic regarding
concessional lending. • Improve transparency and efficiency in the channel finance ecosystem, ensuring faster
disbursements and better fund utilization.


## Note 
ive installed the ui-ux-pro-max skill check it and add it in the gitignore file 
dont forget to add the requirements file and 
create only the one file .env for the api keys 

## we are going to propose the solution for the above problem statemnt

### Master Build Prompt
**AI-Driven Scheme Matching for Marginalized Entrepreneurs (NSFDC, MoSJE)**


 Act as the Senior full stack ai enginner and masterd in the rag pipeline with the best chunking and the retirval stategies 

You are building the backend + frontend for a government scheme-matching platform. This is NOT a greenfield design task — the data layer is already built and audited. Your job is application logic only. Do not propose alternative architectures, alternative databases, or alternative AI approaches for the modules described below; those decisions are final and explained so you understand *why*, not so you can revisit them.

### Non-negotiable architecture facts

1. **No RAG, no ML, no LLM judgment for scheme eligibility.** Modules 1 and 2 are deterministic rule engines against structured Postgres data. Eligibility for a real loan must be 100% reproducible and explainable — "the model decided" is not an acceptable answer for a government financial-inclusion product. RAG is used ONLY in Module 4, and only for open-ended narrative questions, never for the yes/no eligibility decision itself.
2. **Two-tier recommendation, never merged into one ranked list.** NSFDC's 5 credit schemes are the *primary, authoritative* result (rule-verified, exact). The 377-scheme welfare corpus is a *secondary, clearly-labeled* "related schemes" section (RAG-retrieved, softer confidence). A judge or user must always be able to tell which answer is exact and which is exploratory.
3. **Cost ranges overlap across NSFDC schemes — output is always a ranked list, never a single match.** Micro Finance Scheme and Aajeevika both cover ₹0–1,40,000 at different rates (6.5% vs 15%); Udyam Nidhi's range overlaps both. Never write logic that assumes exactly one scheme can match.
4. **Stack is fixed:** Supabase (Postgres + PostGIS + pgvector + Auth), FastAPI, Next.js (React + TypeScript). Do not suggest swapping any of these.
5. **Precompute, never compute-on-request** for anything that doesn't change per-user: scheme translations, embeddings. Batch jobs, stored in the DB, read at request time.

### Build order — follow exactly, do not reorder

```
1. Add `purpose` field to nsfdc_schemes.json (5 records, manual tag: 4 business_self_employment, 1 education)
2. Module 1 — filter_and_rank_credit_schemes() — pure Python/SQL, unit-testable standalone, no API yet
3. Module 2 — calculate_emi() — pure math, unit-testable standalone, no API yet
4. Wrap 2 and 3 in FastAPI endpoints
5. Module 3 capability+state-filter endpoint (steps 1-2 of its 4-step pipeline only — this logic already verified correct against a real Karnataka/Term Loan test case, do not rewrite it, just wrap it)
6. Module 3 remaining steps (health filter, proximity — proximity is blocked on geocoding, build health filter first)
7. Scaffold Next.js frontend (App Router, TypeScript, Supabase client, i18n setup) — wire it to the endpoints from steps 4-6 so the core flow (form intake → recommendation → calculator → locator) is demoable with zero AI dependency
8. Module 4 last — LLM intake + RAG Q&A, then wire into the frontend's free-text intake and Q&A screens
```

Modules 1 and 2 have zero LLM dependency and should produce a fully demoable core before any AI integration work begins.

### Module 1 — Scheme Recommender

**Inputs (exact field names):** `estimated_cost` (₹), `income_level` (₹), `project_type` (enum: `business_self_employment` | `education`), `education_status` (conditional on project_type=education; enum: `admission_secured` | `currently_enrolled`).

**Credit-scheme branch (nsfdc_schemes.json, 5 rows):**
- Filter: `income_level <= max_annual_income` AND `estimated_cost BETWEEN project_cost.min AND project_cost.max` AND `purpose == project_type`
- Sort survivors by `interest_rate_pct.beneficiary ASC`
- Return: top pick (full detail) + array of alternatives (summary only)
- **Income cap = ₹5,00,000** (per PS text, chosen for judged-demo correctness). Store the live NSFDC figure (₹3,00,000) as an annotated alternate in the same record, never silently override — this is a documented, deliberate choice, not an oversight.

**Welfare-scheme branch (schemes_production_deduped.json, 377 rows):**
- Filter: `issuing_state` match OR central, `income_criteria` amount check (mind the `{operator, amount}` structure — not all schemes use `less_than`), `caste_or_target_scope` overlap
- `education_criteria` is unstructured text — keyword match only until a structured extraction pass is done; do not present this filter to the user as exact when it isn't

### Module 2 — Financial Calculator

```
EMI = P × r × (1+r)^n / ((1+r)^n − 1)
r = interest_rate_pct.beneficiary / 12 / 100   (scheme-owned, NEVER user-editable)
P = min(user_requested_amount, max_loan_amount, project_cost × project_cost_coverage_pct)
n = min(user_requested_months, tenure_years × 12)
```
- EMI payments begin at month `moratorium_months + 1`
- **Explicit assumption, must be stated in the submission/UI, not hidden:** interest does NOT accrue during moratorium (source data doesn't specify either way — this is our documented choice)
- Null handling: `max_loan_amount: null` (Education Loan Scheme) → derive cap from `project_cost × project_cost_coverage_pct`. `moratorium_months: null` → treat as 0.

### Module 3 — Partner Locator

Exact query order, do not reorder — proximity is deliberately last because it's the only step still blocked:

1. **Capability filter:** `partner_type IN matched_scheme.channel_partners[]` — direct pass-through from Module 1 output, zero ambiguity, already verified working
2. **Eligibility filter:** SCA → hard state match (`partner.state = user.state`, no fuzzy proximity, SCAs are state-bound by charter). PSB/RRB/NBFC-MFI/Cooperative/SFB/Other → nationally eligible, no state constraint
3. **Health filter:** query mocked `partner_health(partner_id, npa_ratio, utilization_pct)` table. **Deprioritize, do not hard-exclude** above-threshold partners — hard exclusion risks a zero-result state in the demo
4. **Proximity rank:** PostGIS `<->` KNN on a `geom` column — blocked until geocoding + IFSC join land; build this last

Known permanent gap to disclose in the UI, not hide: NBFC-MFIs are absent from IFSC.csv entirely — they will always resolve to a single HQ pin, never real branch-level proximity.

### Module 4 — LLM Intake + RAG Q&A

Scale reality: ~377 schemes × 5-7 chunks ≈ 2,600 chunks total. This is small. Do not over-engineer with reranking or multi-query retrieval — those solve problems this corpus doesn't have.

- **Chunking:** scheme boundary first, section boundary second (Details/Benefits/Eligibility/Exclusions/Application Process/Documents Required), sub-split only if a section exceeds ~1200 chars, and never mid-unit (never split a table row or a numbered step)
- **Retrieval:** metadata pre-filter to the single matched `scheme_id` FIRST (2,600 → 5-7 chunks), only then rank by embedding similarity. At that scale, plain keyword match is nearly as good as vector search — don't assume vector search is always the better tool.
- **Intent routing before retrieval:** structured questions ("what's the interest rate") answer directly from Postgres, zero LLM calls. Only narrative questions ("why don't I qualify") reach retrieval+generation.
- **Contextual embedding prefix:** prepend `scheme_name + region` before embedding each chunk (embed-time only, not stored in raw text) — prevents near-identical eligibility bullets across different states/schemes from collapsing together in vector space.
- **Sibling-chunk fetch rule:** when a section was sub-split (e.g. a benefits table into 4 chunks), always fetch ALL sibling chunks for that section once one is deemed relevant — never trust top-1 similarity alone. This failed silently on a real example during testing; the fix is mandatory, not optional polish.

### Translation (Groq, `gpt-oss-120b`)

- Scheme content: batch-translate offline, once per language, store in `scheme_translations(scheme_id, lang, field, text)`. Never translate live per-request.
- Module 4 Q&A: generate the answer directly in the user's language in one call — do not generate English then translate as a second step.
- UI chrome (buttons/labels/menus): static i18n JSON files (`frontend/messages/`), not LLM-translated, ever.
- Eligibility/income/document-requirement text specifically needs a human/native-speaker review pass before production — a mistranslated income threshold is not a cosmetic bug.

### Known data flags to resolve, not ignore

- `channel_partners.json`: 8 of 92 records flagged (two recurring bug patterns — zero-width-joiner characters splitting "Nth Floor" into phantom records; two-column PDF bleed merging adjacent entries). Fix before Module 3 ships past the demo stage.
- `schemes_production_deduped.json`: 25 flagged (24 cosmetic, 1 real — `credit-enhancement-guarantee-scheme...`'s department field needs a second look).
- `IFSC.csv`'s `BANK` column is blank on many rows — fuzzy-matching partner names against it will miss records; key off the IFSC prefix instead where possible.

### Do not build these yet (explicitly deferred, listed so you don't "helpfully" add them)

Real NPA/utilization feed, full address geocoding, scheduled IFSC refresh job, live-synced income cap, TRAI DLT SMS registration, embedding-refresh-on-update pipeline, staging/prod environment split. All of these are real production requirements and are listed in the hardening checklist below — none of them block a working demo, and building them now is scope creep against the hackathon timeline.

---

## Production hardening checklist (post-hackathon, not now)

| Item | Requirement |
|---|---|
| NPA/utilization data | Real feed via formal NSFDC data-sharing agreement — mocked data cannot ship to real users |
| Geocoding | Full address geocoding, not pincode-centroid |
| IFSC refresh | Scheduled monthly job against live RBI source |
| Income cap | Scheduled live-sync from nsfdc.nic.in with change alerts |
| Flagged records | All 8 partner + 25 scheme flags resolved, zero tolerance |
| Multi-lingual | Biggest gap — PS explicitly requires it, build early even in the hackathon version |
| Sensitive data | Caste/income are DPDP-Act-covered — encryption at rest, RLS, explicit consent, retention policy |
| SMS OTP | TRAI DLT sender-ID registration mandatory for real delivery |
| Embedding refresh | Versioned pipeline triggered on content updates, not manual re-runs |
| Environment | Staging/production separation, automated backups, monitoring |

---

## How the app actually functions end-to-end (real-world user journey)

```
1. LANDING (guest, no login wall)
   User picks language → sees "Describe your need" (free text, Module 4 intake)
   or "Fill a form" (structured, Module 1 direct)

2. INTAKE
   Free text path: LLM extracts {estimated_cost, income_level, project_type, education_status}
                    → shown back to user for confirmation before proceeding (never auto-trusted)
   Form path: same 4 fields, direct structured input

3. RECOMMENDATION (Module 1, <100ms, zero LLM calls)
   Primary block: NSFDC ranked list — top pick + alternatives, each showing
                  scheme name, why it matched, interest rate, max loan, moratorium
   Secondary block: "Related schemes you may qualify for" — welfare corpus,
                     clearly labeled as broader/less-precise matches

4. CALCULATOR (Module 2, on primary pick)
   User adjusts loan amount / tenure within scheme-enforced caps
   Sees EMI, total interest, repayment schedule, moratorium period explained

5. PARTNER LOCATOR (Module 3)
   User shares/enters location → capability filter (which partner types handle
   this scheme) → state filter (SCA) → health-deprioritized ranking →
   nearest eligible partners shown on a map with contact info

6. HANDOFF
   "Apply via PM-SURAJ Portal" — this app does NOT process the application itself,
   it hands off to the real government application system. This is intentional
   scope, not a missing feature — duplicating a government backend is out of scope.

7. Q&A (Module 4, optional, any point after step 3)
   User asks follow-up questions about their matched scheme in natural language,
   answered from that scheme's chunks only (session-scoped stickiness)

8. LOGIN (optional, only gate in the whole flow)
   Only required if the user wants to save their match / track application status
   over time. Everything above works fully as a guest.
```

The core principle: **steps 1-5 must work with zero AI-model dependency failure risk** — if the LLM intake or the RAG Q&A layer goes down, the form-path recommendation, calculator, and locator still work end-to-end. AI enhances the experience; it never gates the critical path.

---

## Folder structure

```
saarthi-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI app entrypoint
│   │   ├── config.py                    # env vars, Supabase connection
│   │   ├── db/
│   │   │   ├── session.py               # Supabase/Postgres client setup
│   │   │   └── migrations/              # SQL migration files (schemes, partners, health, translations tables)
│   │   ├── modules/
│   │   │   ├── module1_recommender/
│   │   │   │   ├── credit_engine.py     # filter_and_rank_credit_schemes()
│   │   │   │   ├── welfare_engine.py    # welfare corpus filter (state/income/caste)
│   │   │   │   └── tests/
│   │   │   │       └── test_recommender.py
│   │   │   ├── module2_calculator/
│   │   │   │   ├── emi.py               # calculate_emi()
│   │   │   │   └── tests/
│   │   │   │       └── test_emi.py
│   │   │   ├── module3_locator/
│   │   │   │   ├── capability_filter.py
│   │   │   │   ├── eligibility_filter.py  # SCA state-match, others national
│   │   │   │   ├── health_filter.py       # mocked partner_health table query
│   │   │   │   ├── proximity.py           # PostGIS KNN (blocked on geocoding)
│   │   │   │   └── tests/
│   │   │   └── module4_rag/
│   │   │       ├── intake_extraction.py   # free-text → structured fields
│   │   │       ├── chunking.py            # hierarchical chunker (scheme→section→sub-split)
│   │   │       ├── embedding_pipeline.py  # batch embed job, versioned
│   │   │       ├── retrieval.py           # metadata pre-filter + similarity rank
│   │   │       ├── intent_router.py       # structured-vs-narrative question routing
│   │   │       └── generation.py          # answer generation, target-language-direct
│   │   ├── api/
│   │   │   ├── routes_recommender.py
│   │   │   ├── routes_calculator.py
│   │   │   ├── routes_locator.py
│   │   │   ├── routes_rag.py
│   │   │   └── routes_auth.py
│   │   └── translation/
│   │       ├── batch_translate.py       # Groq gpt-oss-120b offline batch job
│   │       └── i18n/                    # static UI-chrome JSON strings per language (source of truth, synced into frontend/messages/)
│   └── requirements.txt
│
├── data/
│   ├── raw/                             # original docx/pdf sources, untouched
│   ├── staging/
│   │   ├── nsfdc_schemes.json           # 5 records, credit rule-engine source
│   │   ├── schemes_production_deduped.json  # 377 records, welfare + Module 4 corpus
│   │   └── channel_partners.json        # 92 records, Module 3 source
│   ├── reference/
│   │   └── ifsc.csv                     # 182,758 rows, branch-level geo enrichment
│   └── pipelines/
│       ├── docx_extraction_pipeline.py  # scheme docx → JSON (already built)
│       ├── pdf_extraction_pipeline.py   # partner PDFs → JSON (already built)
│       └── validation/
│           ├── validation_report.json
│           ├── review_required.json
│           └── canonical_scheme_index.json
│
├── frontend/                            # Next.js (App Router) + TypeScript
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                     # landing screen (language pick + form/free-text toggle)
│   │   ├── intake/
│   │   │   └── page.tsx                 # form + free-text intake (Module 4 extraction confirm step)
│   │   ├── recommendation/
│   │   │   └── page.tsx                 # primary (NSFDC) + secondary (welfare) blocks
│   │   ├── calculator/
│   │   │   └── page.tsx                 # EMI, tenure/amount sliders within scheme caps
│   │   ├── locator/
│   │   │   └── page.tsx                 # map view (react-leaflet / mapbox-gl)
│   │   ├── qa/
│   │   │   └── page.tsx                 # Module 4 chat, session-scoped to matched scheme
│   │   ├── login/
│   │   │   └── page.tsx                 # optional gate — save match / track status
│   │   └── api/                         # (only if using Next.js route handlers as a thin proxy;
│   │                                     #  otherwise frontend calls FastAPI directly)
│   ├── components/
│   │   ├── SchemeCard.tsx
│   │   ├── EmiCalculator.tsx
│   │   ├── PartnerMap.tsx
│   │   ├── LanguageSwitcher.tsx
│   │   └── ChatBubble.tsx
│   ├── lib/
│   │   ├── supabaseClient.ts
│   │   ├── apiClient.ts                 # typed fetch wrappers per module (mirrors backend/app/api routes)
│   │   └── types.ts                     # shared types (mirror Pydantic schemas where practical)
│   ├── messages/                        # next-intl / next-i18next locale JSON (per language)
│   ├── public/
│   ├── middleware.ts                    # auth/session middleware if needed
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── docs/
│   ├── BUILT_PROMPT.md                  # this file
│   ├── ARCHITECTURE_DECISIONS.md        # the "why", not just the "what"
│   └── PRODUCTION_HARDENING.md          # the checklist table, expanded
│
├── AGENTS.md                            # standing rules for Antigravity agents
└── README.md
```

**Note on `data/pipelines/`:** these scripts already ran and produced the staging JSON — they are one-time/scheduled tools, not something the running application calls per-request. Keep them in the repo for reproducibility and future re-runs when source documents update, but they are not part of the request-serving path.