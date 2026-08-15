"""
Doctor repository.

Responsible for all database operations related to Doctor.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.repositories.base_repository import BaseRepository


class DoctorRepository(BaseRepository[Doctor]):
    """
    Repository for Doctor entity.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(Doctor, session)

    async def create_doctor(
        self,
        doctor: Doctor,
    ) -> Doctor:
        """
        Create doctor profile.
        """
        return await self.create(doctor)

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> Doctor | None:
        """
        Get doctor by user ID.
        """

        result = await self.session.execute(
            select(Doctor).where(
                Doctor.user_id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_registration_number(
        self,
        registration_number: str,
    ) -> Doctor | None:
        """
        Get doctor by registration number.
        """

        result = await self.session.execute(
            select(Doctor).where(
                Doctor.registration_number == registration_number
            )
        )

        return result.scalar_one_or_none()

    async def exists_by_registration_number(
        self,
        registration_number: str,
    ) -> bool:
        """
        Check if registration number already exists.
        """

        result = await self.session.execute(
            select(Doctor.id).where(
                Doctor.registration_number == registration_number
            )
        )

        return result.scalar_one_or_none() is not None

    async def update_doctor(
        self,
        doctor: Doctor,
    ) -> Doctor:
        """
        Update doctor profile.
        """

        await self.session.flush()
        await self.session.refresh(doctor)

        return doctor

    async def list_doctors(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Doctor]:
        """
        Get paginated list of doctors.
        """

        result = await self.session.execute(
            select(Doctor)
            .offset(offset)
            .limit(limit)
        )

        return result.scalars().all()
    
    async def create_for_user(
        self,
        user_id: UUID,
    ) -> Doctor:
        """Create an initial doctor row for a user.

        Avoid using duplicate empty strings for unique fields. license_number is
        non-nullable and unique, so generate a temporary unique placeholder. The
        registration_number is nullable and should be left as NULL when not
        provided by the user (avoid empty string which would violate the unique
        constraint on subsequent inserts).
        """
        from uuid import uuid4

        doctor = Doctor(
            user_id=user_id,
            # license_number must be unique and non-nullable; use a temporary unique
            # placeholder until the doctor updates their real license number.
            license_number=f"temp-{uuid4().hex}",
            # registration_number is nullable in the model — use None instead of ''
            registration_number=None,
            specialization="",
            qualification=None,
            department=None,
            bio=None,
            experience_years=0,
            consultation_fee=0,
        )

        self.session.add(doctor)

        await self.session.flush()

        return doctor