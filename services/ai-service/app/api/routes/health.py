from datetime import UTC, datetime
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


@router.get("/")
def root() -> dict[str, str]:
    return {
        "message": "MedMatch AI Service is running",
    }


@router.get("/health")
def health() -> dict:
    """
    General health endpoint.
    Used by Docker and monitoring tools.
    """

    return {
        "status": "UP",
        "service": settings.APP_NAME,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/live")
def liveness() -> dict:
    """
    Kubernetes/Docker liveness probe.
    Checks whether the application process is alive.
    """

    return {
        "status": "UP",
        "service": settings.APP_NAME,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/ready")
def readiness() -> dict:
    """
    Kubernetes readiness probe.

    Verifies:
    - PostgreSQL connectivity
    - Upload directory
    - Redis connectivity
    - pgvector availability and vector operation
    """

    checks: dict[str, str] = {}

    #
    # Database
    #
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        checks["database"] = "UP"

    except Exception:
        checks["database"] = "DOWN"

        return {
            "status": "DOWN",
            "service": settings.APP_NAME,
            "checks": checks,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    #
    # Upload directory
    #
    upload_dir = Path(settings.UPLOAD_DIR)

    if upload_dir.exists() and upload_dir.is_dir():
        checks["uploads"] = "UP"

    else:
        checks["uploads"] = "DOWN"

        return {
            "status": "DOWN",
            "service": settings.APP_NAME,
            "checks": checks,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    #
    # Redis
    #
    try:
        RedisClient.ping()
        checks["redis"] = "UP"

    except Exception:
        checks["redis"] = "DOWN"

        return {
            "status": "DOWN",
            "service": settings.APP_NAME,
            "checks": checks,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    #
    # Vector search / pgvector
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
                    SELECT
                        embedding <=> embedding
                    FROM criteria_embeddings
                    LIMIT 1
                    """
                )
            )

        checks["vector_search"] = "UP"

    except Exception:
        checks["vector_search"] = "DOWN"

        return {
            "status": "DOWN",
            "service": settings.APP_NAME,
            "checks": checks,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    #
    # All readiness checks passed
    #
    return {
        "status": "UP",
        "service": settings.APP_NAME,
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/db-check")
def db_check() -> dict[str, str]:
    """
    Simple database connectivity check.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

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
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """
    Protected endpoint.
    Returns authenticated user's JWT claims.
    """

    return {
        "message": "Authentication successful",
        "user": current_user,
    }