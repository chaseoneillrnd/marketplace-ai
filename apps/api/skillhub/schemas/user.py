"""Pydantic v2 schemas for the Users domain."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    """Full user profile from JWT claims + DB stats."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    sub: str
    name: str
    division: str
    role: str
    is_platform_team: bool
    is_security_team: bool
    skills_installed: int
    skills_submitted: int
    reviews_written: int
    forks_made: int


class UserSkillSummary(BaseModel):
    """Skill summary for user collection endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    short_desc: str
    category: str
    divisions: list[str] = []
    tags: list[str] = []
    author: str | None = None
    author_type: str
    version: str
    install_method: str
    verified: bool
    featured: bool
    install_count: int
    fork_count: int
    favorite_count: int
    avg_rating: Decimal
    review_count: int
    days_ago: int | None = None
    user_has_installed: bool | None = None
    user_has_favorited: bool | None = None


class UserSkillCollectionResponse(BaseModel):
    """Paginated response for user skill collections."""

    items: list[UserSkillSummary]
    total: int
    page: int
    per_page: int
    has_more: bool


class SubmissionSummary(BaseModel):
    """Submission summary for user submissions list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_id: str
    name: str
    short_desc: str
    category: str
    status: str
    created_at: datetime | str


class UserSubmissionsResponse(BaseModel):
    """Paginated response for user submissions."""

    items: list[SubmissionSummary]
    total: int
    page: int
    per_page: int
    has_more: bool
