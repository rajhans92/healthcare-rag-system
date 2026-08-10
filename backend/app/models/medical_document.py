from enum import Enum
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Enum as SqlEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity


class DocumentSource(str, Enum):
    """
    Who uploaded the medical document.
    """

    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    SYSTEM = "SYSTEM"


class DocumentType(str, Enum):
    """
    Type/category of medical document.
    """

    LAB_REPORT = "LAB_REPORT"
    PRESCRIPTION = "PRESCRIPTION"
    DIAGNOSIS_REPORT = "DIAGNOSIS_REPORT"
    RADIOLOGY_REPORT = "RADIOLOGY_REPORT"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    MEDICAL_HISTORY = "MEDICAL_HISTORY"
    OTHER = "OTHER"


class DocumentProcessingStatus(str, Enum):
    """
    Document ingestion status.
    """

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MedicalDocument(Base, BaseEntity):
    """
    Stores metadata for patient/doctor uploaded
    medical documents.

    Actual files are stored in S3.
    """

    __tablename__ = "medical_documents"

    # ---------------------------------------------------------
    # Patient
    # ---------------------------------------------------------

    patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "patients.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Encounter
    # ---------------------------------------------------------

    encounter_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "encounters.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # Uploaded By
    # ---------------------------------------------------------

    uploaded_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Document Information
    # ---------------------------------------------------------

    source: Mapped[DocumentSource] = mapped_column(
        SqlEnum(DocumentSource),
        nullable=False,
        index=True,
    )

    document_type: Mapped[DocumentType] = mapped_column(
        SqlEnum(DocumentType),
        nullable=False,
        default=DocumentType.OTHER,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # File Information
    # ---------------------------------------------------------

    file_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_key: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        unique=True,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    # ---------------------------------------------------------
    # Processing
    # ---------------------------------------------------------

    processing_status: Mapped[
        DocumentProcessingStatus
    ] = mapped_column(
        SqlEnum(DocumentProcessingStatus),
        nullable=False,
        default=DocumentProcessingStatus.PENDING,
        index=True,
    )

    processing_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    patient = relationship(
        "Patient",
        back_populates="medical_documents",
    )

    encounter = relationship(
        "Encounter",
        back_populates="medical_documents",
    )

    uploaded_by_user = relationship(
        "User",
        foreign_keys=[uploaded_by],
    )

    patient = relationship(
        "Patient",
        back_populates="medical_documents",
    )

    encounter = relationship(
        "Encounter",
        back_populates="medical_documents",
    )
    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<MedicalDocument("
            f"id={self.id}, "
            f"patient_id={self.patient_id}, "
            f"file_name='{self.file_name}', "
            f"status='{self.processing_status}')>"
        )