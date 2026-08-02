"""
Common API response schemas.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API success response.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    success: bool = True

    message: str

    data: T


class Pagination(BaseModel):
    """
    Pagination metadata.
    """

    page: int

    page_size: int

    total_records: int

    total_pages: int


class PagedResponse(BaseModel, Generic[T]):
    """
    Standard paginated response.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    success: bool = True

    message: str

    data: list[T]

    pagination: Pagination