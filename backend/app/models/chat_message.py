from enum import Enum
from uuid import UUID

from sqlalchemy import (
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseEntity


class MessageRole(str, Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class ChatMessage(Base, BaseEntity):
    __tablename__ = "chat_messages"

    chat_session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[MessageRole] = mapped_column(
        SqlEnum(MessageRole),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    citations: Mapped[dict | None] = mapped_column(
        JSONB,
    )

    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer,
    )

    completion_tokens: Mapped[int | None] = mapped_column(
        Integer,
    )

    total_tokens: Mapped[int | None] = mapped_column(
        Integer,
    )

    response_time_ms: Mapped[int | None] = mapped_column(
        Integer,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
    )

    chat_session = relationship(
        "ChatSession",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return (
            f"<ChatMessage("
            f"role='{self.role}', "
            f"session='{self.chat_session_id}')>"
        )