"""
Tests for Phase 15 Evaluation & Performance Dashboard API.

Verifies:
1. Security: Unauthenticated request returns 401.
2. RBAC: PATIENT and PHYSICIAN roles receive 403.
3. RBAC: SYSTEM_ADMIN, HOSPITAL_ADMIN, RESEARCH_COORDINATOR receive 200.
4. Schema validation and response correctness across all 4 endpoints.
5. Exact Phase 14.1 frozen baseline values (128.32 ms, 181.60 ms, 5 queries).
6. Exact Phase 14.2 controlled same-run experiment values (121.55 -> 25.34 ms, 79.15%, 5 -> 1 query, 80.0%).
7. Explicit unmeasured status for Gemini API and HTTP socket latencies.
8. Safety parity (14/14 injections intercepted, 100% detection rate).
9. Ablation parity (n=6 sample size, 5 experiments, 5 ablations).
"""

from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    """Ensure clean dependency overrides before and after every test."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_admin():
    return {
        "sub": str(uuid4()),
        "email": "sysadmin@medmatch.org",
        "role": "SYSTEM_ADMIN",
        "hospital_id": str(uuid4()),
    }


@pytest.fixture
def mock_hospital_admin():
    return {
        "sub": str(uuid4()),
        "email": "admin@hospital.org",
        "role": "HOSPITAL_ADMIN",
        "hospital_id": str(uuid4()),
    }


@pytest.fixture
def mock_research_coordinator():
    return {
        "sub": str(uuid4()),
        "email": "coordinator@hospital.org",
        "role": "RESEARCH_COORDINATOR",
        "hospital_id": str(uuid4()),
    }


@pytest.fixture
def mock_physician():
    return {
        "sub": str(uuid4()),
        "email": "doctor@hospital.org",
        "role": "PHYSICIAN",
        "hospital_id": str(uuid4()),
    }


@pytest.fixture
def mock_patient():
    return {
        "sub": str(uuid4()),
        "email": "patient@example.com",
        "role": "PATIENT",
        "hospital_id": str(uuid4()),
    }


EVALUATION_ENDPOINTS = [
    "/api/evaluation/overview",
    "/api/evaluation/performance",
    "/api/evaluation/safety",
    "/api/evaluation/ablations",
]


# =============================================================================
# Security & RBAC Tests
# =============================================================================

@pytest.mark.parametrize("endpoint", EVALUATION_ENDPOINTS)
def test_unauthenticated_requests_return_401(endpoint):
    """Unauthenticated requests must be rejected with 401."""
    with TestClient(app) as client:
        response = client.get(endpoint)
        assert response.status_code == 401


@pytest.mark.parametrize("endpoint", EVALUATION_ENDPOINTS)
def test_patient_role_rejected_with_403(endpoint, mock_patient):
    """PATIENT role must be rejected with 403 Forbidden."""
    app.dependency_overrides[get_current_user] = lambda: mock_patient
    with TestClient(app) as client:
        response = client.get(endpoint)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json().get("detail", "")


@pytest.mark.parametrize("endpoint", EVALUATION_ENDPOINTS)
def test_physician_role_rejected_with_403(endpoint, mock_physician):
    """PHYSICIAN role must be rejected with 403 Forbidden for Phase 15 dashboard."""
    app.dependency_overrides[get_current_user] = lambda: mock_physician
    with TestClient(app) as client:
        response = client.get(endpoint)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json().get("detail", "")


@pytest.mark.parametrize("endpoint", EVALUATION_ENDPOINTS)
def test_system_admin_role_returns_200(endpoint, mock_admin):
    """SYSTEM_ADMIN role is authorized."""
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    with TestClient(app) as client:
        response = client.get(endpoint)
        assert response.status_code == 200


@pytest.mark.parametrize("endpoint", EVALUATION_ENDPOINTS)
def test_hospital_admin_role_returns_200(endpoint, mock_hospital_admin):
    """HOSPITAL_ADMIN role is authorized."""
    app.dependency_overrides[get_current_user] = lambda: mock_hospital_admin
    with TestClient(app) as client:
        response = client.get(endpoint)
        assert response.status_code == 200


@pytest.mark.parametrize("endpoint", EVALUATION_ENDPOINTS)
def test_research_coordinator_role_returns_200(endpoint, mock_research_coordinator):
    """RESEARCH_COORDINATOR role is authorized."""
    app.dependency_overrides[get_current_user] = lambda: mock_research_coordinator
    with TestClient(app) as client:
        response = client.get(endpoint)
        assert response.status_code == 200


# =============================================================================
# Phase 14 Performance Data Parity Tests
# =============================================================================

def test_performance_endpoint_data_parity(mock_admin):
    """Verify performance metrics adhere strictly to Phase 14.1 & 14.2 artifacts."""
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    with TestClient(app) as client:
        response = client.get("/api/evaluation/performance")
        assert response.status_code == 200
        body = response.json()

        # 1. Phase 14.1 Frozen Reference
        ref = body["frozen_phase14_1_reference"]
        assert ref["commit"] == "03cd93a"
        assert ref["candidate_trials"] == 5
        assert ref["total_criteria"] == 77
        assert ref["criteria_loading_mean_ms"] == 128.32
        assert ref["local_pipeline_mean_ms"] == 181.60
        assert ref["criteria_loading_queries"] == 5
        assert ref["gemini_latency"] == "NOT MEASURED"
        assert ref["real_http_latency"] == "NOT MEASURED"

        # 2. Phase 14.2 Controlled Same-Run Experiment
        exp = body["controlled_same_run_experiment"]
        query = exp["primary_query_count"]
        assert query["baseline"] == 5
        assert query["optimized"] == 1
        assert query["reduction"] == 4
        assert query["reduction_pct"] == 80.0

        crit = exp["criteria_loading_latency_ms"]
        assert round(crit["baseline"]["mean_ms"], 2) == 121.55
        assert round(crit["optimized"]["mean_ms"], 2) == 25.34
        assert crit["percentage_improvement"] == 79.15
        assert crit["absolute_reduction_ms"] == 96.21

        pipe = exp["local_pipeline_latency_ms"]
        assert round(pipe["baseline"]["mean_ms"], 2) == 163.63
        assert round(pipe["optimized"]["mean_ms"], 2) == 67.57
        assert pipe["percentage_improvement"] == 58.71
        assert pipe["absolute_reduction_ms"] == 96.06

        # 3. Direct PostgreSQL measurement
        pg = body["real_postgresql_measurement"]
        assert pg["available"] is True
        assert pg["sequential_5_trials_mean_ms"] == 118.51
        assert pg["batched_5_trials_mean_ms"] == 2.79
        assert pg["real_db_pct_improvement"] == 97.65

        # 4. Unmeasured components
        unmeasured = body["unmeasured_components"]
        assert any("Gemini API" in item for item in unmeasured)
        assert any("HTTP" in item for item in unmeasured)


# =============================================================================
# Phase 12 Safety Data Parity Tests
# =============================================================================

def test_safety_endpoint_data_parity(mock_admin):
    """Verify safety pipeline and error injection metrics match Phase 12 artifacts."""
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    with TestClient(app) as client:
        response = client.get("/api/evaluation/safety")
        assert response.status_code == 200
        body = response.json()

        assert body["evidence_classification"] == "SYNTHETIC / DEVELOPMENT FIXTURE"
        summary = body["summary"]

        assert summary["s_e0_synthetic_unmitigated_unsafe_rate"] == 0.5833
        assert summary["s_e4_synthetic_safety_pipeline_unsafe_rate"] == 0.0
        assert summary["s_e4_hr_routing_recall"] == 1.0

        err = summary["error_injection"]
        assert err["total_injections"] == 14
        assert err["detected_count"] == 14
        assert err["detection_rate"] == 1.0
        assert err["aggregate_interception_count"] == 14
        assert err["aggregate_interception_rate"] == 1.0
        assert err["missed_count"] == 0

        # Safety ablations
        ablations = body["safety_ablations"]
        assert len(ablations) == 7
        ablation_ids = [a["ablation_id"] for a in ablations]
        assert "A-S1" in ablation_ids
        assert "A-S7" in ablation_ids

        # Error scenarios
        scenarios = body["error_scenarios"]
        assert len(scenarios) == 14
        assert all(s["detected"] is True for s in scenarios)


# =============================================================================
# Phase 11 Ablations Data Parity Tests
# =============================================================================

def test_ablations_endpoint_data_parity(mock_admin):
    """Verify ablation studies match Phase 11 artifacts with strict n=6 guardrail."""
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    with TestClient(app) as client:
        response = client.get("/api/evaluation/ablations")
        assert response.status_code == 200
        body = response.json()

        assert body["sample_size"] == 6
        assert body["evidence_classification"] == "SYNTHETIC / DEVELOPMENT FIXTURE"
        assert "n=6" in body["disclaimer"]

        # 5 experiments: E0 through E4
        experiments = body["experiments"]
        assert len(experiments) == 5
        exp_ids = [e["experiment_id"] for e in experiments]
        assert exp_ids == [
            "E0_BASELINE",
            "E1_STRUCTURED_PROFILE",
            "E2_DENSE_RAG",
            "E3_HYBRID_RAG",
            "E4_RERANKED_RAG",
        ]

        # 5 ablations: A1 through A5
        ablations = body["ablations"]
        assert len(ablations) == 5
        abl_ids = [a["ablation_id"] for a in ablations]
        assert abl_ids == ["A1", "A2", "A3", "A4", "A5"]
        assert all(a["is_development_fixture_observation_only"] is True for a in ablations)
        assert all(a["empirical_superiority_claim_permitted"] is False for a in ablations)


# =============================================================================
# Overview Data Parity Tests
# =============================================================================

def test_overview_endpoint_data_parity(mock_admin):
    """Verify executive overview reflects complete Phase 5–14 coverage and guardrails."""
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    with TestClient(app) as client:
        response = client.get("/api/evaluation/overview")
        assert response.status_code == 200
        body = response.json()

        coverage = body["evaluation_coverage"]
        phase_ids = [c["phase_id"] for c in coverage]
        assert "Phase 5" in phase_ids
        assert "Phase 12" in phase_ids
        assert "Phase 14.1" in phase_ids
        assert "Phase 14.2" in phase_ids

        highlights = body["highlights"]
        assert len(highlights) >= 5
        titles = [h["title"] for h in highlights]
        assert "Adversarial Safety Interception" in titles
        assert "Primary SQL Query Reduction" in titles
        assert "Criteria Loading Latency Improvement" in titles

        disclaimers = body["disclaimers"]
        assert len(disclaimers) >= 3
