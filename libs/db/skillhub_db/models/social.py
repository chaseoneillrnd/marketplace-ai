"""Social domain models: Install, Fork, Favorite, Follow, Review, Comment."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from skillhub_db.base import Base, UUIDMixin


class Install(UUIDMixin, Base):
    """Record of a skill installation by a user."""

    __tablename__ = "installs"

    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    uninstalled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Install skill={self.skill_id} user={self.user_id}>"


class Fork(UUIDMixin, Base):
    """Record of a skill fork."""

    __tablename__ = "forks"

    original_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    forked_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    forked_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    upstream_version_at_fork: Mapped[str] = mapped_column(String(50), nullable=False)
    forked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Fork {self.original_skill_id} -> {self.forked_skill_id}>"


class Favorite(Base):
    """User's favorited skill. Composite PK."""

    __tablename__ = "favorites"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Favorite user={self.user_id} skill={self.skill_id}>"


class Follow(Base):
    """User following another user. Composite PK."""

    __tablename__ = "follows"

    follower_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    followed_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Follow {self.follower_id} -> {self.followed_user_id}>"


class VoteType(enum.StrEnum):
    HELPFUL = "helpful"
    UNHELPFUL = "unhelpful"


class Review(UUIDMixin, Base):
    """Skill review. UNIQUE on (skill_id, user_id)."""

    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("skill_id", "user_id", name="uq_reviews_skill_user"),)

    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    unhelpful_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    votes: Mapped[list["ReviewVote"]] = relationship(back_populates="review", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Review skill={self.skill_id} rating={self.rating}>"


class ReviewVote(Base):
    """Vote on a review. Composite PK."""

    __tablename__ = "review_votes"

    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    vote: Mapped[VoteType] = mapped_column(Enum(VoteType, native_enum=False, length=10), nullable=False)

    # Relationships
    review: Mapped["Review"] = relationship(back_populates="votes")

    def __repr__(self) -> str:
        return f"<ReviewVote {self.vote}>"


class Comment(UUIDMixin, Base):
    """Discussion comment on a skill. Soft-deletable."""

    __tablename__ = "comments"

    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    upvote_count: Mapped[int] = mapped_column(Integer, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    replies: Mapped[list["Reply"]] = relationship(back_populates="comment", cascade="all, delete-orphan")
    votes: Mapped[list["CommentVote"]] = relationship(back_populates="comment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Comment {self.id}>"


class Reply(UUIDMixin, Base):
    """Reply to a comment."""

    __tablename__ = "replies"

    comment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    comment: Mapped["Comment"] = relationship(back_populates="replies")

    def __repr__(self) -> str:
        return f"<Reply {self.id}>"


class CommentVote(Base):
    """Vote on a comment. Composite PK."""

    __tablename__ = "comment_votes"

    comment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    comment: Mapped["Comment"] = relationship(back_populates="votes")

    def __repr__(self) -> str:
        return f"<CommentVote comment={self.comment_id}>"
