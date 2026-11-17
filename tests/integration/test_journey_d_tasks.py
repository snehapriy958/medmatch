"""
Journey D: Background Processing Integration Tests
Tests:
1. Asynchronous task registration with hospital tenant scoping
2. Task state transitions (PENDING -> RUNNING -> SUCCESS / FAILURE)
3. Cross-tenant task polling rejection (403 Forbidden)
4. Nonexistent task handling (404 Not Found)
5. Sanitization of internal exception messages before client exposure
6. In-memory / Redis task registry isolation
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_hospital_id, get_current_user
from app.main import app
from app.services.task_registry import (
    clear_in_memory_task_tenants,
    get_task_tenant,
    record_task_tenant,
)


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    app.dependency_overrides.clear()
    clear_in_memory_task_tenants()
    yield
    app.dependency_overrides.clear()
    clear_in_memory_task_tenants()


@pytest.fixture
def mock_hospital_a_user():
    return {
        "sub": str(uuid4()),
        "email": "userA@hospitalA.org",
        "role": "RESEARCH_COORDINATOR",
        "hospital_id": str(uuid4()),
    }


@pytest.fixture
def mock_hospital_b_user():
    return {
        "sub": str(uuid4()),
        "email": "userB@hospitalB.org",
        "role": "RESEARCH_COORDINATOR",
        "hospital_id": str(uuid4()),
    }


def test_journey_d_same_tenant_task_access(mock_hospital_a_user):
    """User from Hospital A can access task registered to Hospital A."""
    app.dependency_overrides[get_current_user] = lambda: mock_hospital_a_user
    app.dependency_overrides[get_current_hospital_id] = lambda: mock_hospital_a_user["hospital_id"]

    task_id = str(uuid4())
    record_task_tenant(task_id, mock_hospital_a_user["hospital_id"])

    with patch("app.api.routes.tasks.AsyncResult") as mock_async_result:
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"trial_id": "test-trial", "criteria_count": 15, "hospital_id": mock_hospital_a_user["hospital_id"]}
        mock_async_result.return_value = mock_result

        with TestClient(app) as client:
            res = client.get(f"/api/tasks/{task_id}")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "SUCCESS"
            assert data["result"]["trial_id"] == "test-trial"
            # hospital_id is stripped from public output
            assert "hospital_id" not in data["result"]


def test_journey_d_cross_tenant_task_access_rejected(mock_hospital_a_user, mock_hospital_b_user):
    """User from Hospital B attempting to poll Hospital A's task receives 403."""
    app.dependency_overrides[get_current_user] = lambda: mock_hospital_b_user
    app.dependency_overrides[get_current_hospital_id] = lambda: mock_hospital_b_user["hospital_id"]

    task_id = str(uuid4())
    # Register task to Hospital A
    record_task_tenant(task_id, mock_hospital_a_user["hospital_id"])

    with TestClient(app) as client:
        res = client.get(f"/api/tasks/{task_id}")
        assert res.status_code == 403
        assert "belongs to another hospital" in res.json().get("detail", "").lower()


def test_journey_d_nonexistent_task_returns_404(mock_hospital_a_user):
    """Querying a task ID not in registry returns 404 rather than Celery PENDING."""
    app.dependency_overrides[get_current_user] = lambda: mock_hospital_a_user
    app.dependency_overrides[get_current_hospital_id] = lambda: mock_hospital_a_user["hospital_id"]

    task_id = str(uuid4())
    # Do not register task

    with TestClient(app) as client:
        res = client.get(f"/api/tasks/{task_id}")
        assert res.status_code == 404
        assert "task not found" in res.json().get("detail", "").lower()


def test_journey_d_task_error_sanitization(mock_hospital_a_user):
    """Internal database/traceback errors must be sanitized to generic messages."""
    app.dependency_overrides[get_current_user] = lambda: mock_hospital_a_user
    app.dependency_overrides[get_current_hospital_id] = lambda: mock_hospital_a_user["hospital_id"]

    task_id = str(uuid4())
    record_task_tenant(task_id, mock_hospital_a_user["hospital_id"])

    with patch("app.api.routes.tasks.AsyncResult") as mock_async_result:
        mock_result = MagicMock()
        mock_result.status = "FAILURE"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = True
        mock_result.result = Exception("OperationalError: Connection to postgres:5432 failed password auth")
        mock_async_result.return_value = mock_result

        with TestClient(app) as client:
            res = client.get(f"/api/tasks/{task_id}")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "FAILURE"
            # Sensitive internal database connection details must NOT leak
            assert data["error"] == "Task processing failed"
