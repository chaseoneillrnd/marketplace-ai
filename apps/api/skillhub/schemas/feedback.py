"""Pydantic v2 schemas for feedback and roadmap/changelog endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Feedback Schemas ---


class FeedbackCreate(BaseModel):
    """Request body for creating feedback."""

    category: str = Field(..., pattern=r"^(feature_request|bug_report|praise|complaint)$")
    body: str = Field(..., min_length=20, max_length=500)
    skill_id: UUID | None = None
    allow_contact: bool = False


class FeedbackResponse(BaseModel):
    """Single feedback item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    skill_id: UUID | None = None
    category: str
    body: str
    sentiment: str
    upvotes: int
    status: str
    allow_contact: bool
    created_at: datetime
    # Joined display fields — populated by admin list endpoint only
    skill_name: str | None = None
    user_display_name: str | None = None


class FeedbackListResponse(BaseModel):
    """Paginated feedback list."""

    items: list[FeedbackResponse]
    total: int
    page: int
    per_page: int
    has_more: bool


# --- Platform Updates / Roadmap Schemas ---


class PlatformUpdateCreate(BaseModel):
    """Request body for creating a platform update."""

    title: str = Field(..., min_length=3, max_length=255)
    body: str = Field(..., min_length=10)
    status: str = Field(default="planned", pattern=r"^(planned|in_progress|shipped|cancelled)$")
    target_quarter: str | None = Field(default=None, max_length=10)


class PlatformUpdateResponse(BaseModel):
    """Single platform update item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    body: str
    status: str
    author_id: UUID
    target_quarter: str | None = None
    linked_feedback_ids: list = []
    shipped_at: datetime | None = None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class PlatformUpdateListResponse(BaseModel):
    """Paginated platform updates list."""

    items: list[PlatformUpdateResponse]
    total: int
    page: int
    per_page: int
    has_more: bool


class ShipRequest(BaseModel):
    """Request body for shipping a platform update."""

    version_tag: str = Field(..., min_length=1, max_length=50)
    changelog_body: str = Field(..., min_length=10)


class ChangelogEntry(BaseModel):
    """A shipped changelog entry for public consumption."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    body: str
    version_tag: str | None = None
    shipped_at: datetime | None = None


class ChangelogResponse(BaseModel):
    """Public changelog list."""

    items: list[ChangelogEntry]
