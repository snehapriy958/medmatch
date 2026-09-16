from http import HTTPStatus


class APIException(Exception):
    """
    Base exception for all application-specific errors.
    """

    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
    ) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BadRequestException(APIException):
    """
    Raised when a request cannot be processed because the
    supplied input is invalid for the requested operation.
    """

    def __init__(
        self,
        message: str = "Bad request.",
    ) -> None:
        super().__init__(
            message,
            HTTPStatus.BAD_REQUEST,
        )


class UnauthorizedException(APIException):
    """
    Raised when authentication is required.
    """

    def __init__(
        self,
        message: str = "Authentication required.",
    ) -> None:
        super().__init__(
            message,
            HTTPStatus.UNAUTHORIZED,
        )


class ForbiddenException(APIException):
    """
    Raised when an authenticated user does not have permission
    to perform the requested operation.
    """

    def __init__(
        self,
        message: str = "Access denied.",
    ) -> None:
        super().__init__(
            message,
            HTTPStatus.FORBIDDEN,
        )


class NotFoundException(APIException):
    """
    Raised when a requested resource does not exist.
    """

    def __init__(
        self,
        message: str = "Resource not found.",
    ) -> None:
        super().__init__(
            message,
            HTTPStatus.NOT_FOUND,
        )


class ConflictException(APIException):
    """
    Raised when a requested operation conflicts with the
    current resource state.
    """

    def __init__(
        self,
        message: str = "Resource already exists.",
    ) -> None:
        super().__init__(
            message,
            HTTPStatus.CONFLICT,
        )


class DatabaseException(APIException):
    """
    Raised when a database operation cannot be completed.
    """

    def __init__(
        self,
        message: str = "Database operation failed.",
    ) -> None:
        super().__init__(
            message,
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class ExternalServiceException(APIException):
    """
    Raised when a required external dependency is temporarily
    unavailable or cannot successfully process a request.

    Examples include LLM providers and other upstream services.
    """

    def __init__(
        self,
        message: str = "External service unavailable.",
    ) -> None:
        super().__init__(
            message,
            HTTPStatus.SERVICE_UNAVAILABLE,
        )