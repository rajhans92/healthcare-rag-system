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
from app.enums.roles import Role

class EncounterType(str, Enum):
    OPD = "OPD"
    IPD = "IPD"
    EMERGENCY = "EMERGENCY"
    TELEMEDICINE = "TELEMEDICINE"


class EncounterStatus(str, Enum):
    OPEN = "OPEN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Encounter(Base, BaseEntity):
    __tablename__ = "encounters"

    encounter_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

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

    encounter_type: Mapped[EncounterType] = mapped_column(
        SqlEnum(EncounterType),
        nullable=False,
    )

    chief_complaint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    visit_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[EncounterStatus] = mapped_column(
        SqlEnum(EncounterStatus),
        default=EncounterStatus.OPEN,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
    )

    # Relationships

    patient = relationship(
        "Patient",
        back_populates="encounters",
    )

    doctor = relationship(
        "Doctor",
        back_populates="encounters",
    )

    diagnoses = relationship(
        "Diagnosis",
        back_populates="encounter",
    )

    prescriptions = relationship(
        "Prescription",
        back_populates="encounter",
    )

    doctor_notes = relationship(
        "DoctorNote",
        back_populates="encounter",
    )

    medical_reports = relationship(
        "MedicalReport",
        back_populates="encounter",
    )

    medical_documents = relationship(
        "MedicalDocument",
        back_populates="encounter",
    )

    @property
    def encounter_date(self) -> datetime:
        return self.visit_date

    @encounter_date.setter
    def encounter_date(self, value: datetime) -> None:
        self.visit_date = value

    def __repr__(self):
        return (
            f"<Encounter("
            f"encounter_number='{self.encounter_number}', "
            f"status='{self.status}')>"
        )