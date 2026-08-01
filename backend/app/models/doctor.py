from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity


class Doctor(Base, BaseEntity):
    __tablename__ = "doctors"

    user_id: Mapped[UUID] = mapped_column(
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

    license_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    specialization: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20),
    )

    hospital_name: Mapped[str | None] = mapped_column(
        String(255),
    )

    years_of_experience: Mapped[int | None] = mapped_column(
        Integer,
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