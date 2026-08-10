"""
Diagnosis service.

Contains business logic related to diagnoses.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diagnosis import Diagnosis
from app.models.encounter import EncounterStatus
from app.models.user import User
from app.repositories.diagnosis_repository import DiagnosisRepository
from app.repositories.encounter_repository import EncounterRepository
from app.schemas.diagnosis import (
    CreateDiagnosisRequest,
    DiagnosisResponse,
    UpdateDiagnosisRequest,
)

logger = logging.getLogger(__name__)


class DiagnosisService:
    """
    Service responsible for diagnosis management.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.diagnosis_repository = DiagnosisRepository(
            session
        )

        self.encounter_repository = EncounterRepository(
            session
        )

    # ==========================================================
    # Private Validation Methods
    # ==========================================================

    async def _get_encounter(
        self,
        encounter_id: UUID,
    ):
        """
        Get encounter or raise an error.
        """

        encounter = await self.encounter_repository.get_by_id(
            encounter_id
        )

        if encounter is None:
            raise ValueError(
                "Encounter not found."
            )

        return encounter

    def _validate_encounter_access(
        self,
        encounter,
        doctor: User,
    ) -> None:
        """
        Verify that the doctor owns the encounter.
        """

        if encounter.doctor_id != doctor.id:
            raise PermissionError(
                "You are not authorized to access this encounter."
            )

    def _validate_encounter_is_open(
        self,
        encounter,
    ) -> None:
        """
        Ensure diagnosis can only be modified
        while encounter is open.
        """

        if encounter.status != EncounterStatus.OPEN:
            raise ValueError(
                "Diagnosis cannot be modified because "
                "the encounter is not open."
            )

    # ==========================================================
    # Create Diagnosis
    # ==========================================================

    async def create_diagnosis(
        self,
        encounter_id: UUID,
        doctor: User,
        request: CreateDiagnosisRequest,
    ) -> DiagnosisResponse:
        """
        Create a diagnosis for an encounter.
        """

        logger.info(
            "Creating diagnosis for encounter=%s doctor=%s",
            encounter_id,
            doctor.id,
        )

        try:
            encounter = await self._get_encounter(
                encounter_id
            )

            self._validate_encounter_access(
                encounter,
                doctor,
            )

            self._validate_encounter_is_open(
                encounter
            )

            # --------------------------------------------------
            # Validate primary diagnosis
            # --------------------------------------------------

            if request.is_primary:

                existing_primary = (
                    await self.diagnosis_repository
                    .get_primary_diagnosis(
                        encounter_id
                    )
                )

                if existing_primary is not None:
                    raise ValueError(
                        "This encounter already has "
                        "a primary diagnosis."
                    )

            # --------------------------------------------------
            # Create diagnosis
            # --------------------------------------------------

            diagnosis = Diagnosis(
                encounter_id=encounter_id,
                diagnosis_name=request.diagnosis_name,
                icd10_code=request.icd10_code,
                diagnosis_type=request.diagnosis_type,
                is_primary=request.is_primary,
                notes=request.notes,
                created_by=doctor.id,
            )

            diagnosis = (
                await self.diagnosis_repository
                .create_diagnosis(
                    diagnosis
                )
            )

            await self.session.commit()

            await self.session.refresh(
                diagnosis
            )

            logger.info(
                "Diagnosis created successfully id=%s",
                diagnosis.id,
            )

            return DiagnosisResponse.model_validate(
                diagnosis
            )

        except Exception:

            logger.exception(
                "Failed to create diagnosis."
            )

            await self.session.rollback()

            raise

    # ==========================================================
    # Get Diagnosis
    # ==========================================================

    async def get_diagnosis(
        self,
        diagnosis_id: UUID,
        doctor: User,
    ) -> DiagnosisResponse:
        """
        Get a diagnosis.

        The doctor must own the encounter associated
        with the diagnosis.
        """

        diagnosis = (
            await self.diagnosis_repository.get_by_id(
                diagnosis_id
            )
        )

        if diagnosis is None:
            raise ValueError(
                "Diagnosis not found."
            )

        encounter = await self._get_encounter(
            diagnosis.encounter_id
        )

        self._validate_encounter_access(
            encounter,
            doctor,
        )

        return DiagnosisResponse.model_validate(
            diagnosis
        )

    # ==========================================================
    # List Diagnoses
    # ==========================================================

    async def get_encounter_diagnoses(
        self,
        encounter_id: UUID,
        doctor: User,
    ) -> list[DiagnosisResponse]:
        """
        Get all diagnoses belonging to an encounter.
        """

        encounter = await self._get_encounter(
            encounter_id
        )

        self._validate_encounter_access(
            encounter,
            doctor,
        )

        diagnoses = (
            await self.diagnosis_repository
            .get_by_encounter_id(
                encounter_id
            )
        )

        return [
            DiagnosisResponse.model_validate(
                diagnosis
            )
            for diagnosis in diagnoses
        ]

    # ==========================================================
    # Update Diagnosis
    # ==========================================================

    async def update_diagnosis(
        self,
        diagnosis_id: UUID,
        doctor: User,
        request: UpdateDiagnosisRequest,
    ) -> DiagnosisResponse:
        """
        Update an existing diagnosis.
        """

        logger.info(
            "Updating diagnosis=%s doctor=%s",
            diagnosis_id,
            doctor.id,
        )

        try:
            diagnosis = (
                await self.diagnosis_repository
                .get_by_id(
                    diagnosis_id
                )
            )

            if diagnosis is None:
                raise ValueError(
                    "Diagnosis not found."
                )

            encounter = await self._get_encounter(
                diagnosis.encounter_id
            )

            self._validate_encounter_access(
                encounter,
                doctor,
            )

            self._validate_encounter_is_open(
                encounter
            )

            # --------------------------------------------------
            # Primary diagnosis validation
            # --------------------------------------------------

            if request.is_primary is True:

                existing_primary = (
                    await self.diagnosis_repository
                    .get_primary_diagnosis(
                        diagnosis.encounter_id
                    )
                )

                if (
                    existing_primary is not None
                    and existing_primary.id
                    != diagnosis.id
                ):
                    raise ValueError(
                        "This encounter already has "
                        "another primary diagnosis."
                    )

            # --------------------------------------------------
            # Update only supplied fields
            # --------------------------------------------------

            if request.diagnosis_name is not None:
                diagnosis.diagnosis_name = (
                    request.diagnosis_name
                )

            if request.icd10_code is not None:
                diagnosis.icd10_code = (
                    request.icd10_code
                )

            if request.diagnosis_type is not None:
                diagnosis.diagnosis_type = (
                    request.diagnosis_type
                )

            if request.is_primary is not None:
                diagnosis.is_primary = (
                    request.is_primary
                )

            if request.notes is not None:
                diagnosis.notes = request.notes

            diagnosis = (
                await self.diagnosis_repository
                .update_diagnosis(
                    diagnosis
                )
            )

            await self.session.commit()

            logger.info(
                "Diagnosis updated successfully id=%s",
                diagnosis.id,
            )

            return DiagnosisResponse.model_validate(
                diagnosis
            )

        except Exception:

            logger.exception(
                "Failed to update diagnosis."
            )

            await self.session.rollback()

            raise

    # ==========================================================
    # Delete Diagnosis
    # ==========================================================

    async def delete_diagnosis(
        self,
        diagnosis_id: UUID,
        doctor: User,
    ) -> None:
        """
        Delete a diagnosis.
        """

        logger.info(
            "Deleting diagnosis=%s doctor=%s",
            diagnosis_id,
            doctor.id,
        )

        try:
            diagnosis = (
                await self.diagnosis_repository
                .get_by_id(
                    diagnosis_id
                )
            )

            if diagnosis is None:
                raise ValueError(
                    "Diagnosis not found."
                )

            encounter = await self._get_encounter(
                diagnosis.encounter_id
            )

            self._validate_encounter_access(
                encounter,
                doctor,
            )

            self._validate_encounter_is_open(
                encounter
            )

            await self.diagnosis_repository.delete_diagnosis(
                diagnosis
            )

            await self.session.commit()

            logger.info(
                "Diagnosis deleted successfully id=%s",
                diagnosis_id,
            )

        except Exception:

            logger.exception(
                "Failed to delete diagnosis."
            )

            await self.session.rollback()

            raise