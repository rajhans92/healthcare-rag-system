"""
Patient API endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import (
    get_current_user,
    get_patient_service,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.patient import (
    PatientResponse,
    UpdatePatientRequest,
)
from app.services.patient_service import PatientService

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)

@router.get(
    "/me",
    response_model=ApiResponse[PatientResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    service: PatientService = Depends(get_patient_service),
):
    """
    Get logged-in patient's profile.
    """

    patient = await service.get_my_profile(
        current_user.id,
    )

    return ApiResponse(
        message="Patient profile retrieved successfully.",
        data=patient,
    )

@router.put(
    "/me",
    response_model=ApiResponse[PatientResponse],
)
async def update_my_profile(
    request: UpdatePatientRequest,
    current_user: User = Depends(get_current_user),
    service: PatientService = Depends(get_patient_service),
):
    """
    Update logged-in patient's profile.
    """

    patient = await service.update_profile(
        current_user.id,
        request,
    )

    return ApiResponse(
        message="Patient profile updated successfully.",
        data=patient,
    )

@router.get(
    "/{patient_id}",
    response_model=ApiResponse[PatientResponse],
)
async def get_patient_by_id(
    patient_id: UUID,
    service: PatientService = Depends(get_patient_service),
):
    """
    Get patient by patient ID.
    """

    patient = await service.get_patient_by_id(
        patient_id,
    )

    return ApiResponse(
        message="Patient retrieved successfully.",
        data=patient,
    )

