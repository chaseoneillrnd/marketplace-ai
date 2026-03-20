"""User model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from skillhub_db.base import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    """User account."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    division: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("divisions.slug"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    oauth_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_platform_team: Mapped[bool] = mapped_column(default=False)
    is_security_team: Mapped[bool] = mapped_column(default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    oauth_sessions: Mapped[list["OAuthSession"]] = relationship(
        "OAuthSession", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username!r}>"


# Import here to avoid circular imports at type-check time
from skillhub_db.models.oauth_session import OAuthSession as OAuthSession  # noqa: E402, F811
