"""OAuth session model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from skillhub_db.base import Base, TimestampMixin, UUIDMixin


class OAuthSession(UUIDMixin, TimestampMixin, Base):
    """OAuth session — stores hashed tokens only."""

    __tablename__ = "oauth_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    access_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_sessions")

    def __repr__(self) -> str:
        return f"<OAuthSession provider={self.provider!r}>"


from skillhub_db.models.user import User as User  # noqa: E402, F811
