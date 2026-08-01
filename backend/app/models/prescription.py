from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity


class Prescription(Base, BaseEntity):
    __tablename__ = "prescriptions"

    encounter_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("encounters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    instructions: Mapped[str | None] = mapped_column(
        Text,
    )

    follow_up_date: Mapped[date | None] = mapped_column(
        Date,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
    )

    # Relationships

    encounter = relationship(
        "Encounter",
        back_populates="prescriptions",
    )

    prescription_items = relationship(
        "PrescriptionItem",
        back_populates="prescription",
    )

    def __repr__(self):
        return (
            f"<Prescription(id={self.id})>"
        )