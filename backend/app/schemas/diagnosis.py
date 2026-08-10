"""
Diagnosis request and response schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.diagnosis import Severity


class CreateDiagnosisRequest(BaseModel):
    """
    Request for creating a diagnosis.
    """

    diagnosis_code: str | None = Field(
        default=None,
        max_length=20,
        description="ICD-10 or other clinical diagnosis code.",
    )

    diagnosis_name: str = Field(
        min_length=2,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    severity: Severity | None = None

    is_primary: bool = False


class UpdateDiagnosisRequest(BaseModel):
    """
    Request for updating a diagnosis.
    """

    diagnosis_code: str | None = Field(
        default=None,
        max_length=20,
    )

    diagnosis_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    severity: Severity | None = None

    is_primary: bool | None = None


class DiagnosisResponse(BaseModel):
    """
    Diagnosis response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    encounter_id: UUID

    diagnosis_code: str | None

    diagnosis_name: str

    description: str | None

    severity: Severity | None

    is_primary: bool

    created_by: UUID

    created_at: datetime

    updated_at: datetime