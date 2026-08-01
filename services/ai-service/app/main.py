from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from prometheus_fastapi_instrumentator import Instrumentator

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import api_router
from app.config.rate_limit import limiter
from app.config.settings import settings
from app.db.init_db import init_db

from app.exceptions.api_exceptions import APIException
from app.exceptions.handlers import (
    api_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)

from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware


logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "[%(name)s] | "
        "%(message)s"
    ),
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:

    try:
        if settings.ENVIRONMENT in ("development", "docker"):
            logger.info(
                "Initializing database..."
            )

            init_db()

            logger.info(
                "Database initialization completed."
            )

        else:
            logger.info(
                "Automatic database initialization is disabled for environment: %s",
                settings.ENVIRONMENT,
            )

        yield

    except Exception:
        logger.exception(
            "Application startup failed."
        )
        raise


app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url=(
        "/docs"
        if settings.ENABLE_DOCS
        else None
    ),
    openapi_url=(
        "/openapi.json"
        if settings.ENABLE_OPENAPI
        else None
    ),
    lifespan=lifespan,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.TRUSTED_HOSTS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SlowAPIMiddleware)


app.add_exception_handler(
    APIException,
    api_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    SQLAlchemyError,
    database_exception_handler,
)

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_exception_handler(
    Exception,
    generic_exception_handler,
)


app.include_router(api_router)
Instrumentator().instrument(app).expose(app)