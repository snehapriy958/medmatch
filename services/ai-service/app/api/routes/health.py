from datetime import UTC, datetime
import os
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import text

from app.api.deps import get_current_user
from app.cache.redis import RedisClient
from app.config.settings import settings
from app.db.database import engine


router = APIRouter(
    prefix=settings.API_PREFIX,
    tags=["Health"],
)


def _timestamp() -> str:
    """
    Return the current timestamp in UTC.
    """

    return datetime.now(UTC).isoformat()


def _readiness_response(
    checks: dict[str, str],
    is_ready: bool,
) -> dict[str, Any]:
    """
    Build a consistent readiness response.
    """

    return {
        "status": "UP" if is_ready else "DOWN",
        "service": settings.APP_NAME,
        "checks": checks,
        "timestamp": _timestamp(),
    }


@router.get("/")
def root() -> dict[str, str]:
    """
    Basic service endpoint.
    """

    return {
        "message": "MedMatch AI Service is running",
    }


@router.get("/health")
def health() -> dict[str, Any]:
    """
    General health endpoint.

    Indicates that the API application is responding.
    """

    return {
        "status": "UP",
        "service": settings.APP_NAME,
        "timestamp": _timestamp(),
    }


@router.get("/health/live")
def liveness() -> dict[str, Any]:
    """
    Kubernetes liveness probe.

    This endpoint intentionally performs no external dependency checks.
    A successful response means that the API process is alive.
    """

    return {
        "status": "UP",
        "service": settings.APP_NAME,
        "timestamp": _timestamp(),
    }


@router.get("/health/ready")
def readiness() -> dict[str, Any]:
    """
    Kubernetes readiness probe.

    Verifies that required dependencies are available:

    - PostgreSQL connectivity
    - Upload directory availability
    - Redis connectivity
    - pgvector extension availability

    Returns HTTP 503 when the service is not ready so Kubernetes
    can remove the pod from service traffic.
    """

    checks: dict[str, str] = {}

    #
    # PostgreSQL & Migration Schema
    #
    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

            # Secondary readiness check: verify database schema is at expected Alembic head
            version = connection.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            ).scalar_one_or_none()

            expected_head = "6f0604b23df6"
            if version != expected_head:
                raise RuntimeError(
                    f"Alembic migration version mismatch: expected {expected_head}, found {version}"
                )

        checks["database"] = "UP"

    except Exception:
        checks["database"] = "DOWN"

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_readiness_response(
                checks=checks,
                is_ready=False,
            ),
        )

    #
    # Upload directory
    #
    try:
        upload_dir = Path(settings.UPLOAD_DIR)

        upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not upload_dir.is_dir():
            raise RuntimeError(
                "Upload path is not a directory."
            )

        if not os.access(upload_dir, os.W_OK):
            raise PermissionError(
                f"Upload directory '{upload_dir}' is not writable."
            )

        checks["uploads"] = "UP"

    except Exception:
        checks["uploads"] = "DOWN"

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_readiness_response(
                checks=checks,
                is_ready=False,
            ),
        )

    #
    # Redis
    #
    try:
        RedisClient.ping()

        checks["redis"] = "UP"

    except Exception:
        checks["redis"] = "DOWN"

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_readiness_response(
                checks=checks,
                is_ready=False,
            ),
        )

    #
    # pgvector
    #
    try:
        with engine.connect() as connection:

            extension = connection.execute(
                text(
                    """
                    SELECT extversion
                    FROM pg_extension
                    WHERE extname = 'vector'
                    """
                )
            ).scalar_one_or_none()

            if extension is None:
                raise RuntimeError(
                    "pgvector extension is not installed."
                )

            connection.execute(
                text(
                    """
                    SELECT '[0.1,0.2,0.3]'::vector
                    <=> '[0.1,0.2,0.3]'::vector
                    """
                )
            )

        checks["vector_search"] = "UP"

    except Exception:
        checks["vector_search"] = "DOWN"

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_readiness_response(
                checks=checks,
                is_ready=False,
            ),
        )

    return _readiness_response(
        checks=checks,
        is_ready=True,
    )


@router.get("/db-check")
def db_check() -> dict[str, str]:
    """
    Simple PostgreSQL connectivity check.
    """

    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        return {
            "database": "connected",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc


@router.get("/profile")
def get_profile(
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Protected endpoint.

    Returns authenticated user's JWT claims.
    """

    return {
        "message": "Authentication successful",
        "user": current_user,
    }