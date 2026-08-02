"""
Global exception handlers.
"""

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.exceptions import AppException

def build_error_response(
    *,
    request: Request,
    status_code: int,
    error_code: str,
    message: str,
    details: dict | list | None = None,
) -> JSONResponse:
    """
    Build a standard error response.
    """

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details,
            },
            "path": request.url.path,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    """
    Handle business exceptions.
    """

    return build_error_response(
        request=request,
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):

    errors = []

    for error in exc.errors():

        field = ".".join(
            str(item)
            for item in error["loc"]
            if item != "body"
        )

        errors.append(
            {
                "field": field,
                "message": error["msg"],
            }
        )

    return build_error_response(
        request=request,
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Validation failed.",
        details=errors,
    )

async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    """
    Handle FastAPI HTTP exceptions.
    """

    return build_error_response(
        request=request,
        status_code=exc.status_code,
        error_code="HTTP_ERROR",
        message=str(exc.detail),
    )

async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    """
    Handle unexpected exceptions.
    """

    return build_error_response(
        request=request,
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred.",
    )

def register_exception_handlers(
    app: FastAPI,
) -> None:
    """
    Register all exception handlers.
    """

    app.add_exception_handler(
        AppException,
        app_exception_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    app.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )

    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

