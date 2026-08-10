"""
Diagnosis API endpoints.
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_doctor
from app.db.database import get_db
from app.models.user import User
from app.schemas.diagnosis import (
    CreateDiagnosisRequest,
    DiagnosisResponse,
    UpdateDiagnosisRequest,
)
from app.services.diagnosis_service import DiagnosisService


router = APIRouter(
    prefix="/diagnoses",
    tags=["Diagnosis"],
)


# ==========================================================
# Create Diagnosis
# ==========================================================

@router.post(
    "/encounters/{encounter_id}",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_diagnosis(
    encounter_id: UUID,
    request: CreateDiagnosisRequest,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> DiagnosisResponse:
    """
    Create a diagnosis for an encounter.

    Only authenticated doctors can create diagnoses.
    """

    service = DiagnosisService(db)

    return await service.create_diagnosis(
        encounter_id=encounter_id,
        doctor=current_user,
        request=request,
    )


# ==========================================================
# Get Diagnoses for Encounter
# ==========================================================

@router.get(
    "/encounters/{encounter_id}",
    response_model=list[DiagnosisResponse],
)
async def get_encounter_diagnoses(
    encounter_id: UUID,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> list[DiagnosisResponse]:
    """
    Get all diagnoses for an encounter.
    """

    service = DiagnosisService(db)

    return await service.get_encounter_diagnoses(
        encounter_id=encounter_id,
        doctor=current_user,
    )


# ==========================================================
# Get Single Diagnosis
# ==========================================================

@router.get(
    "/{diagnosis_id}",
    response_model=DiagnosisResponse,
)
async def get_diagnosis(
    diagnosis_id: UUID,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> DiagnosisResponse:
    """
    Get a diagnosis by ID.
    """

    service = DiagnosisService(db)

    return await service.get_diagnosis(
        diagnosis_id=diagnosis_id,
        doctor=current_user,
    )


# ==========================================================
# Update Diagnosis
# ==========================================================

@router.put(
    "/{diagnosis_id}",
    response_model=DiagnosisResponse,
)
async def update_diagnosis(
    diagnosis_id: UUID,
    request: UpdateDiagnosisRequest,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> DiagnosisResponse:
    """
    Update a diagnosis.
    """

    service = DiagnosisService(db)

    return await service.update_diagnosis(
        diagnosis_id=diagnosis_id,
        doctor=current_user,
        request=request,
    )


# ==========================================================
# Delete Diagnosis
# ==========================================================

@router.delete(
    "/{diagnosis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_diagnosis(
    diagnosis_id: UUID,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Delete a diagnosis.

    Diagnosis can only be deleted while
    the encounter is open.
    """

    service = DiagnosisService(db)

    await service.delete_diagnosis(
        diagnosis_id=diagnosis_id,
        doctor=current_user,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )