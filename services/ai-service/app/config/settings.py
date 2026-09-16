from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Configuration is validated during application startup so invalid or
    unsafe production settings fail fast instead of causing runtime errors.
    """

    # ==========================================================
    # Application
    # ==========================================================

    APP_NAME: str = Field(
        default="MedMatch AI Service",
        min_length=1,
    )

    APP_VERSION: str = Field(
        default="1.0.0",
        min_length=1,
    )

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
            "http://localhost:5174",
        ]
    )

    TRUSTED_HOSTS: list[str] = Field(
        default_factory=lambda: [
            "localhost",
            "127.0.0.1",
            "testserver",
            "ai-service",
        ]
    )

    REQUEST_TIMEOUT_SECONDS: int = Field(
        default=120,
        ge=1,
        le=600,
    )

    WORKER_TIMEOUT: int = Field(
        default=120,
        ge=1,
        le=3600,
    )

    API_PREFIX: str = "/api"

    API_TITLE: str = "MedMatch AI Service"

    API_DESCRIPTION: str = (
        "AI-powered Clinical Trial Matching Platform"
    )

    TIMEZONE: str = "UTC"

    ALLOWED_UPLOAD_EXTENSIONS: list[str] = Field(
        default_factory=lambda: [
            ".pdf",
        ]
    )

    ENABLE_CACHE: bool = True

    # ==========================================================
    # Rate Limiting
    # ==========================================================

    SEARCH_RATE_LIMIT: str = Field(
        default="30/minute",
        min_length=1,
        description="API rate limit for semantic search.",
    )

    EVALUATE_RATE_LIMIT: str = Field(
        default="20/minute",
        min_length=1,
        description="API rate limit for eligibility evaluation.",
    )

    # ==========================================================
    # Database
    # ==========================================================

    DATABASE_URL: str = Field(
        min_length=1,
    )

    DB_POOL_SIZE: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    DB_MAX_OVERFLOW: int = Field(
        default=20,
        ge=0,
        le=200,
    )

    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        le=300,
    )

    # ==========================================================
    # Uploads
    # ==========================================================

    UPLOAD_DIR: str = Field(
        default="uploads",
        min_length=1,
    )

    MAX_UPLOAD_SIZE_MB: int = Field(
        default=20,
        ge=1,
        le=500,
    )

    # ==========================================================
    # JWT Security
    # ==========================================================

    JWT_PUBLIC_KEY_PATH: str = Field(
        default="keys/public_key.pem",
        min_length=1,
    )

    JWT_ALGORITHM: Literal[
        "RS256",
    ] = "RS256"

    # ==========================================================
    # Gemini / LLM
    # ==========================================================

    GOOGLE_API_KEY: str | None = Field(
        default=None,
        min_length=1,
    )

    LLM_MODEL: str = Field(
        default="gemini-2.5-flash",
        min_length=1,
    )

    LLM_TIMEOUT_SECONDS: int = Field(
        default=60,
        ge=1,
        le=300,
    )

    LLM_MAX_RETRIES: int = Field(
        default=3,
        ge=1,
        le=10,
    )

    # ==========================================================
    # Embeddings / Retrieval
    # ==========================================================

    TOP_K_RESULTS: int = Field(
        default=5,
        ge=1,
        le=100,
    )

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

    REDIS_URL: str = Field(
        default="redis://redis:6379/0",
        min_length=1,
    )

    REDIS_HOST: str = Field(
        default="redis",
        min_length=1,
    )

    REDIS_PORT: int = Field(
        default=6379,
        ge=1,
        le=65535,
    )

    REDIS_DB: int = Field(
        default=0,
        ge=0,
        le=15,
    )

    REDIS_PASSWORD: str | None = None

    # ==========================================================
    # Celery
    # ==========================================================

    CELERY_BROKER_URL: str = Field(
        default="redis://redis:6379/0",
        min_length=1,
    )

    CELERY_RESULT_BACKEND: str = Field(
        default="redis://redis:6379/1",
        min_length=1,
    )

    CELERY_CONCURRENCY: int = Field(
        default=2,
        ge=1,
        le=32,
    )

    CELERY_TASK_TIME_LIMIT: int = Field(
        default=300,
        ge=1,
        le=3600,
    )

    # ==========================================================
    # Cache
    # ==========================================================

    EMBEDDING_CACHE_TTL: int = Field(
        default=60 * 60 * 24 * 7,
        ge=0,
    )

    RETRIEVAL_CACHE_TTL: int = Field(
        default=60 * 60,
        ge=0,
    )

    LLM_CACHE_TTL: int = Field(
        default=60 * 30,
        ge=0,
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

    # ==========================================================
    # Validators
    # ==========================================================

    @field_validator(
        "ALLOWED_UPLOAD_EXTENSIONS",
    )
    @classmethod
    def validate_upload_extensions(
        cls,
        extensions: list[str],
    ) -> list[str]:
        """
        Ensure every configured upload extension starts with a dot
        and is normalized to lowercase.
        """

        normalized_extensions = [
            extension.strip().lower()
            for extension in extensions
            if extension.strip()
        ]

        if not normalized_extensions:
            raise ValueError(
                "At least one upload extension must be configured."
            )

        invalid_extensions = [
            extension
            for extension in normalized_extensions
            if not extension.startswith(".")
        ]

        if invalid_extensions:
            raise ValueError(
                "Upload extensions must start with '.'."
            )

        return normalized_extensions

    @field_validator(
        "ALLOWED_ORIGINS",
    )
    @classmethod
    def validate_allowed_origins(
        cls,
        origins: list[str],
    ) -> list[str]:
        """
        Normalize configured CORS origins and reject empty values.
        """

        normalized_origins = [
            origin.strip().rstrip("/")
            for origin in origins
            if origin.strip()
        ]

        if not normalized_origins:
            raise ValueError(
                "At least one allowed origin must be configured."
            )

        return normalized_origins

    @field_validator(
        "TRUSTED_HOSTS",
    )
    @classmethod
    def validate_trusted_hosts(
        cls,
        hosts: list[str],
    ) -> list[str]:
        """
        Normalize configured trusted hosts.
        """

        normalized_hosts = [
            host.strip()
            for host in hosts
            if host.strip()
        ]

        if not normalized_hosts:
            raise ValueError(
                "At least one trusted host must be configured."
            )

        return normalized_hosts

    @model_validator(
        mode="after",
    )
    def validate_production_configuration(
        self,
    ) -> "Settings":
        """
        Apply additional safety checks when running in production.
        """

        if self.ENVIRONMENT == "production":

            if "*" in self.TRUSTED_HOSTS:
                raise ValueError(
                    "TRUSTED_HOSTS must not contain '*' "
                    "in production."
                )

            if not self.GOOGLE_API_KEY:
                raise ValueError(
                    "GOOGLE_API_KEY must be configured "
                    "in production."
                )

            if self.LOG_LEVEL == "DEBUG":
                raise ValueError(
                    "LOG_LEVEL must not be DEBUG "
                    "in production."
                )

        return self

settings = Settings()