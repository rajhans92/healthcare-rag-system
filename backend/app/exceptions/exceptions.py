"""
Custom application exceptions.

All business exceptions should inherit from AppException.
"""

from typing import Any


class AppException(Exception):
    """
    Base application exception.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "APPLICATION_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

        super().__init__(message)

class InvalidCredentialsException(AppException):
    """
    Invalid email or password.
    """

    def __init__(self):
        super().__init__(
            message="Invalid email or password.",
            status_code=401,
            error_code="INVALID_CREDENTIALS",
        )


class UserAlreadyExistsException(AppException):
    """
    User already exists.
    """

    def __init__(self):
        super().__init__(
            message="User already exists.",
            status_code=409,
            error_code="USER_ALREADY_EXISTS",
        )


class UserNotFoundException(AppException):
    """
    User not found.
    """

    def __init__(self):
        super().__init__(
            message="User not found.",
            status_code=404,
            error_code="USER_NOT_FOUND",
        )


class InactiveUserException(AppException):
    """
    User account is inactive.
    """

    def __init__(self):
        super().__init__(
            message="User account is inactive.",
            status_code=403,
            error_code="USER_INACTIVE",
        )

class ForbiddenException(AppException):
    """
    Access denied.
    """

    def __init__(self):
        super().__init__(
            message="Access denied.",
            status_code=403,
            error_code="FORBIDDEN",
        )


class UnauthorizedException(AppException):
    """
    Authentication required.
    """

    def __init__(self):
        super().__init__(
            message="Authentication required.",
            status_code=401,
            error_code="UNAUTHORIZED",
        )

class ResourceNotFoundException(AppException):
    """
    Generic resource not found.
    """

    def __init__(
        self,
        resource_name: str,
    ):
        super().__init__(
            message=f"{resource_name} not found.",
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
        )

class ValidationException(AppException):
    """
    Business validation failed.
    """

    def __init__(
        self,
        message: str,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
        )

