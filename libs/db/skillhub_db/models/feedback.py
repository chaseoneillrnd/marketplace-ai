"""Feedback and Platform Updates domain models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from skillhub_db.base import Base


class SkillFeedback(Base):
    """User-submitted feedback on skills or the platform."""

    __tablename__ = "skill_feedback"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"), nullable=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(20), server_default="neutral")
    upvotes: Mapped[int] = mapped_column(Integer, server_default="0", default=0)
    status: Mapped[str] = mapped_column(String(20), server_default="open", default="open")
    allow_contact: Mapped[bool] = mapped_column(Boolean, server_default="false", default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<SkillFeedback {self.id} category={self.category!r}>"


class PlatformUpdate(Base):
    """Roadmap item or changelog entry managed by admins."""

    __tablename__ = "platform_updates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="planned", default="planned")
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_quarter: Mapped[str | None] = mapped_column(String(10), nullable=True)
    linked_feedback_ids: Mapped[list] = mapped_column(JSON, server_default="'[]'::json", default=list)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<PlatformUpdate {self.id} title={self.title!r}>"
