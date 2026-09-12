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
    # PostgreSQL
    #
    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
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

        test_file = (
            upload_dir
            / ".readiness_check.tmp"
        )

        test_file.write_text(
            "MedMatch readiness check",
            encoding="utf-8",
        )

        test_file.unlink()

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