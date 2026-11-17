"""
Journey E: Monitoring and Reliability Integration Tests
Tests:
1. Liveness probe (/health) returns 200 healthy
2. Readiness probe (/api/health/ready) evaluates DB, Redis, and upload volume
3. Dependency failure: Database offline marks readiness DOWN (503)
4. Dependency failure: Redis offline marks readiness DOWN (503)
5. Prometheus instrumentation: /metrics endpoint accessible and emits counters
6. Graceful degradation: Service reports accurate readiness component health
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
import redis

from app.main import app


def test_journey_e_liveness_endpoint():
    """Liveness probe must return 200 without external dependencies."""
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "healthy"}


def test_journey_e_readiness_all_dependencies_up():
    """Readiness probe returns 200 UP when DB and Redis succeed."""
    with patch("app.api.routes.health.engine.connect") as mock_connect, \
         patch("app.api.routes.health.RedisClient.ping") as mock_redis_ping:

        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_result = MagicMock()
        # Mock alembic version head and pgvector version
        mock_result.scalar_one_or_none.side_effect = ["6f0604b23df6", "0.5.1"]
        mock_conn.execute.return_value = mock_result
        mock_redis_ping.return_value = True

        with TestClient(app) as client:
            res = client.get("/api/health/ready")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "UP"
            assert data["checks"]["database"] == "UP"
            assert data["checks"]["redis"] == "UP"


def test_journey_e_readiness_database_failure_degrades_gracefully():
    """Database connection failure sets readiness to 503 DOWN."""
    with patch("app.api.routes.health.engine.connect", side_effect=OperationalError("Connection failed", {}, None)), \
         patch("app.api.routes.health.RedisClient.ping", return_value=True):

        with TestClient(app) as client:
            res = client.get("/api/health/ready")
            assert res.status_code == 503
            data = res.json()
            detail = data.get("detail", data)
            assert detail["status"] == "DOWN"
            assert detail["checks"]["database"] == "DOWN"


def test_journey_e_readiness_redis_failure_degrades_gracefully():
    """Redis connection failure sets readiness to 503 DOWN."""
    with patch("app.api.routes.health.engine.connect") as mock_connect, \
         patch("app.api.routes.health.RedisClient.ping", side_effect=redis.ConnectionError("Redis unreachable")):

        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = ["6f0604b23df6", "0.5.1"]
        mock_conn.execute.return_value = mock_result

        with TestClient(app) as client:
            res = client.get("/api/health/ready")
            assert res.status_code == 503
            data = res.json()
            detail = data.get("detail", data)
            assert detail["status"] == "DOWN"
            assert detail["checks"]["redis"] == "DOWN"


def test_journey_e_prometheus_metrics_exposed():
    """Prometheus /metrics endpoint is exposed and exports metrics."""
    with TestClient(app) as client:
        res = client.get("/metrics")
        assert res.status_code == 200
        assert "http_requests_total" in res.text or "medmatch" in res.text or "process_cpu_seconds" in res.text
