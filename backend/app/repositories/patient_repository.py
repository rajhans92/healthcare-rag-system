"""
Patient repository.

Responsible for all database operations related to Patient.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.repositories.base_repository import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    """
    Repository for Patient entity.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Patient, session)

    async def create_patient(
        self,
        patient: Patient,
    ) -> Patient:
        """
        Create a new patient.
        """
        return await self.create(patient)

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> Patient | None:
        """
        Get patient by user ID.
        """

        result = await self.session.execute(
            select(Patient).where(
                Patient.user_id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def exists_by_user_id(
        self,
        user_id: UUID,
    ) -> bool:
        """
        Check if patient exists for a user.
        """

        result = await self.session.execute(
            select(Patient.id).where(
                Patient.user_id == user_id
            )
        )

        return result.scalar_one_or_none() is not None

    async def update_patient(
        self,
        patient: Patient,
    ) -> Patient:
        """
        Update patient details.
        """

        await self.session.flush()
        await self.session.refresh(patient)

        return patient
    
    async def create_for_user(
        self,
        user_id: UUID,
    ) -> Patient:

        patient = Patient(
            user_id=user_id,
        )

        self.session.add(patient)

        await self.session.flush()

        return patient