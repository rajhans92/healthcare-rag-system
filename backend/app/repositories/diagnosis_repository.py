"""
Repository for Diagnosis entity.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diagnosis import Diagnosis
from app.repositories.base_repository import BaseRepository


class DiagnosisRepository(BaseRepository[Diagnosis]):
    """
    Repository for diagnosis database operations.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        super().__init__(Diagnosis, session)

    async def create_diagnosis(
        self,
        diagnosis: Diagnosis,
    ) -> Diagnosis:
        """
        Create a new diagnosis.
        """
        return await self.create(diagnosis)

    async def get_by_id(
        self,
        diagnosis_id: UUID,
    ) -> Diagnosis | None:
        """
        Get diagnosis by ID.
        """

        result = await self.session.execute(
            select(Diagnosis).where(
                Diagnosis.id == diagnosis_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_encounter_id(
        self,
        encounter_id: UUID,
    ) -> list[Diagnosis]:
        """
        Get all diagnoses belonging to an encounter.
        """

        result = await self.session.execute(
            select(Diagnosis)
            .where(
                Diagnosis.encounter_id == encounter_id
            )
            .order_by(
                Diagnosis.is_primary.desc(),
                Diagnosis.created_at.asc(),
            )
        )

        return list(result.scalars().all())

    async def get_primary_diagnosis(
        self,
        encounter_id: UUID,
    ) -> Diagnosis | None:
        """
        Get the primary diagnosis for an encounter.
        """

        result = await self.session.execute(
            select(Diagnosis).where(
                Diagnosis.encounter_id == encounter_id,
                Diagnosis.is_primary.is_(True),
            )
        )

        return result.scalar_one_or_none()

    async def update_diagnosis(
        self,
        diagnosis: Diagnosis,
    ) -> Diagnosis:
        """
        Persist diagnosis changes.
        """

        await self.session.flush()
        await self.session.refresh(diagnosis)

        return diagnosis

    async def delete_diagnosis(
        self,
        diagnosis: Diagnosis,
    ) -> None:
        """
        Delete a diagnosis.
        """

        await self.session.delete(diagnosis)
        await self.session.flush()