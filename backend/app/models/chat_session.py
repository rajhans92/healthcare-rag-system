from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity


class ChatSession(Base, BaseEntity):
    __tablename__ = "chat_sessions"

    patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    llm_model: Mapped[str] = mapped_column(
        String(100),
    )

    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    patient = relationship(
        "Patient",
        back_populates="chat_sessions",
    )

    messages = relationship(
        "ChatMessage",
        back_populates="chat_session",
    )

    conversation_summary: Mapped[str | None]
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, title='{self.title}')>"