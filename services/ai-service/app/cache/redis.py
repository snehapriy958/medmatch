import logging

import redis
from redis import Redis
from redis.exceptions import RedisError

from app.config.settings import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """
    Singleton Redis client used across the application.

    This class is responsible only for:
    - Creating the Redis connection
    - Verifying connectivity
    - Providing access to the Redis client

    It does NOT implement caching logic.
    """

    _client: Redis | None = None

    @classmethod
    def get_client(cls) -> Redis:
        """
        Return a singleton Redis client instance.
        """

        if cls._client is None:
            cls._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30,
            )

        return cls._client

    @classmethod
    def ping(cls) -> bool:
        """
        Verify Redis connectivity.
        """

        try:
            return bool(cls.get_client().ping())

        except RedisError:
            logger.exception(
                "Failed to connect to Redis."
            )
            raise