from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity
from enum import Enum

class NoteType(str, Enum):
    OBSERVATION = "OBSERVATION"
    ADVICE = "ADVICE"
    FOLLOW_UP = "FOLLOW_UP"
    GENERAL = "GENERAL"

class DoctorNote(Base, BaseEntity):
    __tablename__ = "doctor_notes"

    encounter_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("encounters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    note: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    note_type: Mapped[NoteType] = mapped_column(
        SqlEnum(NoteType),
        nullable=False,
        default=NoteType.GENERAL,
    )

    encounter = relationship(
        "Encounter",
        back_populates="doctor_notes",
    )

    def __repr__(self) -> str:
        return (
            f"<DoctorNote(id={self.id})>"
        )