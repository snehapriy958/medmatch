import logging

import redis
from redis import Redis
from redis.exceptions import (
    ConnectionError,
    RedisError,
    TimeoutError,
)

from app.config.settings import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Singleton Redis client used across the application.

    This class is responsible only for:
    - Creating the Redis connection client
    - Managing the shared Redis connection pool
    - Verifying connectivity
    - Providing access to the Redis client

    Cache behavior and serialization are handled separately by
    CacheService.
    """

    _client: Redis | None = None

    @classmethod
    def get_client(cls) -> Redis:
        """
        Return a singleton Redis client instance.

        The Redis client uses connection pooling internally. Creating
        the client does not require Redis to be immediately available;
        individual operations and explicit health checks handle
        connectivity failures.
        """

        if cls._client is None:
            cls._client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
                max_connections=50,
                retry_on_timeout=True,
            )

            logger.info(
                "Redis client initialized."
            )

        return cls._client

    @classmethod
    def ping(cls) -> bool:
        """
        Verify Redis connectivity.

        Raises:
            RedisError: If Redis cannot be reached.
        """

        try:
            return bool(
                cls.get_client().ping()
            )

        except (
            ConnectionError,
            TimeoutError,
        ):
            logger.exception(
                "Failed to connect to Redis."
            )
            raise

        except RedisError:
            logger.exception(
                "Redis connectivity check failed."
            )
            raise