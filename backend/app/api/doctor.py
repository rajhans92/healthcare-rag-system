"""
Doctor API endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import (
    get_current_user,
    get_doctor_service,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.doctor import (
    DoctorResponse,
    UpdateDoctorRequest,
)
from app.services.doctor_service import DoctorService

router = APIRouter(
    prefix="/doctors",
    tags=["Doctors"],
)

@router.get(
    "/me",
    response_model=ApiResponse[DoctorResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    service: DoctorService = Depends(get_doctor_service),
):
    """
    Get logged-in doctor's profile.
    """

    doctor = await service.get_my_profile(
        current_user.id,
    )

    return ApiResponse(
        message="Doctor profile retrieved successfully.",
        data=doctor,
    )

@router.put(
    "/me",
    response_model=ApiResponse[DoctorResponse],
    status_code=status.HTTP_200_OK,
)
async def update_my_profile(
    request: UpdateDoctorRequest,
    current_user: User = Depends(get_current_user),
    service: DoctorService = Depends(get_doctor_service),
):
    """
    Update logged-in doctor's profile.
    """

    doctor = await service.update_profile(
        current_user.id,
        request,
    )

    return ApiResponse(
        message="Doctor profile updated successfully.",
        data=doctor,
    )

@router.get(
    "/{doctor_id}",
    response_model=ApiResponse[DoctorResponse],
    status_code=status.HTTP_200_OK,
)
async def get_doctor_by_id(
    doctor_id: UUID,
    service: DoctorService = Depends(get_doctor_service),
):
    """
    Get doctor by ID.
    """

    doctor = await service.get_doctor_by_id(
        doctor_id,
    )

    return ApiResponse(
        message="Doctor retrieved successfully.",
        data=doctor,
    )

@router.get(
    "",
    response_model=ApiResponse[list[DoctorResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_doctors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: DoctorService = Depends(get_doctor_service),
):
    """
    Get all doctors.
    """

    doctors = await service.list_doctors(
        page=page,
        page_size=page_size,
    )

    return ApiResponse(
        message="Doctors retrieved successfully.",
        data=doctors,
    )

