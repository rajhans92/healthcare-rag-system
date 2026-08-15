"""
Global exception handlers.
"""

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.exceptions.error_codes import ErrorCode
from app.exceptions.exceptions import (
    AppException,
    DatabaseException,
)
from app.schemas.error import (
    ErrorDetail,
    ErrorResponse,
)

logger = logging.getLogger(__name__)


def _sanitize_validation_errors(errors: list[dict]) -> list[dict]:
    """Convert any non-serializable values in the validation error dicts to strings.

    Pydantic's error 'ctx' may include exception objects (e.g. ValueError) which are
    not JSON serializable. This helper replaces such values with their string
    representation to ensure the error response can be serialized safely.
    """
    sanitized: list[dict] = []
    for err in errors:
        new_err: dict = {}
        for k, v in err.items():
            if k == "ctx" and isinstance(v, dict):
                new_ctx: dict = {}
                for ck, cv in v.items():
                    if isinstance(cv, (str, int, float, bool)) or cv is None:
                        new_ctx[ck] = cv
                    else:
                        try:
                            new_ctx[ck] = str(cv)
                        except Exception:
                            new_ctx[ck] = repr(cv)
                new_err["ctx"] = new_ctx
            else:
                # For other fields, keep primitives, else stringify
                if isinstance(v, (str, int, float, bool)) or v is None:
                    new_err[k] = v
                else:
                    try:
                        new_err[k] = v
                    except Exception:
                        new_err[k] = str(v)
        sanitized.append(new_err)
    return sanitized


def register_exception_handlers(
    app: FastAPI,
) -> None:
    """
    Register all global exception handlers.
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                error={
                    "code": exc.code.value,
                    "message": exc.message,
                    "details": exc.details,
                },
                path=request.url.path,
            ).model_dump(mode="json"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        # Extract validation errors and sanitize any non-serializable ctx values
        errors = exc.errors()
        sanitized = _sanitize_validation_errors(errors)

        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                success=False,
                error={
                    "code": ErrorCode.VALIDATION_ERROR.value,
                    "message": "Validation failed.",
                    "details": sanitized,
                },
                path=request.url.path,
            ).model_dump(mode="json"),
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(
        request: Request,
        exc: SQLAlchemyError,
    ):
        logger.exception(
            "Database Exception: %s",
            str(exc),
        )

        database_exception = DatabaseException()

        return JSONResponse(
            status_code=database_exception.status_code,
            content=ErrorResponse(
                success=False,
                error={
                    "code": database_exception.code.value,
                    "message": database_exception.message,
                    "details": None,
                },
                path=request.url.path,
            ).model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ):
        logger.exception(
            "Unhandled Exception: %s",
            str(exc),
        )

        if settings.DEBUG:
            traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                success=False,
                error={
                    "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                    "message": "An unexpected error occurred.",
                    "details": str(exc) if settings.DEBUG else None,
                },
                path=request.url.path,
            ).model_dump(mode="json"),
        )