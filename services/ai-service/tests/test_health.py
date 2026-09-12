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