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
    def __init__(self, message: str = "Bad request.") -> None:
        super().__init__(message, HTTPStatus.BAD_REQUEST)


class UnauthorizedException(APIException):
    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(message, HTTPStatus.UNAUTHORIZED)


class ForbiddenException(APIException):
    def __init__(self, message: str = "Access denied.") -> None:
        super().__init__(message, HTTPStatus.FORBIDDEN)


class NotFoundException(APIException):
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(message, HTTPStatus.NOT_FOUND)


class ConflictException(APIException):
    def __init__(self, message: str = "Resource already exists.") -> None:
        super().__init__(message, HTTPStatus.CONFLICT)


class DatabaseException(APIException):
    def __init__(self, message: str = "Database operation failed.") -> None:
        super().__init__(message, HTTPStatus.INTERNAL_SERVER_ERROR)


class ExternalServiceException(APIException):
    def __init__(self, message: str = "External service unavailable.") -> None:
        super().__init__(message, HTTPStatus.BAD_GATEWAY)