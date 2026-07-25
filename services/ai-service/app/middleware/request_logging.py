import logging
import time
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("medmatch")


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next: Any,
    ):

        start = time.perf_counter()

        status_code: int | str = "ERROR"

        try:

            response = await call_next(request)

            status_code = response.status_code

            return response

        except Exception:

            logger.exception(
                "[%s] Unhandled exception while processing %s %s",
                getattr(request.state, "request_id", "-"),
                request.method,
                request.url.path,
            )

            raise

        finally:

            duration = (time.perf_counter() - start) * 1000

            logger.info(
                "[%s] %s %s | %s | %.2f ms | %s",
                getattr(request.state, "request_id", "-"),
                request.method,
                request.url.path,
                status_code,
                duration,
                request.client.host if request.client else "unknown",
            )