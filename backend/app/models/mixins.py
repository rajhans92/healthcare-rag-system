"""
Reusable SQLAlchemy mixins.

Every business entity should inherit from BaseEntity to get
common audit fields, optimistic locking and soft delete support.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column
from sqlalchemy.sql import text


class BaseEntity:
    """
    Base mixin for all business entities.

    Provides:
    - UUID Primary Key
    - Audit timestamps
    - Audit user tracking
    - Soft delete
    - Optimistic locking
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="Primary Key",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp (UTC)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp (UTC)",
    )

    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="User who created the record",
    )

    updated_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="User who last updated the record",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="Soft delete flag",
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="Optimistic locking version",
    )

    @declared_attr.directive
    def __mapper_args__(cls) -> dict:
        return {
            "version_id_col": cls.version,
        }