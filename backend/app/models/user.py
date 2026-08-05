from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity
from app.enums.roles import Role

class UserRole(str, Enum):
    ADMIN = Role.ADMIN.value
    DOCTOR = Role.DOCTOR.value
    PATIENT = Role.PATIENT.value


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"


class User(Base, BaseEntity):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole),
        nullable=False,
    )

    status: Mapped[UserStatus] = mapped_column(
        SqlEnum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False,
    )

    is_email_verified = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    doctor = relationship(
        "Doctor",
        back_populates="user",
        uselist=False,
    )

    patient = relationship(
        "Patient",
        back_populates="user",
        uselist=False,
    )

    def __repr__(self):
        return f"<User(email={self.email}, role={self.role})>"