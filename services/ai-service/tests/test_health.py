from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_healthy():
    with TestClient(app) as client:

        response = client.get(
            "/health"
        )

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy"
    }


def test_health_endpoint_returns_json():
    with TestClient(app) as client:

        response = client.get(
            "/health"
        )

    assert (
        response.headers[
            "content-type"
        ].startswith(
            "application/json"
        )
    )


def test_readiness_matching_migration_head_marks_database_up():
    """
    1. Migration head matches expected (6f0604b23df6):
       Readiness reports database check as UP.
    """
    with patch("app.api.routes.health.engine.connect") as mock_connect, \
         patch("app.api.routes.health.RedisClient.ping") as mock_redis_ping:

        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = ["6f0604b23df6", "0.5.1"]
        mock_conn.execute.return_value = mock_result
        mock_redis_ping.return_value = True

        with TestClient(app) as client:
            response = client.get("/api/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"
        assert data["checks"]["database"] == "UP"


def test_readiness_mismatched_migration_head_marks_database_down():
    """
    2. Migration head does NOT match (e.g. outdated revision):
       Readiness marks database as DOWN and returns 503.
    """
    with patch("app.api.routes.health.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "0008"
        mock_conn.execute.return_value = mock_result

        with TestClient(app) as client:
            response = client.get("/api/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert data["detail"]["status"] == "DOWN"
        assert data["detail"]["checks"]["database"] == "DOWN"


def test_readiness_missing_migration_head_marks_database_down():
    """
    2b. Migration head is None (empty alembic_version table):
        Readiness marks database as DOWN and returns 503.
    """
    with patch("app.api.routes.health.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_conn.execute.return_value = mock_result

        with TestClient(app) as client:
            response = client.get("/api/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert data["detail"]["status"] == "DOWN"
        assert data["detail"]["checks"]["database"] == "DOWN"


def test_readiness_table_unavailable_marks_database_down():
    """
    3. alembic_version table or database query unavailable:
       Readiness fails safely, marks database as DOWN, and returns 503.
    """
    with patch("app.api.routes.health.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.side_effect = Exception("relation alembic_version does not exist")

        with TestClient(app) as client:
            response = client.get("/api/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert data["detail"]["status"] == "DOWN"
        assert data["detail"]["checks"]["database"] == "DOWN"