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

class ReportType(str, Enum):
    BLOOD_TEST = "BLOOD_TEST"
    XRAY = "XRAY"
    MRI = "MRI"
    CT_SCAN = "CT_SCAN"
    ECG = "ECG"
    PRESCRIPTION = "PRESCRIPTION"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    OTHER = "OTHER"
    
class UploadStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class MedicalReport(Base, BaseEntity):
    __tablename__ = "medical_reports"

    patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    encounter_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("encounters.id"),
    )

    uploaded_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    report_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    report_type: Mapped[ReportType] = mapped_column(
        String(100),
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    upload_status: Mapped[UploadStatus] = mapped_column(
        SqlEnum(UploadStatus),
        default=UploadStatus.UPLOADED,
        nullable=False,
    )

    patient = relationship(
        "Patient",
        back_populates="medical_reports",
    )

    encounter = relationship(
        "Encounter",
        back_populates="medical_reports",
    )