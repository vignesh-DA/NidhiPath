# Data Staging Directory

Place the following files here:

1. **nsfdc_schemes.json** — 5 NSFDC credit scheme records (source of truth for Module 1 credit engine)
2. **schemes_production_deduped.json** — 377 welfare scheme records (Module 1 welfare engine + Module 4 RAG corpus)
3. **channel_partners.json** — 92 channel partner records (Module 3 partner locator)

These files were produced by the data extraction pipelines and are the audited, canonical source.
Do NOT edit them manually — if corrections are needed, update the pipeline and re-extract.
