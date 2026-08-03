"""
Application custom exceptions.
"""

from app.exceptions.error_codes import ErrorCode


class AppException(Exception):
    """
    Base application exception.
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        status_code: int,
        details: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

        super().__init__(message)


class ValidationException(AppException):
    """
    Request validation failed.
    """

    def __init__(
        self,
        message: str = "Validation failed.",
        details: dict | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details,
        )


class AuthenticationException(AppException):
    """
    Authentication failed.
    """

    def __init__(
        self,
        message: str = "Authentication failed.",
        code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=401,
        )


class AuthorizationException(AppException):
    """
    User is not authorized.
    """

    def __init__(
        self,
        message: str = "You are not authorized to perform this action.",
    ):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            status_code=403,
        )


class ResourceNotFoundException(AppException):
    """
    Resource not found.
    """

    def __init__(
        self,
        resource_name: str,
    ):
        super().__init__(
            message=f"{resource_name} not found.",
            code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
        )


class ConflictException(AppException):
    """
    Duplicate resource.
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=409,
        )


class DatabaseException(AppException):
    """
    Database operation failed.
    """

    def __init__(
        self,
        message: str = "Database operation failed.",
    ):
        super().__init__(
            message=message,
            code=ErrorCode.DATABASE_ERROR,
            status_code=500,
        )


class InternalServerException(AppException):
    """
    Unexpected application error.
    """

    def __init__(
        self,
        message: str = "Internal server error.",
    ):
        super().__init__(
            message=message,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=500,
        )