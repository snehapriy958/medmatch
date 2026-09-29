"""
Unit tests for background task status endpoint security.

Verifies:
1. Unauthenticated request is rejected (401).
2. Authenticated request for same hospital tenant succeeds (200).
3. Authenticated request for different hospital tenant is rejected (403).
4. Nonexistent task is rejected (404).
5. Valid task returns expected status and does not leak internal traces.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_hospital_id, get_current_user
from app.main import app
from app.services.task_registry import record_task_tenant


@pytest.fixture
def hospital_a():
    return uuid4()


@pytest.fixture
def hospital_b():
    return uuid4()


@pytest.fixture
def user_hospital_a(hospital_a):
    return {
        "sub": str(uuid4()),
        "email": "doctor@hospital-a.org",
        "role": "RESEARCHER",
        "hospital_id": str(hospital_a),
    }


@pytest.fixture
def user_hospital_b(hospital_b):
    return {
        "sub": str(uuid4()),
        "email": "doctor@hospital-b.org",
        "role": "RESEARCHER",
        "hospital_id": str(hospital_b),
    }


def test_unauthenticated_request_returns_401():
    """1. Unauthenticated request must return 401 Unauthorized."""
    # Ensure no dependency overrides
    app.dependency_overrides.clear()

    with TestClient(app) as client:
        response = client.get("/api/tasks/some-arbitrary-task-id")

    assert response.status_code == 401
    assert "detail" in response.json()


def test_authenticated_same_tenant_request_succeeds(hospital_a, user_hospital_a):
    """2. Authenticated same-tenant request returns 200 with task status."""
    task_id = str(uuid4())
    record_task_tenant(task_id, hospital_a)

    app.dependency_overrides[get_current_user] = lambda: user_hospital_a
    app.dependency_overrides[get_current_hospital_id] = lambda: hospital_a

    try:
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"trial_id": str(uuid4()), "message": "Success"}

        with patch("app.api.routes.tasks.AsyncResult", return_value=mock_result):
            with TestClient(app) as client:
                response = client.get(f"/api/tasks/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "SUCCESS"
        assert "result" in data
        assert data["result"]["message"] == "Success"
    finally:
        app.dependency_overrides.clear()


def test_authenticated_cross_tenant_request_rejected(hospital_a, hospital_b, user_hospital_b):
    """3. Authenticated cross-tenant request must return 403 Forbidden."""
    task_id = str(uuid4())
    # Task belongs to Hospital A
    record_task_tenant(task_id, hospital_a)

    # User belongs to Hospital B
    app.dependency_overrides[get_current_user] = lambda: user_hospital_b
    app.dependency_overrides[get_current_hospital_id] = lambda: hospital_b

    try:
        mock_result = MagicMock()
        mock_result.status = "PENDING"
        mock_result.date_done = None
        mock_result.result = None

        with patch("app.api.routes.tasks.AsyncResult", return_value=mock_result):
            with TestClient(app) as client:
                response = client.get(f"/api/tasks/{task_id}")

        assert response.status_code == 403
        assert "Access forbidden" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_nonexistent_task_returns_404(hospital_a, user_hospital_a):
    """4. Nonexistent task must return 404 Not Found rather than Celery's default PENDING."""
    nonexistent_task_id = f"nonexistent-{uuid4()}"

    app.dependency_overrides[get_current_user] = lambda: user_hospital_a
    app.dependency_overrides[get_current_hospital_id] = lambda: hospital_a

    try:
        mock_result = MagicMock()
        mock_result.status = "PENDING"
        mock_result.date_done = None
        mock_result.result = None

        with patch("app.api.routes.tasks.AsyncResult", return_value=mock_result):
            with TestClient(app) as client:
                response = client.get(f"/api/tasks/{nonexistent_task_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    finally:
        app.dependency_overrides.clear()


def test_valid_task_failure_sanitizes_internal_errors(hospital_a, user_hospital_a):
    """5. Valid task with failure state returns 200 without leaking stack traces or internal exception details."""
    task_id = str(uuid4())
    record_task_tenant(task_id, hospital_a)

    app.dependency_overrides[get_current_user] = lambda: user_hospital_a
    app.dependency_overrides[get_current_hospital_id] = lambda: hospital_a

    try:
        mock_result = MagicMock()
        mock_result.status = "FAILURE"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = True
        mock_result.result = RuntimeError("Sensitive DB Connection String postgres://user:secret@10.0.0.1 failed")

        with patch("app.api.routes.tasks.AsyncResult", return_value=mock_result):
            with TestClient(app) as client:
                response = client.get(f"/api/tasks/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "FAILURE"
        assert "error" in data
        # Ensure sensitive internal exception repr is NOT leaked
        assert "postgres://" not in data["error"]
        assert "secret" not in data["error"]
        assert data["error"] == "Task processing failed"
    finally:
        app.dependency_overrides.clear()


def test_task_status_survives_pod_restart_via_redis(hospital_a, user_hospital_a):
    """6. Simulates pod/process restart: in-memory cache cleared, tenant recovered from Redis."""
    from app.services.task_registry import clear_in_memory_task_tenants

    task_id = str(uuid4())
    # Simulate Redis having the key
    mock_redis = MagicMock()
    mock_redis.get.return_value = str(hospital_a)

    # Clear in-memory cache to simulate clean restart
    clear_in_memory_task_tenants()

    app.dependency_overrides[get_current_user] = lambda: user_hospital_a
    app.dependency_overrides[get_current_hospital_id] = lambda: hospital_a

    try:
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"status": "ok"}

        with patch("app.cache.redis.RedisClient.get_client", return_value=mock_redis), \
             patch("app.api.routes.tasks.AsyncResult", return_value=mock_result):
            with TestClient(app) as client:
                response = client.get(f"/api/tasks/{task_id}")

        assert response.status_code == 200
        assert response.json()["task_id"] == task_id
        mock_redis.get.assert_called_with(f"medmatch:task:tenant:{task_id}")
    finally:
        app.dependency_overrides.clear()
        clear_in_memory_task_tenants()


def test_missing_registry_fails_closed_returns_404(hospital_a, user_hospital_a):
    """7. Fail-closed: if task is not in Redis and not in memory, return 404 even if Celery has task."""
    from app.services.task_registry import clear_in_memory_task_tenants

    task_id = str(uuid4())
    mock_redis = MagicMock()
    mock_redis.get.return_value = None  # Key missing from Redis
    clear_in_memory_task_tenants()

    app.dependency_overrides[get_current_user] = lambda: user_hospital_a
    app.dependency_overrides[get_current_hospital_id] = lambda: hospital_a

    try:
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.info = {}
        mock_result.result = {}

        with patch("app.cache.redis.RedisClient.get_client", return_value=mock_redis), \
             patch("app.api.routes.tasks.AsyncResult", return_value=mock_result):
            with TestClient(app) as client:
                response = client.get(f"/api/tasks/{task_id}")

        # Must fail-closed with 404
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    finally:
        app.dependency_overrides.clear()
        clear_in_memory_task_tenants()
