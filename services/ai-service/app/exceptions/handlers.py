from http import HTTPStatus
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.api_exceptions import APIException
from app.exceptions.responses import ErrorResponse

logger = logging.getLogger(__name__)


async def api_exception_handler(
    request: Request,
    exc: APIException,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)

    response = ErrorResponse(
        error=exc.__class__.__name__,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
        request_id=request_id,
    )

    json_response = JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
    )

    if request_id:
        json_response.headers["X-Request-ID"] = request_id

    return json_response


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)

    response = ErrorResponse(
        error="ValidationError",
        message="Request validation failed.",
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        path=request.url.path,
        request_id=request_id,
        details=exc.errors(),
    )

    json_response = JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content=response.model_dump(mode="json"),
    )

    if request_id:
        json_response.headers["X-Request-ID"] = request_id

    return json_response


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    logger.exception(
        "Database error while processing %s %s",
        request.method,
        request.url.path,
    )

    request_id = getattr(request.state, "request_id", None)

    response = ErrorResponse(
        error="DatabaseError",
        message="A database error occurred.",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        path=request.url.path,
        request_id=request_id,
    )

    json_response = JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode="json"),
    )

    if request_id:
        json_response.headers["X-Request-ID"] = request_id

    return json_response


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled exception while processing %s %s",
        request.method,
        request.url.path,
    )

    request_id = getattr(request.state, "request_id", None)

    response = ErrorResponse(
        error="InternalServerError",
        message="An unexpected error occurred.",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        path=request.url.path,
        request_id=request_id,
    )

    json_response = JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode="json"),
    )

    if request_id:
        json_response.headers["X-Request-ID"] = request_id

    return json_response