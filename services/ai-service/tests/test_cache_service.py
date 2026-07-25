from app.cache.cache_keys import CacheKeys
from app.cache.cache_service import CacheService


def test_cache_set_get_delete():

    cache = CacheService()

    key = CacheKeys.embedding("Hello World")

    value = {
        "message": "Redis Works!"
    }

    assert cache.set(key, value, ttl=60) is True

    cached = cache.get(key)

    assert cached == value

    assert cache.exists(key) is True

    assert cache.delete(key) is True

    assert cache.exists(key) is False