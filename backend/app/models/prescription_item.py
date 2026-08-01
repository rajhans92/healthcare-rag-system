from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity


class PrescriptionItem(Base, BaseEntity):
    __tablename__ = "prescription_items"

    prescription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    medicine_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    strength: Mapped[str | None] = mapped_column(
        String(50),
    )

    dosage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    frequency: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    duration_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    quantity: Mapped[int | None] = mapped_column(
        Integer,
    )

    route: Mapped[str | None] = mapped_column(
        String(50),
    )

    before_food: Mapped[bool | None] = mapped_column(
        Boolean,
    )

    instructions: Mapped[str | None] = mapped_column(
        Text,
    )

    prescription = relationship(
        "Prescription",
        back_populates="prescription_items",
    )

    def __repr__(self):
        return (
            f"<PrescriptionItem("
            f"medicine='{self.medicine_name}', "
            f"dosage='{self.dosage}')>"
        )