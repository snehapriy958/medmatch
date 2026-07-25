from app.cache.cache_keys import CacheKeys


def test_embedding_key():

    key = CacheKeys.embedding("Hello World")

    assert key.startswith("embedding:")
    assert len(key) > len("embedding:")


def test_retrieval_key():

    key = CacheKeys.retrieval(
        "Patient has stage II breast cancer",
        5,
    )

    assert key.startswith("retrieval:")
    assert key.endswith(":5")


def test_match_key():

    key = CacheKeys.match(12, 42)

    assert key == "match:12:42"