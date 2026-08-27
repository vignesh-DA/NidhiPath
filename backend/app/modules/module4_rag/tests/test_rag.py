"""
Unit tests for Module 4: LLM Intake + RAG Q&A
"""

import pytest
from app.modules.module4_rag.models import SchemeChunk
from app.modules.module4_rag.chunking import (
    subsplit_section,
    split_into_units,
    pack_units,
    chunk_scheme,
    chunk_schemes,
)
from app.modules.module4_rag.embedding_pipeline import (
    embed_text,
    cosine_similarity,
    contextual_prefix,
    embed_chunk,
    build_index,
)
from app.modules.module4_rag.intent_router import route_intent
from app.modules.module4_rag.retrieval import (
    retrieve,
    fetch_siblings,
    prefilter,
)
from app.modules.module4_rag.generation import extractive_answer
from app.modules.module4_rag.intake_extraction import (
    heuristic_extract,
    _parse_indian_amount,
    _detect_state,
)
from app.modules.module4_rag.qa_service import (
    answer_question,
    find_scheme,
    answer_structured,
)


# ─── 1. Chunking Tests ────────────────────────────────────────────────────────

class TestChunking:
    def test_split_into_units_numbered_steps(self):
        text = "1. First step\n2. Second step\n3. Third step"
        units = split_into_units(text)
        assert len(units) == 3
        assert "First step" in units[0]

    def test_subsplit_section_under_limit(self):
        text = "Short section content"
        parts = subsplit_section(text, limit=1200)
        assert len(parts) == 1
        assert parts[0] == text

    def test_subsplit_section_over_limit(self):
        # Create a text with 10 steps that exceeds 500 chars
        steps = [f"{i}. " + ("Step content details " * 8) for i in range(1, 11)]
        long_text = "\n".join(steps)
        parts = subsplit_section(long_text, limit=400)
        assert len(parts) > 1
        # Atomic integrity: No part should break a sentence or step mid-way
        for part in parts:
            assert len(part) <= 800  # reasonably packed

    def test_chunk_nsfdc_scheme(self):
        sample_scheme = {
            "scheme_id": "TEST_SCHEME_1",
            "scheme_name": "Test Micro Finance",
            "purpose": "business_self_employment",
            "project_cost": {"min": 0, "max": 140000},
            "interest_rate_pct": {"beneficiary": 6.5, "sca": 3.5},
            "max_loan_amount": 140000,
            "project_cost_coverage_pct": 90,
            "tenure_years": 3,
            "moratorium_months": 3,
            "required_documents": ["Aadhaar", "Caste Certificate"],
            "channel_partners": ["SCA", "PSB"],
            "max_annual_income": 500000,
        }
        chunks = chunk_scheme(sample_scheme, source="nsfdc")
        assert len(chunks) >= 4
        sections = {c.section for c in chunks}
        assert "details" in sections
        assert "benefits" in sections
        assert "eligibility" in sections
        assert "documents_required" in sections
        for c in chunks:
            assert c.scheme_id == "TEST_SCHEME_1"
            assert c.source == "nsfdc"


# ─── 2. Embedding & Retrieval Tests ──────────────────────────────────────────

class TestEmbeddingAndRetrieval:
    def test_embed_text_dimensions_and_normalization(self):
        vec = embed_text("Concessional loan for SC entrepreneur in Karnataka")
        assert len(vec) == 384
        # L2 norm should be approx 1.0
        norm = sum(x * x for x in vec) ** 0.5
        assert pytest.approx(norm, rel=1e-3) == 1.0

    def test_cosine_similarity_identical_and_orthogonal(self):
        vec1 = embed_text("Micro finance loan")
        vec2 = embed_text("Micro finance loan")
        assert pytest.approx(cosine_similarity(vec1, vec2), rel=1e-3) == 1.0

        vec3 = embed_text("Completely unrelated astrophysical telescope topic")
        assert cosine_similarity(vec1, vec3) < 0.6

    def test_sibling_fetch(self):
        chunk1 = SchemeChunk(
            chunk_id="S1::eligibility::0",
            scheme_id="S1",
            scheme_name="Scheme 1",
            section="eligibility",
            section_index=0,
            sibling_count=2,
            was_subsplit=True,
            text="Eligibility part 1",
        )
        chunk2 = SchemeChunk(
            chunk_id="S1::eligibility::1",
            scheme_id="S1",
            scheme_name="Scheme 1",
            section="eligibility",
            section_index=1,
            sibling_count=2,
            was_subsplit=True,
            text="Eligibility part 2",
        )
        corpus = [chunk1, chunk2]
        expanded = fetch_siblings([chunk1], corpus)
        assert len(expanded) == 2
        assert expanded[0].chunk_id == "S1::eligibility::0"
        assert expanded[1].chunk_id == "S1::eligibility::1"


# ─── 3. Intent Router Tests ──────────────────────────────────────────────────

class TestIntentRouter:
    def test_routes_interest_rate(self):
        res = route_intent("What is the interest rate for this scheme?")
        assert res.kind == "structured"
        assert res.field == "interest_rate"

    def test_routes_income_cap(self):
        res = route_intent("What is the maximum family income limit?")
        assert res.kind == "structured"
        assert res.field == "income_cap"

    def test_routes_moratorium(self):
        res = route_intent("How much moratorium period is allowed?")
        assert res.kind == "structured"
        assert res.field == "moratorium"

    def test_routes_documents(self):
        res = route_intent("What documents do I need to submit?")
        assert res.kind == "structured"
        assert res.field == "documents"

    def test_routes_narrative_question(self):
        res = route_intent("Why don't I qualify for the term loan scheme?")
        assert res.kind == "narrative"

    def test_narrative_marker_overrides_field_keyword(self):
        # "why" makes it narrative even with "interest rate"
        res = route_intent("Why is the interest rate 6.5% instead of 5%?")
        assert res.kind == "narrative"


# ─── 4. Intake Extraction Tests ──────────────────────────────────────────────

class TestIntakeExtraction:
    def test_parse_indian_amount_lakhs(self):
        assert _parse_indian_amount("1.4 lakh") == 140000.0
        assert _parse_indian_amount("₹2.5 Lakhs") == 250000.0
        assert _parse_indian_amount("50,000") == 50000.0
        assert _parse_indian_amount("2 crore") == 20000000.0

    def test_detect_state(self):
        assert _detect_state("I live in Bengaluru and need a loan") == "Karnataka"
        assert _detect_state("Looking for schemes in Tamil Nadu") == "Tamil Nadu"
        assert _detect_state("Resident of Mumbai") == "Maharashtra"

    def test_heuristic_extract_business(self):
        text = "I am an SC entrepreneur in Karnataka. I need a loan of 1.4 lakh for my kirana shop. My annual family income is 2 lakh."
        res = heuristic_extract(text)
        assert res.project_type == "business_self_employment"
        assert res.estimated_cost == 140000.0
        assert res.income_level == 200000.0
        assert res.user_state == "Karnataka"
        assert res.caste_scope == ["SC"]
        assert res.needs_confirmation is True

    def test_heuristic_extract_education(self):
        text = "I got admission secured for engineering college in Delhi. Need 5 lakh for tuition. Income is 1.5 lakh."
        res = heuristic_extract(text)
        assert res.project_type == "education"
        assert res.education_status == "admission_secured"
        assert res.estimated_cost == 500000.0
        assert res.income_level == 150000.0
        assert res.user_state == "Delhi"
        assert res.needs_confirmation is True


# ─── 5. Q&A Service Tests ───────────────────────────────────────────────────

class TestQAService:
    @pytest.fixture
    def mock_nsfdc_schemes(self):
        return [
            {
                "scheme_id": "NSFDC_MF",
                "scheme_name": "Micro Finance Scheme",
                "purpose": "business_self_employment",
                "project_cost": {"min": 0, "max": 140000},
                "interest_rate_pct": {"beneficiary": 6.5, "sca": 3.5},
                "max_loan_amount": 140000,
                "project_cost_coverage_pct": 90,
                "tenure_years": 3,
                "moratorium_months": 3,
                "max_annual_income": 500000,
                "_max_annual_income_nsfdc_live": 300000,
                "required_documents": ["aadhaar_card", "caste_certificate"],
                "channel_partners": ["SCA", "PSB"],
            }
        ]

    def test_answer_structured_interest_rate(self, mock_nsfdc_schemes):
        res = answer_question(
            "What is the interest rate?",
            scheme_id="NSFDC_MF",
            nsfdc_schemes=mock_nsfdc_schemes,
        )
        assert res.intent == "structured"
        assert res.used_llm is False
        assert "6.5%" in res.answer
        assert "Micro Finance Scheme" in res.answer

    def test_answer_structured_income_cap(self, mock_nsfdc_schemes):
        res = answer_question(
            "What is the family income limit?",
            scheme_id="NSFDC_MF",
            nsfdc_schemes=mock_nsfdc_schemes,
        )
        assert res.intent == "structured"
        assert res.used_llm is False
        assert "500,000" in res.answer
        assert "300,000" in res.answer  # Shows live alternate without silent override

    def test_answer_structured_moratorium(self, mock_nsfdc_schemes):
        res = answer_question(
            "What is the moratorium period?",
            scheme_id="NSFDC_MF",
            nsfdc_schemes=mock_nsfdc_schemes,
        )
        assert res.intent == "structured"
        assert "3 month" in res.answer
        assert "Interest does NOT accrue" in res.answer

    def test_answer_narrative_extractive_fallback(self, mock_nsfdc_schemes):
        chunks = chunk_schemes(nsfdc_schemes=mock_nsfdc_schemes)
        res = answer_question(
            "Explain how the application process works for this scheme",
            scheme_id="NSFDC_MF",
            nsfdc_schemes=mock_nsfdc_schemes,
            chunks=chunks,
        )
        assert res.intent == "narrative"
        assert len(res.sources) > 0
        assert "Micro Finance Scheme" in res.answer
