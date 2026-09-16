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

    Cache failures are handled gracefully because Redis is used
    as an optimization layer and should not make core application
    operations unavailable.
    """

    def __init__(self) -> None:
        self.client = RedisClient.get_client()

    def get(
        self,
        key: str,
    ) -> Any | None:
        """
        Retrieve and deserialize a cached value.

        Returns None when the key does not exist or when the cached
        value cannot be retrieved or deserialized.
        """

        try:
            value = self.client.get(key)

            if value is None:
                return None

            if isinstance(value, bytes):
                value = value.decode("utf-8")

            return json.loads(value)

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):
            logger.exception(
                "Failed to deserialize cache value for key '%s'.",
                key,
            )
            return None

        except RedisError:
            logger.exception(
                "Failed to retrieve cache value for key '%s'.",
                key,
            )
            return None

        except Exception:
            logger.exception(
                "Unexpected cache retrieval failure for key '%s'.",
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
        Serialize and store a value in Redis with a positive TTL.

        Returns False when serialization or Redis storage fails.
        """

        if ttl <= 0:
            logger.error(
                "Cache TTL must be greater than zero for key '%s'.",
                key,
            )
            return False

        try:
            serialized = json.dumps(
                value,
                default=str,
            )

        except (
            TypeError,
            ValueError,
        ):
            logger.exception(
                "Failed to serialize cache value for key '%s'.",
                key,
            )
            return False

        try:
            result = self.client.set(
                name=key,
                value=serialized,
                ex=ttl,
            )

            return bool(result)

        except RedisError:
            logger.exception(
                "Failed to store cache value for key '%s'.",
                key,
            )
            return False

        except Exception:
            logger.exception(
                "Unexpected cache storage failure for key '%s'.",
                key,
            )
            return False

    def delete(
        self,
        key: str,
    ) -> bool:
        """
        Remove a cache entry.

        Returns True when at least one key was deleted.
        """

        try:
            return bool(
                self.client.delete(key)
            )

        except RedisError:
            logger.exception(
                "Failed to delete cache key '%s'.",
                key,
            )
            return False

        except Exception:
            logger.exception(
                "Unexpected cache deletion failure for key '%s'.",
                key,
            )
            return False

    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Check whether a cache key exists.
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

        except Exception:
            logger.exception(
                "Unexpected cache existence check failure "
                "for key '%s'.",
                key,
            )
            return False