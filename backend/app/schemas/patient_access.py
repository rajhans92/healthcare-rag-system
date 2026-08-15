"""
Patient access request and response schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.patient_access import AccessStatus


class PatientAccessRequest(BaseModel):
    """Request a patient-doctor access grant."""

    patient_id: UUID
    doctor_id: UUID
    expires_days: int = Field(default=30, ge=1, le=365)


class PatientAccessDecisionRequest(BaseModel):
    """Approve or reject a patient access request."""

    status: AccessStatus
    remarks: str | None = Field(default=None, max_length=1000)


class PatientAccessResponse(BaseModel):
    """Patient access response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    doctor_id: UUID
    otp: str
    status: AccessStatus
    expires_at: datetime
    approved_at: datetime | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime
