"""Submission pipeline models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from skillhub_db.base import Base, TimestampMixin, UUIDMixin


class SubmissionStatus(enum.StrEnum):
    SUBMITTED = "submitted"
    GATE1_PASSED = "gate1_passed"
    GATE1_FAILED = "gate1_failed"
    GATE2_PASSED = "gate2_passed"
    GATE2_FLAGGED = "gate2_flagged"
    GATE2_FAILED = "gate2_failed"
    GATE3_CHANGES_REQUESTED = "gate3_changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class GateResult(enum.StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    FLAGGED = "flagged"


class AccessRequestStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class Submission(UUIDMixin, TimestampMixin, Base):
    """Skill submission through the pipeline."""

    __tablename__ = "submissions"

    display_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"), nullable=True)
    submitted_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_desc: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    declared_divisions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    division_justification: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, native_enum=False, length=30),
        default=SubmissionStatus.SUBMITTED,
    )

    def __repr__(self) -> str:
        return f"<Submission {self.display_id}>"


class SubmissionGateResult(UUIDMixin, Base):
    """Result of a gate check on a submission."""

    __tablename__ = "submission_gate_results"

    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    gate: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[GateResult] = mapped_column(Enum(GateResult, native_enum=False, length=10), nullable=False)
    findings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<SubmissionGateResult gate={self.gate} result={self.result}>"


class DivisionAccessRequest(UUIDMixin, TimestampMixin, Base):
    """Request from a user to access a skill in a different division."""

    __tablename__ = "division_access_requests"

    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    user_division: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AccessRequestStatus] = mapped_column(
        Enum(AccessRequestStatus, native_enum=False, length=10),
        default=AccessRequestStatus.PENDING,
    )

    def __repr__(self) -> str:
        return f"<DivisionAccessRequest {self.id}>"
