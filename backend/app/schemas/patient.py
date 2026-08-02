"""
Patient request and response schemas.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PatientResponse(BaseModel):
    """
    Patient profile response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    user_id: UUID

    date_of_birth: date | None = None

    gender: str | None = None

    blood_group: str | None = None

    height_cm: float | None = None

    weight_kg: float | None = None

    emergency_contact_name: str | None = None

    emergency_contact_phone: str | None = None

    address: str | None = None

    city: str | None = None

    state: str | None = None

    country: str | None = None

    postal_code: str | None = None

    created_at: datetime

    updated_at: datetime


class UpdatePatientRequest(BaseModel):
    """
    Update patient profile request.
    """

    date_of_birth: date | None = None

    gender: str | None = Field(
        default=None,
        max_length=20,
    )

    blood_group: str | None = Field(
        default=None,
        max_length=5,
    )

    height_cm: float | None = Field(
        default=None,
        ge=30,
        le=300,
    )

    weight_kg: float | None = Field(
        default=None,
        ge=1,
        le=500,
    )

    emergency_contact_name: str | None = Field(
        default=None,
        max_length=100,
    )

    emergency_contact_phone: str | None = Field(
        default=None,
        max_length=20,
    )

    address: str | None = None

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    country: str | None = Field(
        default=None,
        max_length=100,
    )

    postal_code: str | None = Field(
        default=None,
        max_length=20,
    )


class PatientSummaryResponse(BaseModel):
    """
    Patient summary response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    user_id: UUID

    gender: str | None = None

    blood_group: str | None = None

    city: str | None = None

    state: str | None = None