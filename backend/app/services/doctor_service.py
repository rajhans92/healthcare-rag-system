"""
Doctor service.

Contains all business logic related to doctors.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.exceptions import (
    ResourceNotFoundException,
    ValidationException,
)
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor import (
    DoctorResponse,
    UpdateDoctorRequest,
)


class DoctorService:
    """
    Doctor service.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.doctor_repository = DoctorRepository(session)

    async def get_my_profile(
        self,
        user_id: UUID,
    ) -> DoctorResponse:
        """
        Get logged-in doctor's profile.
        """

        doctor = await self.doctor_repository.get_by_user_id(
            user_id
        )

        if doctor is None:
            raise ResourceNotFoundException("Doctor")

        return DoctorResponse.model_validate(doctor)

    async def get_doctor_by_id(
        self,
        doctor_id: UUID,
    ) -> DoctorResponse:
        """
        Get doctor by doctor ID.
        """

        doctor = await self.doctor_repository.get_by_id(
            doctor_id
        )

        if doctor is None:
            raise ResourceNotFoundException("Doctor")

        return DoctorResponse.model_validate(doctor)

    async def update_profile(
        self,
        user_id: UUID,
        request: UpdateDoctorRequest,
    ) -> DoctorResponse:
        """
        Update doctor profile.
        """

        doctor = await self.doctor_repository.get_by_user_id(
            user_id
        )

        if doctor is None:
            raise ResourceNotFoundException("Doctor")

        # Registration number must be unique
        if (
            request.registration_number
            and request.registration_number != doctor.registration_number
        ):
            exists = (
                await self.doctor_repository.exists_by_registration_number(
                    request.registration_number
                )
            )

            if exists:
                raise ValidationException(
                    "Registration number already exists."
                )

        update_data = request.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        for field, value in update_data.items():
            setattr(doctor, field, value)

        await self.doctor_repository.update_doctor(
            doctor
        )

        await self.session.commit()

        await self.session.refresh(doctor)

        return DoctorResponse.model_validate(doctor)

    async def list_doctors(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> list[DoctorResponse]:
        """
        Get paginated doctor list.
        """

        offset = (page - 1) * page_size

        doctors = await self.doctor_repository.list_doctors(
            limit=page_size,
            offset=offset,
        )

        return [
            DoctorResponse.model_validate(
                doctor
            )
            for doctor in doctors
        ]