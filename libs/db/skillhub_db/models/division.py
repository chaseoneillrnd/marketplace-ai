"""Division model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from skillhub_db.base import Base


class Division(Base):
    """Organizational division. Slug is the primary key."""

    __tablename__ = "divisions"

    slug: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    def __repr__(self) -> str:
        return f"<Division {self.slug!r}>"
