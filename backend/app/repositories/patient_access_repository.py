"""
Repository for patient-doctor access grants.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient_access import AccessStatus, PatientAccess
from app.repositories.base_repository import BaseRepository


class PatientAccessRepository(BaseRepository[PatientAccess]):
    """Repository for patient access records."""

    def __init__(self, session: AsyncSession):
        super().__init__(PatientAccess, session)

    async def create_access(self, access: PatientAccess) -> PatientAccess:
        return await self.create(access)

    async def get_by_patient_and_doctor(
        self,
        patient_id: UUID,
        doctor_id: UUID,
    ) -> list[PatientAccess]:
        result = await self.session.execute(
            select(PatientAccess)
            .where(PatientAccess.patient_id == patient_id)
            .where(PatientAccess.doctor_id == doctor_id)
            .order_by(PatientAccess.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_access(
        self,
        patient_id: UUID,
        doctor_id: UUID,
    ) -> PatientAccess | None:
        result = await self.session.execute(
            select(PatientAccess)
            .where(PatientAccess.patient_id == patient_id)
            .where(PatientAccess.doctor_id == doctor_id)
            .where(PatientAccess.status == AccessStatus.APPROVED)
            .where(PatientAccess.expires_at > datetime.now(timezone.utc))
            .order_by(PatientAccess.approved_at.desc())
        )
        return result.scalar_one_or_none()

    async def list_for_patient(
        self,
        patient_id: UUID,
    ) -> list[PatientAccess]:
        result = await self.session.execute(
            select(PatientAccess)
            .where(PatientAccess.patient_id == patient_id)
            .order_by(PatientAccess.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_for_doctor(
        self,
        doctor_id: UUID,
    ) -> list[PatientAccess]:
        result = await self.session.execute(
            select(PatientAccess)
            .where(PatientAccess.doctor_id == doctor_id)
            .order_by(PatientAccess.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_access(self, access: PatientAccess) -> PatientAccess:
        await self.session.flush()
        await self.session.refresh(access)
        return access
