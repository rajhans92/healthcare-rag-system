"""
Error response schemas.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """
    Error details returned to API clients.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    code: str = Field(
        ...,
        description="Application specific error code.",
        examples=["INVALID_CREDENTIALS"],
    )

    message: str = Field(
        ...,
        description="Human readable error message.",
        examples=["Invalid email or password."],
    )

    details: Any | None = Field(
        default=None,
        description="Additional debugging or validation information.",
    )


class ErrorResponse(BaseModel):
    """
    Standard error response.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    success: bool = False

    error: ErrorDetail

    path: str

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
    )

    request_id: str | None = None