from enum import Enum
from uuid import UUID

from sqlalchemy import (
    Enum as SqlEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity


class AuditStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class AuditLog(Base, BaseEntity):
    __tablename__ = "audit_logs"

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
    )

    status: Mapped[AuditStatus] = mapped_column(
        SqlEnum(AuditStatus),
        nullable=False,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
    )

    details: Mapped[dict | None] = mapped_column(
        JSONB,
    )

    user = relationship(
        "User",
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(action='{self.action}', status='{self.status}')>"
        )