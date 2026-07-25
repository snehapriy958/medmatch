import redis


def test_redis_connection():

    client = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    assert client.ping() is True