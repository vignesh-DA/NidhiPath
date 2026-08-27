"""
API Integration Tests for all NidhiPath endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoints():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["modules"]["recommender"] == "active"
    assert data["modules"]["calculator"] == "active"
    assert data["modules"]["locator"] == "active"
    assert data["modules"]["rag"] == "active"

    res_health = client.get("/health")
    assert res_health.status_code == 200


def test_recommend_endpoint():
    payload = {
        "estimated_cost": 100000,
        "income_level": 200000,
        "project_type": "business_self_employment",
        "user_state": "Karnataka",
    }
    res = client.post("/api/v1/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "primary" in data
    assert "secondary" in data
    assert data["primary"]["top_pick"] is not None
    assert data["primary"]["top_pick"]["scheme_name"] != ""


def test_calculate_emi_server_side_resolution():
    # Test that client cannot tamper with interest rate
    payload = {
        "scheme_id": "NSFDC_MF",
        "requested_amount": 100000,
        "requested_months": 36,
        "project_cost": 100000,
        "interest_rate_pct": 1.0,  # Client tries to send 1.0%
        "include_schedule": True,
    }
    res = client.post("/api/v1/calculate-emi", json=payload)
    assert res.status_code == 200
    data = res.json()
    # Server must override with authoritative NSFDC 6.5% rate
    assert data["scheme_resolved"] is True
    assert data["effective_interest_rate_annual"] == 6.5
    assert data["emi_amount"] > 0
    assert len(data["schedule"]) > 0


def test_locate_partners_endpoint():
    payload = {
        "scheme_channel_partners": ["SCA", "PSB", "RRB"],
        "user_state": "Karnataka",
    }
    res = client.post("/api/v1/locate-partners", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "partners" in data
    assert "pipeline_summary" in data


def test_intake_extract_endpoint():
    payload = {
        "text": "I am from Karnataka and need a 2 lakh loan for my shop. Family income is 1.8 lakh."
    }
    res = client.post("/api/v1/intake/extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["needs_confirmation"] is True
    assert data["project_type"] == "business_self_employment"
    assert data["estimated_cost"] == 200000.0


def test_qa_endpoint():
    payload = {
        "question": "What is the interest rate for the Micro Finance Scheme?",
        "scheme_id": "NSFDC_MF",
        "language": "en",
    }
    res = client.post("/api/v1/qa", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "structured"
    assert "6.5%" in data["answer"]
