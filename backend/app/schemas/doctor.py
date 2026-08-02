"""
Doctor request and response schemas.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DoctorResponse(BaseModel):
    """
    Doctor profile response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    user_id: UUID

    registration_number: str | None = None

    specialization: str | None = None

    qualification: str | None = None

    experience_years: int | None = None

    hospital_name: str | None = None

    department: str | None = None

    consultation_fee: Decimal | None = None

    bio: str | None = None

    created_at: datetime

    updated_at: datetime


class UpdateDoctorRequest(BaseModel):
    """
    Update doctor profile request.
    """

    registration_number: str | None = Field(
        default=None,
        max_length=50,
    )

    specialization: str | None = Field(
        default=None,
        max_length=100,
    )

    qualification: str | None = Field(
        default=None,
        max_length=255,
    )

    experience_years: int | None = Field(
        default=None,
        ge=0,
        le=70,
    )

    hospital_name: str | None = Field(
        default=None,
        max_length=255,
    )

    department: str | None = Field(
        default=None,
        max_length=100,
    )

    consultation_fee: Decimal | None = Field(
        default=None,
        ge=0,
    )

    bio: str | None = Field(
        default=None,
        max_length=1000,
    )


class DoctorSummaryResponse(BaseModel):
    """
    Doctor summary response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    user_id: UUID

    specialization: str | None = None

    hospital_name: str | None = None

    experience_years: int | None = None