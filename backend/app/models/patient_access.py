from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity
from app.models.doctor import Doctor  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.user import User  # noqa: F401


class AccessStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class PatientAccess(Base, BaseEntity):
    __tablename__ = "patient_access"

    patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    doctor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    otp: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
    )

    status: Mapped[AccessStatus] = mapped_column(
        SqlEnum(AccessStatus),
        nullable=False,
        default=AccessStatus.PENDING,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
    )

    # Relationships

    patient = relationship(
        "Patient",
        back_populates="patient_accesses",
    )

    doctor = relationship(
        "Doctor",
        back_populates="patient_accesses",
    )

    def __repr__(self) -> str:
        return (
            f"<PatientAccess("
            f"patient_id={self.patient_id}, "
            f"doctor_id={self.doctor_id}, "
            f"status={self.status})>"
        )