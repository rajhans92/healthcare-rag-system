from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from app.db.base import Base, BaseEntity
from app.models.encounter import Encounter  # noqa: F401
from app.models.user import User  # noqa: F401


class Doctor(Base, BaseEntity):
    __tablename__ = "doctors"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )

    license_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    registration_number: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
    )

    specialization: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    qualification: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    experience_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20),
    )

    hospital_name: Mapped[str | None] = mapped_column(
        String(255),
    )

    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    consultation_fee: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 2),
        nullable=True,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships

    user = relationship(
        "User",
        back_populates="doctor",
    )

    encounters = relationship(
        "Encounter",
        back_populates="doctor",
    )

    patient_accesses = relationship(
        "PatientAccess",
        back_populates="doctor",
    )

    def __repr__(self) -> str:
        return (
            f"<Doctor("
            f"license_number='{self.license_number}', "
            f"specialization='{self.specialization}')>"
        )