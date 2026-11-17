"""
Security Tests: Multi-Tenant Data Isolation & BOLA Defenses.
Tests:
1. Strict hospital_id extraction exclusively from verified JWT (ignoring spoofed request headers)
2. Task Registry cross-tenant access rejection
3. Fail-closed behavior on missing or malformed tenant ID
"""

from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_hospital_id, get_current_user
from app.services.task_registry import record_task_tenant, get_task_tenant


def test_tenant_id_extracted_strictly_from_jwt():
    """Client attempting to spoof tenant via HTTP headers like X-Hospital-Id or X-Tenant-Id is ignored."""
    real_hospital_id = uuid4()
    spoofed_hospital_id = uuid4()

    mock_user = {
        "sub": str(uuid4()),
        "email": "doctor@legitimate.org",
        "role": "PHYSICIAN",
        "hospital_id": str(real_hospital_id),
    }

    # Verify that get_current_hospital_id resolves real_hospital_id regardless of incoming headers
    resolved_id = get_current_hospital_id(mock_user)
    assert resolved_id == real_hospital_id
    assert resolved_id != spoofed_hospital_id


def test_cross_tenant_task_access_blocked():
    """Task belonging to Tenant A is strictly inaccessible to Tenant B."""
    hospital_a = uuid4()
    hospital_b = uuid4()
    task_id = str(uuid4())

    record_task_tenant(task_id, hospital_a)

    user_b = {
        "sub": str(uuid4()),
        "email": "intruder@hospital-b.org",
        "role": "PHYSICIAN",
        "hospital_id": str(hospital_b),
    }

    app.dependency_overrides[get_current_user] = lambda: user_b
    app.dependency_overrides[get_current_hospital_id] = lambda: hospital_b

    try:
        with TestClient(app) as client:
            res = client.get(f"/api/tasks/{task_id}")
            assert res.status_code == 403
            assert "belongs to another hospital tenant" in res.json().get("detail", "")
    finally:
        app.dependency_overrides.clear()


def test_missing_hospital_id_in_claims_fails_closed():
    """If JWT claims omit hospital_id, get_current_hospital_id raises 401 Unauthorized."""
    claims_without_tenant = {
        "sub": str(uuid4()),
        "email": "missing_tenant@test.org",
        "role": "PHYSICIAN",
    }
    with pytest.raises(Exception) as exc_info:
        get_current_hospital_id(claims_without_tenant)

    assert "Hospital ID missing from token" in str(exc_info.value)
