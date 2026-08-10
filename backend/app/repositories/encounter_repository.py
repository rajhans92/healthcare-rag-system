"""
Repository for Encounter entity.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.encounter import Encounter
from app.repositories.base_repository import BaseRepository


class EncounterRepository(BaseRepository[Encounter]):
    """
    Repository for Encounter database operations.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        super().__init__(Encounter, session)

    async def create_encounter(
        self,
        encounter: Encounter,
    ) -> Encounter:
        """
        Create a new encounter.
        """
        return await self.create(encounter)

    async def get_by_encounter_number(
        self,
        encounter_number: str,
    ) -> Encounter | None:
        """
        Retrieve encounter using encounter number.
        """

        result = await self.session.execute(
            select(Encounter).where(
                Encounter.encounter_number == encounter_number
            )
        )

        return result.scalar_one_or_none()

    async def get_by_id_with_details(
        self,
        encounter_id: UUID,
    ) -> Encounter | None:
        """
        Retrieve encounter with related entities.
        """

        result = await self.session.execute(
            select(Encounter)
            .options(
                selectinload(Encounter.diagnoses),
                selectinload(Encounter.prescriptions),
                selectinload(Encounter.doctor_notes),
                selectinload(Encounter.medical_reports),
            )
            .where(Encounter.id == encounter_id)
        )

        return result.scalar_one_or_none()

    async def get_patient_encounters(
        self,
        patient_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Encounter], int]:
        """
        Return paginated encounters for a patient.
        """

        offset = (page - 1) * page_size

        total = await self.session.scalar(
            select(func.count())
            .select_from(Encounter)
            .where(
                Encounter.patient_id == patient_id
            )
        )

        result = await self.session.execute(
            select(Encounter)
            .where(
                Encounter.patient_id == patient_id
            )
            .order_by(
                Encounter.encounter_date.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        return (
            list(result.scalars().all()),
            total or 0,
        )

    async def update_encounter(
        self,
        encounter: Encounter,
    ) -> Encounter:
        """
        Persist encounter changes.
        """

        await self.session.flush()
        await self.session.refresh(encounter)

        return encounter
    

    async def get_by_doctor_and_patient(
        self,
        doctor_id: UUID,
        patient_id: UUID,
    ) -> list[Encounter]:
        """
        Get encounters for a doctor and patient.
        """

        result = await self.session.execute(
            select(Encounter)
            .where(
                Encounter.doctor_id == doctor_id,
                Encounter.patient_id == patient_id,
            )
            .order_by(
                Encounter.created_at.desc()
            )
        )

        return list(result.scalars().all())