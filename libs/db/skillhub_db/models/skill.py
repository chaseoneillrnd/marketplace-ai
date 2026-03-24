"""Skill Core domain models."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from skillhub_db.base import Base, TimestampMixin, UUIDMixin


class SkillStatus(enum.StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


class InstallMethod(enum.StrEnum):
    CLAUDE_CODE = "claude-code"
    MCP = "mcp"
    MANUAL = "manual"
    ALL = "all"


class DataSensitivity(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PHI = "phi"


class AuthorType(enum.StrEnum):
    OFFICIAL = "official"
    COMMUNITY = "community"


class Category(Base):
    """Skill category. Slug is the primary key."""

    __tablename__ = "categories"

    slug: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<Category {self.slug!r}>"


class Skill(UUIDMixin, TimestampMixin, Base):
    """A published or draft skill."""

    __tablename__ = "skills"

    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_desc: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), ForeignKey("categories.slug"), nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    author_type: Mapped[str] = mapped_column(
        String(20),
        default="community",
    )
    current_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    install_method: Mapped[str] = mapped_column(
        String(20),
        default="all",
    )
    data_sensitivity: Mapped[str] = mapped_column(
        String(10),
        default="low",
    )
    external_calls: Mapped[bool] = mapped_column(default=False)
    verified: Mapped[bool] = mapped_column(default=False)
    featured: Mapped[bool] = mapped_column(default=False)
    featured_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
    )

    # Denormalized counters
    install_count: Mapped[int] = mapped_column(Integer, default=0)
    fork_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.00"))
    trending_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0.0000"))

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    versions: Mapped[list["SkillVersion"]] = relationship(back_populates="skill", cascade="all, delete-orphan")
    divisions: Mapped[list["SkillDivision"]] = relationship(back_populates="skill", cascade="all, delete-orphan")
    tags: Mapped[list["SkillTag"]] = relationship(back_populates="skill", cascade="all, delete-orphan")
    trigger_phrases: Mapped[list["TriggerPhrase"]] = relationship(back_populates="skill", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Skill {self.slug!r}>"


class SkillVersion(UUIDMixin, Base):
    """Versioned content of a skill."""

    __tablename__ = "skill_versions"

    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    frontmatter: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    submission_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("submissions.id"), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    skill: Mapped["Skill"] = relationship(back_populates="versions")

    def __repr__(self) -> str:
        return f"<SkillVersion {self.skill_id}@{self.version}>"


class SkillDivision(Base):
    """Many-to-many: which divisions can access a skill."""

    __tablename__ = "skill_divisions"

    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    division_slug: Mapped[str] = mapped_column(ForeignKey("divisions.slug"), primary_key=True)

    # Relationships
    skill: Mapped["Skill"] = relationship(back_populates="divisions")

    def __repr__(self) -> str:
        return f"<SkillDivision {self.skill_id}:{self.division_slug}>"


class SkillTag(Base):
    """Tags on a skill."""

    __tablename__ = "skill_tags"

    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    tag: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Relationships
    skill: Mapped["Skill"] = relationship(back_populates="tags")

    def __repr__(self) -> str:
        return f"<SkillTag {self.tag!r}>"


class TriggerPhrase(UUIDMixin, Base):
    """Trigger phrases for a skill."""

    __tablename__ = "trigger_phrases"

    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    phrase: Mapped[str] = mapped_column(String(500), nullable=False)

    # Relationships
    skill: Mapped["Skill"] = relationship(back_populates="trigger_phrases")

    def __repr__(self) -> str:
        return f"<TriggerPhrase {self.phrase!r}>"
