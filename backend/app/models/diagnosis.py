from enum import Enum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    String,
    Text,
    text,
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

    __table_args__ = (
        Index(
            "uq_diagnosis_one_primary_per_encounter",
            "encounter_id",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
    )

    encounter_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "encounters.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    diagnosis_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    diagnosis_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    severity: Mapped[Severity | None] = mapped_column(
        SqlEnum(Severity),
        nullable=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    encounter = relationship(
        "Encounter",
        back_populates="diagnoses",
    )

    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
    )

    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Diagnosis("
            f"name='{self.diagnosis_name}', "
            f"primary={self.is_primary})>"
        )