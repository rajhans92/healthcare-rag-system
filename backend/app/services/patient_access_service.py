"""Patient access service for doctor-patient authorization."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.initializer import initialize_database  # noqa: F401
from app.models.doctor import Doctor  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.patient_access import AccessStatus, PatientAccess
from app.models.user import User  # noqa: F401
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.patient_access_repository import PatientAccessRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_access import PatientAccessResponse


class PatientAccessService:
    """Handle doctor-patient access relationships."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = PatientAccessRepository(session)
        self.patient_repository = PatientRepository(session)
        self.doctor_repository = DoctorRepository(session)

    async def request_access(
        self,
        patient_id: UUID,
        doctor_id: UUID,
        *,
        requester_id: UUID | None = None,
        requester_role: str | None = None,
        expires_days: int = 30,
    ) -> PatientAccessResponse:
        """Create a patient access request for a doctor."""
        patient = await self.patient_repository.get_by_id(patient_id)
        if patient is None:
            raise ValueError("Patient not found.")

        doctor = await self.doctor_repository.get_by_id(doctor_id)
        if doctor is None:
            raise ValueError("Doctor not found.")

        if requester_id is not None and requester_role is not None:
            if requester_role == "PATIENT" and patient.user_id != requester_id:
                raise PermissionError("You are not allowed to request access for this patient.")
            if requester_role == "DOCTOR" and doctor.user_id != requester_id:
                raise PermissionError("You are not allowed to request access on behalf of this doctor.")

        existing = await self.repository.get_by_patient_and_doctor(patient_id, doctor_id)
        for access in existing:
            if access.status == AccessStatus.APPROVED and access.expires_at > datetime.now(timezone.utc):
                return PatientAccessResponse.model_validate(access)

        otp = str(secrets.randbelow(900000) + 100000)
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

        access = PatientAccess(
            patient_id=patient_id,
            doctor_id=doctor_id,
            otp=otp,
            status=AccessStatus.PENDING,
            expires_at=expires_at,
        )
        if access.id is None:
            access.id = uuid4()
        if access.created_at is None:
            access.created_at = datetime.now(timezone.utc)
        if access.updated_at is None:
            access.updated_at = access.created_at

        await self.repository.create_access(access)
        await self.session.commit()
        await self.session.refresh(access)

        return PatientAccessResponse.model_validate(access)

    async def update_access_status(
        self,
        access_id: UUID,
        *,
        status: AccessStatus,
        remarks: str | None = None,
        reviewer_id: UUID | None = None,
        reviewer_role: str | None = None,
    ) -> PatientAccessResponse:
        """Approve or reject a patient access request."""
        access = await self.repository.get_by_id(access_id)
        if access is None:
            raise ValueError("Access record not found.")

        if reviewer_id is not None and reviewer_role is not None:
            if reviewer_role == "PATIENT" and access.patient_id is not None:
                patient = await self.patient_repository.get_by_id(access.patient_id)
                if patient is None or patient.user_id != reviewer_id:
                    raise PermissionError("Only the patient can update their own access request.")
            if reviewer_role == "DOCTOR":
                doctor = await self.doctor_repository.get_by_user_id(reviewer_id)
                if doctor is None or doctor.id != access.doctor_id:
                    raise PermissionError("Doctor can only update their own access records.")

        access.status = status
        access.remarks = remarks
        if status == AccessStatus.APPROVED:
            access.approved_at = datetime.now(timezone.utc)
        else:
            access.approved_at = None
        if access.id is None:
            access.id = uuid4()
        if access.created_at is None:
            access.created_at = datetime.now(timezone.utc)
        if access.updated_at is None:
            access.updated_at = access.created_at

        await self.repository.update_access(access)
        await self.session.commit()
        await self.session.refresh(access)

        return PatientAccessResponse.model_validate(access)

    async def is_doctor_authorized_for_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
    ) -> bool:
        """Return whether the doctor currently has approved access to the patient."""
        access = await self.repository.get_active_access(patient_id, doctor_id)
        return access is not None

    async def list_patient_accesses(
        self,
        patient_id: UUID,
    ) -> list[PatientAccessResponse]:
        accesses = await self.repository.list_for_patient(patient_id)
        return [PatientAccessResponse.model_validate(item) for item in accesses]

    async def list_doctor_accesses(
        self,
        doctor_id: UUID,
    ) -> list[PatientAccessResponse]:
        accesses = await self.repository.list_for_doctor(doctor_id)
        return [PatientAccessResponse.model_validate(item) for item in accesses]
