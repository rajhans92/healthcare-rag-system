"""
Medical document service.
"""

from __future__ import annotations

import hashlib
import logging
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_document import (
    DocumentProcessingStatus,
    DocumentSource,
    MedicalDocument,
)
from app.models.user import User, UserRole
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.encounter_repository import EncounterRepository
from app.repositories.medical_document_repository import (
    MedicalDocumentRepository,
)
from app.repositories.patient_access_repository import PatientAccessRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.medical_document import (
    CreateMedicalDocumentRequest,
    MedicalDocumentResponse,
)
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)


class MedicalDocumentService:
    """
    Business logic for medical documents.
    """

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "text/plain",
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024

    PRESIGNED_URL_EXPIRATION = 900

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.document_repository = (
            MedicalDocumentRepository(session)
        )

        self.patient_repository = (
            PatientRepository(session)
        )

        self.encounter_repository = (
            EncounterRepository(session)
        )

        self.document_ingestion_service = DocumentIngestionService(session)
        self.s3_service = S3Service()

    # ==========================================================
    # Validation
    # ==========================================================

    def _validate_file(
        self,
        file_name: str,
        mime_type: str,
        file_size: int,
    ) -> None:
        """
        Validate uploaded file.
        """

        if not file_name.strip():
            raise ValueError(
                "File name is required."
            )

        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise ValueError(
                f"Unsupported file type: {mime_type}"
            )

        if file_size <= 0:
            raise ValueError(
                "File cannot be empty."
            )

        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                "File size exceeds the 50 MB limit."
            )

    async def _validate_patient(
        self,
        patient_id: UUID,
    ):
        """
        Verify patient exists.
        """

        patient = await self.patient_repository.get_by_id(
            patient_id
        )

        if patient is None:
            raise ValueError(
                "Patient not found."
            )

        return patient

    async def _validate_encounter(
        self,
        patient_id: UUID,
        encounter_id: UUID | None,
    ):
        """
        Verify encounter belongs to patient.
        """

        if encounter_id is None:
            return None

        encounter = (
            await self.encounter_repository.get_by_id(
                encounter_id
            )
        )

        if encounter is None:
            raise ValueError(
                "Encounter not found."
            )

        if encounter.patient_id != patient_id:
            raise ValueError(
                "Encounter does not belong to this patient."
            )

        return encounter

    async def _doctor_has_approved_access(
        self,
        user: User,
        patient_id: UUID,
    ) -> bool:
        """Check whether the current doctor has approved access to a patient."""
        if user.role != UserRole.DOCTOR:
            return True

        doctor = await DoctorRepository(self.session).get_by_user_id(user.id)
        if doctor is None:
            return False

        access = await PatientAccessRepository(self.session).get_active_access(
            patient_id,
            doctor.id,
        )
        return access is not None

    async def _validate_user_access(
        self,
        user: User,
        patient,
    ) -> None:
        """
        Verify the authenticated user can upload
        documents for the patient.
        """

        if user.role == UserRole.PATIENT:

            if patient.user_id != user.id:
                raise PermissionError(
                    "You are not authorized to "
                    "upload documents for this patient."
                )

        elif user.role == UserRole.DOCTOR:
            if not await self._doctor_has_approved_access(user, patient.id):
                raise PermissionError(
                    "You do not have approved access to this patient record."
                )

        else:
            raise PermissionError(
                "User is not authorized to upload "
                "medical documents."
            )

    def _get_document_source(
        self,
        user: User,
    ) -> DocumentSource:

        if user.role == UserRole.PATIENT:
            return DocumentSource.PATIENT

        if user.role == UserRole.DOCTOR:
            return DocumentSource.DOCTOR

        return DocumentSource.SYSTEM

    def _build_s3_key(
        self,
        patient_id: UUID,
        document_id: UUID,
        file_name: str,
    ) -> str:
        """
        Generate unique S3 object key.
        """

        return (
            f"patients/"
            f"{patient_id}/"
            f"documents/"
            f"{document_id}/"
            f"original/"
            f"{file_name}"
        )

    # ==========================================================
    # Generate Upload URL
    # ==========================================================

    async def create_upload_url(
        self,
        user: User,
        request: CreateMedicalDocumentRequest,
        file_name: str,
        mime_type: str,
        file_size: int,
    ) -> dict:
        """
        Create medical document metadata and generate
        a presigned S3 upload URL.
        """

        logger.info(
            "Creating document upload URL "
            "patient=%s user=%s",
            request.patient_id,
            user.id,
        )

        try:
            # --------------------------------------------------
            # Validate file
            # --------------------------------------------------

            self._validate_file(
                file_name=file_name,
                mime_type=mime_type,
                file_size=file_size,
            )

            # --------------------------------------------------
            # Validate patient
            # --------------------------------------------------

            patient = await self._validate_patient(
                request.patient_id
            )

            # --------------------------------------------------
            # Validate user access
            # --------------------------------------------------

            await self._validate_user_access(
                user=user,
                patient=patient,
            )

            # --------------------------------------------------
            # Validate encounter
            # --------------------------------------------------

            await self._validate_encounter(
                patient_id=request.patient_id,
                encounter_id=request.encounter_id,
            )

            # --------------------------------------------------
            # Generate document ID
            # --------------------------------------------------

            document_id = uuid4()

            # --------------------------------------------------
            # Generate S3 key
            # --------------------------------------------------

            file_key = self._build_s3_key(
                patient_id=request.patient_id,
                document_id=document_id,
                file_name=file_name,
            )

            # --------------------------------------------------
            # Determine source
            # --------------------------------------------------

            source = self._get_document_source(
                user
            )

            # --------------------------------------------------
            # Save metadata
            # --------------------------------------------------

            document = MedicalDocument(
                id=document_id,
                patient_id=request.patient_id,
                encounter_id=request.encounter_id,
                uploaded_by=user.id,
                source=source,
                document_type=request.document_type,
                title=request.title,
                description=request.description,
                file_name=file_name,
                file_key=file_key,
                mime_type=mime_type,
                file_size=file_size,
                processing_status=(
                    DocumentProcessingStatus.PENDING
                ),
            )

            await self.document_repository.create_document(
                document
            )

            # --------------------------------------------------
            # Generate S3 presigned URL
            # --------------------------------------------------

            upload_url = (
                self.s3_service.generate_upload_url(
                    file_key=file_key,
                    mime_type=mime_type,
                    expires_in=(
                        self.PRESIGNED_URL_EXPIRATION
                    ),
                )
            )

            # --------------------------------------------------
            # Commit database transaction
            # --------------------------------------------------

            await self.session.commit()

            logger.info(
                "Upload URL generated successfully "
                "document=%s",
                document_id,
            )

            return {
                "document_id": document_id,
                "upload_url": upload_url,
                "file_key": file_key,
                "expires_in": (
                    self.PRESIGNED_URL_EXPIRATION
                ),
            }

        except Exception:

            logger.exception(
                "Failed to create document upload URL."
            )

            await self.session.rollback()

            raise

    # ==========================================================
    # Confirm Upload
    # ==========================================================

    async def confirm_upload(
        self,
        document_id: UUID,
        user: User,
    ) -> MedicalDocumentResponse:
        """
        Confirm that the file was successfully uploaded
        to S3 and schedule processing.
        """

        try:
            document = (
                await self.document_repository.get_by_id(
                    document_id
                )
            )

            if document is None:
                raise ValueError(
                    "Medical document not found."
                )

            # --------------------------------------------------
            # Authorization
            # --------------------------------------------------

            if (
                user.role == UserRole.PATIENT
                and document.uploaded_by != user.id
            ):
                raise PermissionError(
                    "You are not authorized to "
                    "confirm this document."
                )

            if (
                user.role == UserRole.DOCTOR
                and document.uploaded_by != user.id
            ):
                raise PermissionError(
                    "You are not authorized to "
                    "confirm this document."
                )

            # --------------------------------------------------
            # Verify S3 object and detect duplicate uploads
            # --------------------------------------------------

            exists = self.s3_service.object_exists(
                document.file_key
            )

            if not exists:
                raise ValueError(
                    "File has not been uploaded to S3."
                )

            raw_bytes = self.s3_service.download_object(document.file_key)
            file_hash = hashlib.sha256(raw_bytes).hexdigest()
            if await self.document_ingestion_service.detect_duplicate_upload(file_hash):
                raise ValueError(
                    "Duplicate document upload detected."
                )
            self.document_ingestion_service.mark_file_hash_seen(file_hash)

            # --------------------------------------------------
            # Mark document as pending processing
            # --------------------------------------------------

            document.processing_status = (
                DocumentProcessingStatus.PENDING
            )
            document.processing_error = None

            await self.session.commit()
            await self.session.refresh(document)

            logger.info(
                "Document upload confirmed "
                "document=%s",
                document_id,
            )

            content = await self.document_ingestion_service.parse_document_text(document)
            processing_result = await self.document_ingestion_service.process_document(
                document_id=document.id,
                patient_id=document.patient_id,
                content=content,
                metadata={
                    "file_name": document.file_name,
                    "mime_type": document.mime_type,
                    "document_type": document.document_type.value,
                    "source": document.source.value,
                },
            )

            document.processing_status = (
                DocumentProcessingStatus.COMPLETED
            )
            document.processing_error = None
            await self.session.commit()
            await self.session.refresh(document)

            logger.info(
                "Document processing completed for document=%s result=%s",
                document_id,
                processing_result,
            )

            return MedicalDocumentResponse.model_validate(
                document
            )

        except Exception:

            logger.exception(
                "Failed to confirm document upload."
            )

            await self.session.rollback()

            raise

    async def process_pending_documents(
        self,
        limit: int = 20,
    ) -> list[dict]:
        """
        Process all pending documents in queue.
        """
        try:
            return await self.document_ingestion_service.process_pending_documents(limit=limit)
        except Exception:
            logger.exception("Failed to process pending medical documents.")
            raise
    
        # ==========================================================
    # Get Single Document
    # ==========================================================

    async def get_document(
        self,
        document_id: UUID,
        user: User,
    ) -> MedicalDocumentResponse:
        """
        Get a medical document after authorization.
        """

        document = (
            await self.document_repository.get_by_id(
                document_id
            )
        )

        if document is None:
            raise ValueError(
                "Medical document not found."
            )

        # ------------------------------------------------------
        # Patient access
        # ------------------------------------------------------

        if user.role == UserRole.PATIENT:

            patient = await self._validate_patient(
                document.patient_id
            )

            if patient.user_id != user.id:
                raise PermissionError(
                    "You are not authorized to access "
                    "this medical document."
                )

        # ------------------------------------------------------
        # Doctor access
        # ------------------------------------------------------

        elif user.role == UserRole.DOCTOR:
            doctor = await DoctorRepository(self.session).get_by_user_id(user.id)
            if doctor is None:
                raise PermissionError(
                    "Doctor profile not found."
                )

            if document.encounter_id is not None:
                encounter = (
                    await self.encounter_repository
                    .get_by_id(
                        document.encounter_id
                    )
                )

                if encounter is None:
                    raise ValueError(
                        "Associated encounter not found."
                    )

                if encounter.doctor_id != doctor.id:
                    if not await PatientAccessRepository(self.session).get_active_access(
                        document.patient_id,
                        doctor.id,
                    ):
                        raise PermissionError(
                            "You are not authorized to access "
                            "this medical document."
                        )

            else:
                if not await PatientAccessRepository(self.session).get_active_access(
                    document.patient_id,
                    doctor.id,
                ):
                    raise PermissionError(
                        "You are not authorized to access "
                        "this medical document."
                    )

        else:
            raise PermissionError(
                "User is not authorized to access "
                "medical documents."
            )

        return MedicalDocumentResponse.model_validate(
            document
        )

    # ==========================================================
    # Get Patient Documents
    # ==========================================================

    async def get_patient_documents(
        self,
        patient_id: UUID,
        user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> list[MedicalDocumentResponse]:
        """
        Get medical documents for a patient.

        Patients can access their own documents.
        Doctors can access documents for authorized
        patients through the encounter relationship
        for now.
        """

        patient = await self._validate_patient(
            patient_id
        )

        # ------------------------------------------------------
        # Patient access
        # ------------------------------------------------------

        if user.role == UserRole.PATIENT:

            if patient.user_id != user.id:
                raise PermissionError(
                    "You are not authorized to access "
                    "these medical documents."
                )

        # ------------------------------------------------------
        # Doctor access
        # ------------------------------------------------------

        elif user.role == UserRole.DOCTOR:
            doctor = await DoctorRepository(self.session).get_by_user_id(user.id)
            if doctor is None:
                raise PermissionError(
                    "Doctor profile not found."
                )

            encounters = (
                await self.encounter_repository
                .get_by_doctor_and_patient(
                    doctor_id=doctor.id,
                    patient_id=patient_id,
                )
            )

            if not encounters and not await PatientAccessRepository(self.session).get_active_access(
                patient_id,
                doctor.id,
            ):
                raise PermissionError(
                    "You are not authorized to access "
                    "this patient's medical documents."
                )

        else:
            raise PermissionError(
                "User is not authorized to access "
                "medical documents."
            )

        documents, _ = (
            await self.document_repository
            .get_patient_documents(
                patient_id=patient_id,
                page=page,
                page_size=page_size,
            )
        )

        return [
            MedicalDocumentResponse.model_validate(
                document
            )
            for document in documents
        ]
    
    