import json
import logging
from typing import Any

from redis.exceptions import RedisError

from app.cache.redis import RedisClient

logger = logging.getLogger(__name__)


class CacheService:
    """
    Provides common Redis cache operations.

    This service abstracts Redis interactions so the rest of
    the application does not communicate with Redis directly.
    """

    def __init__(self) -> None:
        self.client = RedisClient.get_client()

    def get(
        self,
        key: str,
    ) -> Any | None:
        """
        Retrieve a cached value.
        """

        try:
            value = self.client.get(key)

            if value is None:
                return None

            return json.loads(value)

        except json.JSONDecodeError:
            logger.exception(
                "Failed to deserialize cache for key '%s'.",
                key,
            )
            return None

        except RedisError:
            logger.exception(
                "Failed to retrieve cache for key '%s'.",
                key,
            )
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int,
    ) -> bool:
        """
        Store a value in Redis with a TTL.
        """

        try:
            serialized = json.dumps(
                value,
                default=str,
            )

            return bool(
                self.client.set(
                    name=key,
                    value=serialized,
                    ex=ttl,
                )
            )

        except RedisError:
            logger.exception(
                "Failed to store cache for key '%s'.",
                key,
            )
            return False

    def delete(
        self,
        key: str,
    ) -> bool:
        """
        Remove a cache entry.
        """

        try:
            return bool(
                self.client.delete(key)
            )

        except RedisError:
            logger.exception(
                "Failed to delete cache for key '%s'.",
                key,
            )
            return False

    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Check whether a key exists.
        """

        try:
            return bool(
                self.client.exists(key)
            )

        except RedisError:
            logger.exception(
                "Failed to check cache key '%s'.",
                key,
            )
            return False