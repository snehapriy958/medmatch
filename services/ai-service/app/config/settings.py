from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ==========================================================
    # Application
    # ==========================================================
    APP_NAME: str = "MedMatch AI Service"
    APP_VERSION: str = "1.0.0"

    ENVIRONMENT: Literal[
        "development",
        "docker",
        "production",
        "testing",
    ] = "development"

    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost",
            "http://localhost:80",
            "http://localhost:5173",
        ]
    )
    
    TRUSTED_HOSTS: list[str] = Field(
        default_factory=lambda: [
            "localhost",
            "127.0.0.1",
            "ai-service",
            "medmatch-ai",
            "frontend",
            "nginx",
        ]
    )

    REQUEST_TIMEOUT_SECONDS: int = 120
    WORKER_TIMEOUT: int = 120

    API_PREFIX: str = "/api"
    API_TITLE: str = "MedMatch AI Service"
    API_DESCRIPTION: str = (
        "AI-powered Clinical Trial Matching Platform"
    )

    TIMEZONE: str = "UTC"

    ALLOWED_UPLOAD_EXTENSIONS: list[str] = Field(
        default_factory=lambda: [
            ".pdf"
        ]
    )

    ENABLE_CACHE: bool = True


    # ==========================================================
    # Database
    # ==========================================================
    DATABASE_URL: str

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30


    # ==========================================================
    # Uploads
    # ==========================================================
    UPLOAD_DIR: str = "uploads"

    MAX_UPLOAD_SIZE_MB: int = 20


    # ==========================================================
    # JWT Security
    # ==========================================================
    JWT_PUBLIC_KEY_PATH: str = Field(
        default="keys/public_key.pem"
    )

    JWT_ALGORITHM: str = "RS256"


    # ==========================================================
    # Gemini / LLM
    # ==========================================================
    GOOGLE_API_KEY: str | None = None

    LLM_MODEL: str = "gemini-2.5-flash"

    LLM_TIMEOUT_SECONDS: int = 60

    LLM_MAX_RETRIES: int = 3


    # ==========================================================
    # Embeddings / Retrieval
    # ==========================================================
    TOP_K_RESULTS: int = 5

    SIMILARITY_THRESHOLD: float = Field(
        default=0.75,
        ge=0.0,
        le=2.0,
        description=(
            "Maximum cosine distance accepted "
            "for vector similarity search."
        ),
    )


    # ==========================================================
    # Redis
    # ==========================================================
    REDIS_URL: str = "redis://redis:6379/0"

    REDIS_HOST: str = "redis"

    REDIS_PORT: int = 6379

    REDIS_DB: int = 0

    REDIS_PASSWORD: str | None = None


    # ==========================================================
    # Celery
    # ==========================================================
    CELERY_BROKER_URL: str = "redis://redis:6379/0"

    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    CELERY_CONCURRENCY: int = 2

    CELERY_TASK_TIME_LIMIT: int = 300


    # ==========================================================
    # Cache
    # ==========================================================
    EMBEDDING_CACHE_TTL: int = (
        60 * 60 * 24 * 7
    )

    RETRIEVAL_CACHE_TTL: int = (
        60 * 60
    )

    LLM_CACHE_TTL: int = (
        60 * 30
    )


    # ==========================================================
    # Logging
    # ==========================================================
    LOG_LEVEL: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"


    # ==========================================================
    # API / Swagger
    # ==========================================================
    ENABLE_DOCS: bool = True

    ENABLE_OPENAPI: bool = True

    # ==========================================================
    # Pydantic Settings Configuration
    # ==========================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()