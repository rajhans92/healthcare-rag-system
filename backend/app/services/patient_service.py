"""
Patient service.

Contains all business logic related to patients.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.exceptions import ResourceNotFoundException
from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import (
    PatientResponse,
    UpdatePatientRequest,
)


class PatientService:
    """
    Patient service.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.patient_repository = PatientRepository(session)

    async def get_my_profile(
        self,
        user_id: UUID,
    ) -> PatientResponse:
        """
        Get logged-in patient's profile.
        """

        patient = await self.patient_repository.get_by_user_id(
            user_id
        )

        if patient is None:
            raise ResourceNotFoundException("Patient")

        return PatientResponse.model_validate(patient)

    async def get_patient_by_id(
        self,
        patient_id: UUID,
    ) -> PatientResponse:
        """
        Get patient by patient ID.
        """

        patient = await self.patient_repository.get_by_id(
            patient_id
        )

        if patient is None:
            raise ResourceNotFoundException("Patient")

        return PatientResponse.model_validate(patient)

    async def update_profile(
        self,
        user_id: UUID,
        request: UpdatePatientRequest,
    ) -> PatientResponse:
        """
        Update patient profile.
        """

        patient = await self.patient_repository.get_by_user_id(
            user_id
        )

        if patient is None:
            raise ResourceNotFoundException("Patient")

        update_data = request.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        for field, value in update_data.items():
            setattr(patient, field, value)

        await self.patient_repository.update_patient(patient)

        await self.session.commit()

        await self.session.refresh(patient)

        return PatientResponse.model_validate(patient)

    async def delete_patient(
        self,
        patient_id: UUID,
    ) -> None:
        """
        Soft delete patient.
        """

        patient = await self.patient_repository.get_by_id(
            patient_id
        )

        if patient is None:
            raise ResourceNotFoundException("Patient")

        patient.is_active = False

        await self.patient_repository.update_patient(patient)

        await self.session.commit()