"""
Encounter API endpoints.
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_current_user,
    require_doctor,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.encounter import (
    CreateEncounterRequest,
    EncounterListResponse,
    EncounterResponse,
    UpdateEncounterRequest,
)
from app.services.encounter_service import EncounterService

router = APIRouter(
    prefix="/encounters",
    tags=["Encounter"],
)

@router.post(
    "",
    response_model=EncounterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_encounter(
    request: CreateEncounterRequest,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new encounter.
    """

    service = EncounterService(db)

    return await service.create_encounter(
        current_user,
        request,
    )

@router.get(
    "/{encounter_id}",
    response_model=EncounterResponse,
)
async def get_encounter(
    encounter_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get encounter details.
    """

    service = EncounterService(db)

    return await service.get_encounter(
        encounter_id,
    )

@router.put(
    "/{encounter_id}",
    response_model=EncounterResponse,
)
async def update_encounter(
    encounter_id: UUID,
    request: UpdateEncounterRequest,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Update encounter.
    """

    service = EncounterService(db)

    return await service.update_encounter(
        encounter_id,
        current_user,
        request,
    )

@router.get(
    "/patients/{patient_id}",
    response_model=EncounterListResponse,
)
async def get_patient_encounters(
    patient_id: UUID,
    doctor_id: UUID | None = Query(
        default=None,
        description="Optional doctor ID to filter encounters for a specific doctor.",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get patient encounter history.
    """

    service = EncounterService(db)

    return await service.list_patient_encounters(
        patient_id=patient_id,
        current_user=current_user,
        page=page,
        page_size=page_size,
        doctor_id=doctor_id,
    )

@router.patch(
    "/{encounter_id}/complete",
)
async def complete_encounter(
    encounter_id: UUID,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete encounter.
    """

    service = EncounterService(db)

    return await service.complete_encounter(
        encounter_id,
        current_user,
    )

