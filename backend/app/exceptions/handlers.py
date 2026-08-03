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
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                success=False,
                error={
                    "code": ErrorCode.VALIDATION_ERROR.value,
                    "message": "Validation failed.",
                    "details": exc.errors(),
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