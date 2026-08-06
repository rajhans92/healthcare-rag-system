"""
Encounter request and response schemas.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.encounter import (
    EncounterStatus,
    EncounterType,
)


# ==========================================================
# Create Encounter
# ==========================================================

class CreateEncounterRequest(BaseModel):
    """
    Request model for creating a new encounter.
    """

    patient_id: UUID

    encounter_type: EncounterType

    chief_complaint: str = Field(
        min_length=3,
        max_length=1000,
    )

    encounter_date: datetime


# ==========================================================
# Update Encounter
# ==========================================================

class UpdateEncounterRequest(BaseModel):
    """
    Request model for updating encounter.
    """

    encounter_type: EncounterType | None = None

    chief_complaint: str | None = Field(
        default=None,
        min_length=3,
        max_length=1000,
    )

    encounter_date: datetime | None = None

    status: EncounterStatus | None = None

    notes: str | None = None


# ==========================================================
# Encounter Summary
# ==========================================================

class EncounterSummaryResponse(BaseModel):
    """
    Lightweight encounter response used in listing.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    encounter_number: str

    encounter_type: EncounterType

    encounter_date: datetime

    status: EncounterStatus

    chief_complaint: str


# ==========================================================
# Encounter Details
# ==========================================================

class EncounterResponse(BaseModel):
    """
    Detailed encounter response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    encounter_number: str

    patient_id: UUID

    doctor_id: UUID

    encounter_type: EncounterType

    encounter_date: datetime

    chief_complaint: str

    status: EncounterStatus

    notes: str | None

    created_at: datetime

    updated_at: datetime


# ==========================================================
# Encounter List Response
# ==========================================================

class EncounterListResponse(BaseModel):
    """
    Paginated encounter list.
    """

    total: int

    page: int

    page_size: int

    items: list[EncounterSummaryResponse]