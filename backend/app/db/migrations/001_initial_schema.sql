
-- ============================================================
-- NidhiPath — Initial Schema (Supabase / Postgres)
-- Run in Supabase SQL editor or via psql, in order.
--
-- Tables:
--   nsfdc_schemes        — 5 authoritative credit-scheme records (Module 1/2)
--   welfare_schemes      — 377-record welfare corpus (Module 1 secondary)
--   channel_partners     — 92 partner records (Module 3)
--   partner_health       — mocked NPA/utilization feed (Module 3 step 3)
--   scheme_chunks        — precomputed RAG chunks + pgvector embeddings (Module 4)
--   scheme_translations  — offline batch translations (never live-translated)
--
-- Extensions: postgis (partner geo), pgvector (embeddings)
-- ============================================================

create extension if not exists postgis;
create extension if not exists vector;

-- ─── NSFDC credit schemes ────────────────────────────────────────────────────
create table if not exists nsfdc_schemes (
    scheme_id            text primary key,
    scheme_name          text not null,
    purpose              text not null check (purpose in ('business_self_employment', 'education')),
    project_cost_min     numeric not null default 0,
    project_cost_max     numeric not null,
    max_loan_amount      numeric,              -- null → derive from cost × coverage
    interest_rate_beneficiary numeric not null,
    interest_rate_sca    numeric,
    moratorium_months    integer,              -- null → treat as 0
    tenure_years         numeric,
    project_cost_coverage_pct numeric not null default 90,
    max_annual_income    numeric not null default 500000,
    max_annual_income_nsfdc_live numeric not null default 300000,
    income_cap_note      text,
    allowed_social_categories text[] not null default '{sc}',
    required_documents   text[] not null default '{}',
    channel_partners     text[] not null default '{}',
    official_source_url  text,
    last_verified_date   date,
    raw                  jsonb not null default '{}'::jsonb
);

-- ─── Welfare corpus ──────────────────────────────────────────────────────────
create table if not exists welfare_schemes (
    scheme_id            text primary key,     -- canonical_scheme_id
    scheme_name          text not null,
    issuing_state        text,
    issuing_body         text,
    department           text,
    ministry             text,
    scheme_category      text,
    tags                 text[] not null default '{}',
    caste_or_target_scope text[] not null default '{}',
    gender_scope         text[] not null default '{}',
    income_criteria      jsonb not null default '[]'::jsonb,   -- {operator, amount} — not all less_than
    education_criteria   text[] not null default '{}',         -- unstructured text — keyword match only
    benefits             jsonb not null default '[]'::jsonb,
    raw                  jsonb not null default '{}'::jsonb
);

create index if not exists idx_welfare_state on welfare_schemes (issuing_state);

-- ─── Channel partners ────────────────────────────────────────────────────────
create table if not exists channel_partners (
    partner_id     text primary key,
    partner_name   text not null,
    partner_type   text not null,   -- SCA | PSB | RRB | NBFC-MFI | Cooperative Bank | Cooperative Society | SFB | Other Agency
    state          text not null default '',
    address_raw    text not null default '',
    pincode        text not null default '',
    geom           geography(Point, 4326)  -- populated when geocoding lands (Module 3 step 4)
);

create index if not exists idx_partners_type on channel_partners (partner_type);
create index if not exists idx_partners_state on channel_partners (state);
create index if not exists idx_partners_geom on channel_partners using gist (geom);

-- ─── Partner health (MOCKED — cannot ship to real users, see hardening doc) ──
create table if not exists partner_health (
    partner_id     text primary key references channel_partners (partner_id),
    npa_ratio      numeric not null default 0,
    utilization_pct numeric not null default 0,
    updated_at     timestamptz not null default now()
);

-- ─── RAG chunks (pgvector) ───────────────────────────────────────────────────
create table if not exists scheme_chunks (
    chunk_id          text primary key,
    scheme_id         text not null,
    scheme_name       text not null,
    region            text not null default '',
    section           text not null,
    section_index     integer not null default 0,
    sibling_count     integer not null default 1,
    was_subsplit      boolean not null default false,
    text              text not null,
    source            text not null default 'welfare',  -- 'nsfdc' | 'welfare'
    embedding         vector(384) not null,
    embedding_version text not null default 'hash-v1'
);

create index if not exists idx_chunks_scheme on scheme_chunks (scheme_id);
create index if not exists idx_chunks_embedding on scheme_chunks
    using ivfflat (embedding vector_cosine_ops) with (lists = 50);

-- ─── Offline batch translations (Groq gpt-oss-120b, once per language) ───────
create table if not exists scheme_translations (
    scheme_id   text not null,
    lang        text not null,
    field       text not null,
    text        text not null,
    reviewed    boolean not null default false,  -- income/eligibility text needs native-speaker review
    created_at  timestamptz not null default now(),
    primary key (scheme_id, lang, field)
);

-- ─── Row Level Security: public read, service-role write ─────────────────────
alter table nsfdc_schemes      enable row level security;
alter table welfare_schemes    enable row level security;
alter table channel_partners   enable row level security;
alter table partner_health     enable row level security;
alter table scheme_chunks      enable row level security;
alter table scheme_translations enable row level security;

create policy "public read nsfdc"      on nsfdc_schemes      for select using (true);
create policy "public read welfare"    on welfare_schemes    for select using (true);
create policy "public read partners"   on channel_partners   for select using (true);
create policy "public read health"     on partner_health     for select using (true);
create policy "public read chunks"     on scheme_chunks      for select using (true);
create policy "public read translations" on scheme_translations for select using (true);