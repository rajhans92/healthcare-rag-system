"""
Medical document API endpoints.
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.medical_document import (
    CreateMedicalDocumentRequest,
    MedicalDocumentResponse,
    MedicalDocumentStatusResponse,
)
from app.services.medical_document_service import (
    MedicalDocumentService,
)


router = APIRouter(
    prefix="/medical-documents",
    tags=["Medical Documents"],
)


# ==========================================================
# Generate Upload URL
# ==========================================================

@router.post(
    "/upload-url",
    status_code=status.HTTP_201_CREATED,
)
async def create_upload_url(
    request: CreateMedicalDocumentRequest,
    file_name: str = Query(...),
    mime_type: str = Query(...),
    file_size: int = Query(...),
    current_user: User = Depends(
        get_current_user
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Generate a presigned S3 upload URL.

    The client uploads the actual file directly
    to S3 using the returned URL.
    """

    service = MedicalDocumentService(db)

    return await service.create_upload_url(
        user=current_user,
        request=request,
        file_name=file_name,
        mime_type=mime_type,
        file_size=file_size,
    )


# ==========================================================
# Confirm Upload
# ==========================================================

@router.post(
    "/{document_id}/confirm",
    response_model=MedicalDocumentResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_upload(
    document_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    db: AsyncSession = Depends(get_db),
) -> MedicalDocumentResponse:
    """
    Confirm that the file has been uploaded to S3.
    """

    service = MedicalDocumentService(db)

    return await service.confirm_upload(
        document_id=document_id,
        user=current_user,
    )


# ==========================================================
# Get Patient Documents
# ==========================================================

@router.get(
    "/patients/{patient_id}",
    response_model=list[MedicalDocumentResponse],
)
async def get_patient_documents(
    patient_id: UUID,
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: AsyncSession = Depends(get_db),
) -> list[MedicalDocumentResponse]:
    """
    Get medical documents belonging to a patient.
    """

    service = MedicalDocumentService(db)

    return await service.get_patient_documents(
        patient_id=patient_id,
        user=current_user,
        page=page,
        page_size=page_size,
    )


# ==========================================================
# Get Single Document
# ==========================================================

@router.get(
    "/{document_id}",
    response_model=MedicalDocumentResponse,
)
async def get_medical_document(
    document_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    db: AsyncSession = Depends(get_db),
) -> MedicalDocumentResponse:
    """
    Get a medical document.
    """

    service = MedicalDocumentService(db)

    return await service.get_document(
        document_id=document_id,
        user=current_user,
    )


# ==========================================================
# Process Pending Documents
# ==========================================================

@router.post(
    "/process-pending",
    status_code=status.HTTP_200_OK,
)
async def process_pending_documents(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Process the queue of pending document uploads.
    """
    if current_user.role not in {UserRole.ADMIN, UserRole.DOCTOR}:
        raise PermissionError(
            "Only administrators and doctors can process queued medical documents."
        )

    service = MedicalDocumentService(db)
    return {
        "processed": await service.process_pending_documents(limit=limit),
    }