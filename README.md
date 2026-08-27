# NidhiPath

**AI-Driven Scheme Matching for Marginalized Entrepreneurs**

Built for the Ministry of Social Justice and Empowerment (MoSJE) | Department of Social Justice and Empowerment

---

## What This Does

NidhiPath helps Scheduled Caste (SC) beneficiaries find the right NSFDC concessional credit scheme, calculate EMIs, and locate authorized channel partners — all through a multi-lingual digital platform.

### Core Modules

| Module | Function | AI Dependency |
|--------|----------|---------------|
| **Module 1** — Scheme Recommender | Matches user profile to NSFDC credit schemes + welfare schemes | ❌ None (deterministic rules) |
| **Module 2** — Financial Calculator | EMI calculation with scheme-enforced caps, moratorium handling | ❌ None (pure math) |
| **Module 3** — Partner Locator | Finds nearest authorized channel partner (SCA/PSB/RRB/NBFC-MFI) | ❌ None (filter pipeline) |
| **Module 4** — AI Q&A | Free-text intake extraction + scheme-scoped Q&A | ✅ Groq LLM + RAG |

**Key principle:** Modules 1-3 work with **zero AI dependency**. If the LLM goes down, the core flow still works end-to-end.

---

## Quick Start

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

### Data Files

Place your data files in the following locations before starting the backend:

```
data/staging/nsfdc_schemes.json          # 5 NSFDC credit scheme records
data/staging/schemes_production_deduped.json  # 377 welfare scheme records
data/staging/channel_partners.json       # 92 channel partner records
data/reference/ifsc.csv                  # 182K+ IFSC branch records
```

### Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

---

## Project Structure

```
NidhiPath/
├── backend/               # FastAPI (Python)
│   ├── app/
│   │   ├── main.py        # App entrypoint
│   │   ├── config.py      # Environment config
│   │   ├── api/           # API route handlers
│   │   ├── modules/       # Business logic (4 modules)
│   │   ├── db/            # Database session
│   │   └── translation/   # Batch translation
│   └── requirements.txt
├── frontend/              # Next.js (TypeScript)
│   ├── app/               # App Router pages
│   ├── lib/               # API client, types
│   └── messages/          # i18n (en, hi)
├── data/                  # Data files
│   ├── staging/           # Production JSON
│   ├── reference/         # IFSC CSV
│   └── pipelines/         # Extraction scripts
├── docs/                  # Architecture docs
└── .env                   # Environment variables
```

---

## Tests

```bash
cd backend
python -m pytest -v
```

39 tests across Modules 1, 2, and 3.

---

## License

TBD

---

## Acknowledgments

- **NSFDC** (National Scheduled Castes Finance and Development Corporation)
- **MoSJE** (Ministry of Social Justice and Empowerment)
- **PM-SURAJ Portal** for the actual loan application processing
