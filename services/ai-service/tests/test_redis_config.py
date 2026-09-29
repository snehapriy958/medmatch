import pytest
from app.config.settings import Settings


def test_redis_config_without_password():
    settings = Settings(
        REDIS_HOST="redis",
        REDIS_PORT=6379,
        REDIS_PASSWORD=None,
        CELERY_BROKER_URL="redis://redis:6379/0",
        CELERY_RESULT_BACKEND="redis://redis:6379/1",
    )
    assert settings.REDIS_URL == "redis://redis:6379/0"
    assert settings.CELERY_BROKER_URL == "redis://redis:6379/0"
    assert settings.CELERY_RESULT_BACKEND == "redis://redis:6379/1"


def test_redis_config_with_password():
    settings = Settings(
        REDIS_HOST="redis",
        REDIS_PORT=6379,
        REDIS_PASSWORD="secret_password_123!",
        CELERY_BROKER_URL="redis://redis:6379/0",
        CELERY_RESULT_BACKEND="redis://redis:6379/1",
    )
    # Password should be safely URL-encoded into URLs
    assert ":secret_password_123%21@" in settings.REDIS_URL
    assert ":secret_password_123%21@" in settings.CELERY_BROKER_URL
    assert ":secret_password_123%21@" in settings.CELERY_RESULT_BACKEND
    assert settings.REDIS_PASSWORD == "secret_password_123!"


def test_redis_config_with_existing_creds_in_url():
    settings = Settings(
        REDIS_HOST="redis",
        REDIS_PORT=6379,
        REDIS_PASSWORD="ignored_password",
        CELERY_BROKER_URL="redis://:existing_pass@redis:6379/0",
        CELERY_RESULT_BACKEND="redis://:existing_pass@redis:6379/1",
    )
    # Should not double-inject credentials
    assert settings.CELERY_BROKER_URL == "redis://:existing_pass@redis:6379/0"
    assert settings.CELERY_RESULT_BACKEND == "redis://:existing_pass@redis:6379/1"


def test_redis_config_production_requires_password():
    with pytest.raises(ValueError, match="REDIS_PASSWORD must be configured in production"):
        Settings(
            ENVIRONMENT="production",
            GOOGLE_API_KEY="test_gemini_api_key",
            TRUSTED_HOSTS=["medmatch.internal"],
            LOG_LEVEL="INFO",
            REDIS_PASSWORD=None,
        )


def test_redis_config_production_empty_password_rejected():
    with pytest.raises(ValueError, match="REDIS_PASSWORD must be configured in production"):
        Settings(
            APPLICATION_PROFILE="production",
            GOOGLE_API_KEY="test_gemini_api_key",
            TRUSTED_HOSTS=["medmatch.internal"],
            LOG_LEVEL="INFO",
            REDIS_PASSWORD="   ",
        )


def test_redis_config_production_with_valid_password_succeeds():
    settings = Settings(
        ENVIRONMENT="production",
        GOOGLE_API_KEY="test_gemini_api_key",
        TRUSTED_HOSTS=["medmatch.internal"],
        LOG_LEVEL="INFO",
        REDIS_PASSWORD="strong_prod_password_#42",
        CELERY_BROKER_URL="redis://redis-service:6379/0",
        CELERY_RESULT_BACKEND="redis://redis-service:6379/1",
    )
    assert settings.REDIS_PASSWORD == "strong_prod_password_#42"
    assert ":strong_prod_password_%2342@" in settings.REDIS_URL
    assert ":strong_prod_password_%2342@" in settings.CELERY_BROKER_URL
