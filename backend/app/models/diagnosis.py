from enum import Enum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Enum as SqlEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Diagnosis(Base, BaseEntity):
    __tablename__ = "diagnoses"

    encounter_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("encounters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    diagnosis_code: Mapped[str | None] = mapped_column(
        String(20),
    )

    diagnosis_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    severity: Mapped[Severity | None] = mapped_column(
        SqlEnum(Severity),
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    encounter = relationship(
        "Encounter",
        back_populates="diagnoses",
    )

    def __repr__(self):
        return (
            f"<Diagnosis("
            f"name='{self.diagnosis_name}', "
            f"primary={self.is_primary})>"
        )