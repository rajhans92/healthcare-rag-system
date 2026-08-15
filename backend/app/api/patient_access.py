"""Patient access endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.patient_access import (
    PatientAccessDecisionRequest,
    PatientAccessRequest,
    PatientAccessResponse,
)
from app.services.patient_access_service import PatientAccessService

router = APIRouter(
    prefix="/patient-access",
    tags=["Patient Access"],
)


@router.post(
    "/request",
    response_model=ApiResponse[PatientAccessResponse],
    status_code=status.HTTP_201_CREATED,
)
async def request_access(
    request: PatientAccessRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Request access to a patient's records for a doctor."""
    service = PatientAccessService(db)
    access = await service.request_access(
        request.patient_id,
        request.doctor_id,
        requester_id=current_user.id,
        requester_role=current_user.role.value,
        expires_days=request.expires_days,
    )
    return ApiResponse(
        message="Patient access request created successfully.",
        data=access,
    )


@router.patch(
    "/{access_id}/status",
    response_model=ApiResponse[PatientAccessResponse],
    status_code=status.HTTP_200_OK,
)
async def update_access_status(
    access_id: UUID,
    request: PatientAccessDecisionRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Approve or reject a patient access request."""
    service = PatientAccessService(db)
    access = await service.update_access_status(
        access_id,
        status=request.status,
        remarks=request.remarks,
        reviewer_id=current_user.id,
        reviewer_role=current_user.role.value,
    )
    return ApiResponse(
        message="Patient access status updated successfully.",
        data=access,
    )


@router.get(
    "/patients/{patient_id}",
    response_model=ApiResponse[list[PatientAccessResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_patient_accesses(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = PatientAccessService(db)
    accesses = await service.list_patient_accesses(patient_id)
    return ApiResponse(
        message="Patient access records retrieved successfully.",
        data=accesses,
    )


@router.get(
    "/doctors/{doctor_id}",
    response_model=ApiResponse[list[PatientAccessResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_doctor_accesses(
    doctor_id: UUID,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = PatientAccessService(db)
    accesses = await service.list_doctor_accesses(doctor_id)
    return ApiResponse(
        message="Doctor access records retrieved successfully.",
        data=accesses,
    )
