from datetime import date
from enum import Enum
from uuid import UUID

from sqlalchemy import Date, Enum as SqlEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class Patient(Base, BaseEntity):
    __tablename__ = "patients"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    gender: Mapped[Gender] = mapped_column(
        SqlEnum(Gender),
        nullable=False,
    )

    blood_group: Mapped[str | None] = mapped_column(
        String(5),
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20),
    )

    emergency_contact_name: Mapped[str | None] = mapped_column(
        String(100),
    )

    emergency_contact_number: Mapped[str | None] = mapped_column(
        String(20),
    )

    address: Mapped[str | None] = mapped_column(
        Text,
    )

    # Relationships

    user = relationship(
        "User",
        back_populates="patient",
    )

    encounters = relationship(
        "Encounter",
        back_populates="patient",
        lazy="selectin",
    )

    medical_reports = relationship(
        "MedicalReport",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    chat_sessions = relationship(
        "ChatSession",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    patient_accesses = relationship(
        "PatientAccess",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Patient("
            f"name='{self.first_name} {self.last_name}')>"
        )