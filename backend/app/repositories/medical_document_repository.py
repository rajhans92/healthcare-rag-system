"""
Repository for MedicalDocument entity.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_document import (
    DocumentProcessingStatus,
    MedicalDocument,
)
from app.repositories.base_repository import BaseRepository


class MedicalDocumentRepository(
    BaseRepository[MedicalDocument]
):
    """
    Repository for medical document database operations.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        super().__init__(
            MedicalDocument,
            session,
        )

    # ==========================================================
    # Create
    # ==========================================================

    async def create_document(
        self,
        document: MedicalDocument,
    ) -> MedicalDocument:
        """
        Create a medical document record.
        """

        return await self.create(document)

    # ==========================================================
    # Get By ID
    # ==========================================================

    async def get_by_id(
        self,
        document_id: UUID,
    ) -> MedicalDocument | None:
        """
        Get medical document by ID.
        """

        result = await self.session.execute(
            select(MedicalDocument).where(
                MedicalDocument.id == document_id
            )
        )

        return result.scalar_one_or_none()

    # ==========================================================
    # Get Patient Documents
    # ==========================================================

    async def get_patient_documents(
        self,
        patient_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[MedicalDocument], int]:
        """
        Get paginated documents belonging to a patient.
        """

        offset = (page - 1) * page_size

        # Total count
        from sqlalchemy import func

        total = await self.session.scalar(
            select(func.count())
            .select_from(MedicalDocument)
            .where(
                MedicalDocument.patient_id == patient_id
            )
        )

        # Documents
        result = await self.session.execute(
            select(MedicalDocument)
            .where(
                MedicalDocument.patient_id == patient_id
            )
            .order_by(
                MedicalDocument.created_at.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        documents = list(
            result.scalars().all()
        )

        return documents, total or 0

    # ==========================================================
    # Get Encounter Documents
    # ==========================================================

    async def get_encounter_documents(
        self,
        encounter_id: UUID,
    ) -> list[MedicalDocument]:
        """
        Get documents associated with an encounter.
        """

        result = await self.session.execute(
            select(MedicalDocument)
            .where(
                MedicalDocument.encounter_id
                == encounter_id
            )
            .order_by(
                MedicalDocument.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # ==========================================================
    # Update Processing Status
    # ==========================================================

    async def update_processing_status(
        self,
        document: MedicalDocument,
        status: DocumentProcessingStatus,
        error: str | None = None,
    ) -> MedicalDocument:
        """
        Update document processing status.
        """

        document.processing_status = status
        document.processing_error = error

        if self.session is None:
            return document

        await self.session.flush()
        await self.session.refresh(document)

        return document

    # ==========================================================
    # Get Pending Documents
    # ==========================================================

    async def get_pending_documents(
        self,
        limit: int = 100,
    ) -> list[MedicalDocument]:
        """
        Get documents waiting for processing.

        Useful for background workers/recovery jobs.
        """

        result = await self.session.execute(
            select(MedicalDocument)
            .where(
                MedicalDocument.processing_status
                == DocumentProcessingStatus.PENDING
            )
            .order_by(
                MedicalDocument.created_at.asc()
            )
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )