"""
Medical document request and response schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.medical_document import (
    DocumentProcessingStatus,
    DocumentSource,
    DocumentType,
)


# ==========================================================
# Create Medical Document
# ==========================================================

class CreateMedicalDocumentRequest(BaseModel):
    """
    Request for creating medical document metadata.
    
    The actual file will be uploaded to S3 separately.
    """

    patient_id: UUID

    encounter_id: UUID | None = None

    document_type: DocumentType = DocumentType.OTHER

    title: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )


# ==========================================================
# Medical Document Response
# ==========================================================

class MedicalDocumentResponse(BaseModel):
    """
    Medical document response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    patient_id: UUID

    encounter_id: UUID | None

    uploaded_by: UUID

    source: DocumentSource

    document_type: DocumentType

    title: str | None

    description: str | None

    file_name: str

    mime_type: str

    file_size: int

    processing_status: DocumentProcessingStatus

    processing_error: str | None

    created_at: datetime

    updated_at: datetime


# ==========================================================
# Document Upload Response
# ==========================================================

class MedicalDocumentUploadResponse(BaseModel):
    """
    Response returned after document upload.
    """

    document_id: UUID

    file_name: str

    processing_status: DocumentProcessingStatus

    message: str


# ==========================================================
# Document Processing Status
# ==========================================================

class MedicalDocumentStatusResponse(BaseModel):
    """
    Document processing status response.
    """

    document_id: UUID

    processing_status: DocumentProcessingStatus

    processing_error: str | None