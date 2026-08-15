"""
Encounter service.

Contains all encounter business logic.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.encounter import (
    Encounter,
    EncounterStatus,
)
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.encounter_repository import EncounterRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.encounter import (
    CreateEncounterRequest,
    EncounterResponse,
    EncounterSummaryResponse,
    UpdateEncounterRequest,
)

logger = logging.getLogger(__name__)


class EncounterService:
    """
    Service responsible for encounter management.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:

        self.session = session

        self.encounter_repository = EncounterRepository(
            session
        )

        self.patient_repository = PatientRepository(
            session
        )

        self.doctor_repository = DoctorRepository(
            session
        )

    async def create_encounter(
        self,
        current_user,
        request: CreateEncounterRequest,
    ) -> EncounterResponse:
        """
        Create encounter.
        """

        logger.info(
            "Creating encounter for patient=%s",
            request.patient_id,
        )

        try:

            patient = await (
                self.patient_repository.get_by_id(
                    request.patient_id
                )
            )

            if patient is None:
                raise ValueError(
                    "Patient not found."
                )

            doctor = await (
                self.doctor_repository.get_by_user_id(
                    current_user.id
                )
            )

            if doctor is None:
                raise ValueError(
                    "Doctor profile not found for the authenticated user."
                )

            if request.doctor_id is not None and request.doctor_id != doctor.id:
                raise ValueError(
                    "Doctor ID mismatch with the authenticated doctor."
                )

            encounter = Encounter(
                encounter_number=await self._generate_encounter_number(),
                patient_id=request.patient_id,
                doctor_id=doctor.id,
                encounter_type=request.encounter_type,
                visit_date=request.encounter_date,
                chief_complaint=request.chief_complaint,
                status=EncounterStatus.OPEN,
            )

            encounter = await (
                self.encounter_repository.create_encounter(
                    encounter
                )
            )

            await self.session.commit()

            await self.session.refresh(
                encounter
            )

            logger.info(
                "Encounter created successfully."
            )

            return EncounterResponse.model_validate(
                encounter
            )

        except Exception:

            logger.exception(
                "Encounter creation failed."
            )

            await self.session.rollback()

            raise

    async def _generate_encounter_number(self) -> str:
        """Create a unique encounter number."""

        prefix = "ENC"
        base = datetime.now(timezone.utc).strftime("%Y%m%d")

        for _ in range(10):
            number = f"{prefix}-{base}-{uuid4().hex[:8].upper()}"
            existing = await self.encounter_repository.get_by_encounter_number(number)
            if existing is None:
                return number

        raise RuntimeError("Unable to generate a unique encounter number.")

    async def get_encounter(
        self,
        encounter_id,
    ) -> EncounterResponse:
        """
        Get encounter details.
        """

        encounter = await (
            self.encounter_repository.get_by_id(
                encounter_id
            )
        )

        if encounter is None:
            raise ValueError(
                "Encounter not found."
            )

        return EncounterResponse.model_validate(
            encounter
        )
    
    async def list_patient_encounters(
        self,
        patient_id,
        page: int,
        page_size: int,
        current_user=None,
        doctor_id=None,
    ):
        """
        List patient encounters.
        """

        encounters, total = (
            await self.encounter_repository.get_patient_encounters(
                patient_id,
                page,
                page_size,
                doctor_id=doctor_id,
            )
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                EncounterSummaryResponse.model_validate(
                    encounter
                )
                for encounter in encounters
            ],
        }
    
