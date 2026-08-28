# Architecture Decisions — NidhiPath

This document records the key architecture decisions for the NidhiPath platform and explains the _why_, not just the _what_.

---

## AD-1: No RAG/ML/LLM for Scheme Eligibility

**Decision:** Modules 1 and 2 are deterministic rule engines against structured Postgres/JSON data.

**Why:** Eligibility for a real government loan must be 100% reproducible and explainable. "The model decided" is not an acceptable answer for a government financial-inclusion product. A judge, auditor, or beneficiary must be able to trace exactly why a scheme was or wasn't recommended.

**Implication:** RAG is used ONLY in Module 4 for open-ended narrative questions, never for the yes/no eligibility decision itself.

---

## AD-2: Two-Tier Recommendation, Never Merged

**Decision:** NSFDC's 5 credit schemes are the _primary, authoritative_ result (rule-verified, exact). The 377-scheme welfare corpus is a _secondary, clearly-labeled_ "related schemes" section (approximate).

**Why:** A user (and a judge reviewing the system) must always be able to tell which answer is exact and which is exploratory. Merging them into one ranked list would create false equivalence.

---

## AD-3: Multiple Matches, Never Single

**Decision:** Output is always a ranked list, never a single match.

**Why:** Cost ranges overlap across NSFDC schemes. Micro Finance Scheme and Aajeevika both cover ₹0–1,40,000 at different rates (6.5% vs 15%); Udyam Nidhi's range overlaps both. Logic that assumes exactly one match would silently suppress valid options.

---

## AD-4: Income Cap = ₹5,00,000 (Not ₹3,00,000)

**Decision:** Use ₹5,00,000 as the annual income cap per the Problem Statement text. Store the live NSFDC figure (₹3,00,000) as an annotated alternate in the same record.

**Why:** The Problem Statement explicitly states "annual family income of up to ₹5.00 Lakhs." For judged-demo correctness, we follow the PS. The live NSFDC website shows ₹3,00,000. Neither is silently overridden — both are stored, and the UI discloses this explicitly.

---

## AD-5: Moratorium Interest Assumption

**Decision:** Interest does NOT accrue during the moratorium period.

**Why:** Source data doesn't specify either way. This is our documented, deliberate choice. It must be stated in the UI and submission materials, not hidden. The alternative (interest accruing during moratorium) would require amortization schedule restructuring.

---

## AD-6: Health Filter Deprioritizes, Never Hard-Excludes

**Decision:** Partners with high NPA ratios or over-utilized funds are pushed down the list, not removed.

**Why:** Hard exclusion risks a zero-result state in the demo. In production with real data, the threshold may be configurable, but the principle stands: always show _something_.

---

## AD-7: SCA State-Binding is Hard, Not Fuzzy

**Decision:** State Channelizing Agencies (SCAs) require a hard state match (partner.state = user.state). No fuzzy proximity.

**Why:** SCAs are state-bound by charter. A Karnataka SCA cannot process a Tamil Nadu applicant, regardless of physical proximity. PSBs, RRBs, NBFC-MFIs, etc. are nationally eligible.

---

## AD-8: Precompute, Never Compute-on-Request

**Decision:** Scheme translations, embeddings, and any data that doesn't change per-user are batch-processed and stored in the DB, read at request time.

**Why:** Compute-on-request for static content wastes latency and LLM tokens. Translation of scheme content happens once per language, offline.

---

## AD-9: Stack is Fixed

| Component | Choice | Reason |
|-----------|--------|--------|
| Backend | FastAPI (Python) | Async, Pydantic validation, auto OpenAPI docs |
| Frontend | Next.js (React + TypeScript) | App Router, SSR, i18n support |
| Database | Supabase (Postgres + PostGIS + pgvector + Auth) | Managed, extensions included, RLS for security |
| LLM/Translation | Groq (`gpt-oss-120b`) | Fast inference for translation and RAG generation |

---

## AD-10: AI Enhances, Never Gates

**Decision:** Steps 1-5 of the user journey (Landing → Intake → Recommendation → Calculator → Locator) work with ZERO AI-model dependency.

**Why:** If the LLM intake or the RAG Q&A layer goes down, the form-path recommendation, calculator, and locator still work end-to-end. The critical financial-inclusion path must never be gated by an external AI service's availability.

---

## AD-11: Quarterly Installment Cadence for the Micro Finance Scheme

**Decision:** NSFDC's Micro Finance Scheme officially "repaid in quarterly
instalments within 4 years" (verified from the live NSFDC scheme page). The
calculator treats cadence as a scheme-owned parameter, exactly like the
interest rate: `resolve_payment_frequency()` in
`backend/app/modules/module2_calculator/emi.py` maps `nsfdc-mfs-001` (or any
record whose name contains "micro finance") to quarterly — 4 installments per
year, periodic rate = annual/4, months rounded up to whole quarters — and every
other scheme to monthly. For unknown/welfare schemes the client may pass
`payment_frequency` explicitly; for known NSFDC schemes the server's resolution
always wins.

**Why:** Applying standard monthly-annuity math to a scheme that officially
repays quarterly is a materially wrong repayment structure, not a cosmetic
difference: ₹1,00,000 @ 6.5% p.a. over 3 years is ₹9,239.54/quarter (12
installments, ₹10,874.48 total interest) vs 3 × ₹3,064.90 monthly (₹10,336.41
total interest). Any result still shown on monthly cadence carries an explicit
`assumption_note` disclosing the limitation — silence is the failure mode being
avoided.

**Tests:** `test_emi.py::TestQuarterlyCadence` — golden value ₹9,239.54 pinned,
quarterly-vs-monthly materiality, schedule structure, moratorium interaction,
and the mandated disclosure line on monthly-cadence results.
