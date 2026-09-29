import contextvars
import logging
import re
from typing import Any
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for request correlation ID
_REQUEST_ID_CTX: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)

# Pattern to validate incoming X-Request-ID (alphanumeric, hyphens, underscores, 1-64 chars)
_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


def get_current_request_id() -> str | None:
    """Return the current correlation request ID from contextvars, or None."""
    return _REQUEST_ID_CTX.get()


def set_current_request_id(request_id: str | None) -> contextvars.Token:
    """Set the correlation request ID in contextvars and return the token."""
    return _REQUEST_ID_CTX.set(request_id)


def reset_current_request_id(token: contextvars.Token) -> None:
    """Reset the contextvar to its previous state using the token."""
    _REQUEST_ID_CTX.reset(token)


class RequestIDLogFilter(logging.Filter):
    """Logging filter that enriches every LogRecord with request_id from contextvars."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_current_request_id() or "-"
        return True


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Any,
    ):
        incoming_id = request.headers.get("X-Request-ID")
        if incoming_id and _REQUEST_ID_REGEX.match(incoming_id.strip()):
            request_id = incoming_id.strip()
        else:
            request_id = str(uuid4())

        request.state.request_id = request_id
        token = set_current_request_id(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            reset_current_request_id(token)