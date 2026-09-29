"""
Task Tenant Registry Service.

Provides tenant tracking for background asynchronous Celery tasks,
ensuring hospital tenant isolation on task status lookup endpoints.
In production environments, Redis serves as the authoritative, distributed
task-to-tenant mapping across all API and worker replicas.
"""

import logging
from typing import Any
from uuid import UUID

from celery.result import AsyncResult
from redis.exceptions import RedisError

from app.cache.redis import RedisClient
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Bounded in-memory fallback cache to ensure tenant tracking works
# in offline, local, or mocked unit-test environments without live Redis.
_IN_MEMORY_TASK_TENANTS: dict[str, str] = {}
_MAX_IN_MEMORY_ENTRIES = 10000


def _normalize_tenant_id(hospital_id: str | UUID) -> str:
    return str(hospital_id).strip().lower()


def clear_in_memory_task_tenants() -> None:
    """Clear in-memory task registry (used primarily for test isolation)."""
    _IN_MEMORY_TASK_TENANTS.clear()


def record_task_tenant(
    task_id: str,
    hospital_id: str | UUID,
    expires_in: int = 86400,
) -> None:
    """
    Record hospital tenant ownership for an enqueued background task.
    In production, Redis is strictly required as the authoritative store.
    """
    normalized_tenant = _normalize_tenant_id(hospital_id)

    # 1. Update in-memory registry for local development / test caching
    if len(_IN_MEMORY_TASK_TENANTS) >= _MAX_IN_MEMORY_ENTRIES:
        _IN_MEMORY_TASK_TENANTS.pop(next(iter(_IN_MEMORY_TASK_TENANTS)), None)
    _IN_MEMORY_TASK_TENANTS[task_id] = normalized_tenant

    # 2. Persist to Redis (authoritative multi-replica store)
    try:
        redis_client = RedisClient.get_client()
        redis_key = f"medmatch:task:tenant:{task_id}"
        redis_client.set(redis_key, normalized_tenant, ex=expires_in)
    except (RedisError, Exception) as exc:
        if settings.ENVIRONMENT == "production":
            logger.error(
                "Failed to record task tenant in authoritative Redis store: %s",
                exc,
            )
            raise RuntimeError(
                f"Authoritative task tenant registration failed in production: {exc}"
            ) from exc
        logger.debug(
            "Could not persist task tenant to Redis (in-memory tracking active in dev/test): %s",
            exc,
        )


def get_task_tenant(task_id: str) -> str | None:
    """
    Retrieve the hospital tenant associated with a task ID.

    In production:
    Queries Redis as the authoritative distributed source. If not found in
    Redis, inspects Celery result metadata. If unmapped, returns None
    (fail-closed: calling endpoints will return 404 Not Found).

    In development / test:
    Queries in-memory cache, then Redis, then Celery metadata.
    """
    is_production = settings.ENVIRONMENT == "production"

    # In non-production, check in-memory cache first for fast test execution
    if not is_production and task_id in _IN_MEMORY_TASK_TENANTS:
        return _IN_MEMORY_TASK_TENANTS[task_id]

    # Authoritative Redis query
    try:
        redis_client = RedisClient.get_client()
        redis_key = f"medmatch:task:tenant:{task_id}"
        val = redis_client.get(redis_key)
        if val:
            tenant_str = str(val).strip().lower()
            _IN_MEMORY_TASK_TENANTS[task_id] = tenant_str
            return tenant_str
    except (RedisError, Exception) as exc:
        logger.debug("Redis query failed for task tenant: %s", exc)

    # Fallback: inspect Celery task result metadata
    try:
        result = AsyncResult(task_id)
        info = result.info
        if isinstance(info, dict) and "hospital_id" in info:
            tenant_str = _normalize_tenant_id(info["hospital_id"])
            _IN_MEMORY_TASK_TENANTS[task_id] = tenant_str
            return tenant_str
        if (
            result.successful()
            and isinstance(result.result, dict)
            and "hospital_id" in result.result
        ):
            tenant_str = _normalize_tenant_id(result.result["hospital_id"])
            _IN_MEMORY_TASK_TENANTS[task_id] = tenant_str
            return tenant_str
    except Exception as exc:
        logger.debug("Celery result inspection failed for task tenant: %s", exc)

    # Fail-closed: unmapped tasks return None
    return None
