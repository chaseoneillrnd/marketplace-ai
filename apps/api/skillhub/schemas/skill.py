"""Pydantic v2 schemas for the Skills domain."""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SortOption(enum.StrEnum):
    """Sort options for skill browse."""

    TRENDING = "trending"
    INSTALLS = "installs"
    RATING = "rating"
    NEWEST = "newest"
    UPDATED = "updated"


class SkillSummary(BaseModel):
    """Summary view for browse/search tiles (SkillCard component)."""

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

    # Optional user annotations (only when authenticated)
    user_has_installed: bool | None = None
    user_has_favorited: bool | None = None


class TriggerPhraseResponse(BaseModel):
    """Trigger phrase in skill detail."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phrase: str


class SkillVersionResponse(BaseModel):
    """Version content + frontmatter."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: str
    content: str
    frontmatter: dict | None = None
    changelog: str | None = None
    published_at: datetime
    divisions: list[str] = []


class SkillVersionListItem(BaseModel):
    """Version list item (no content)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: str
    changelog: str | None = None
    published_at: datetime


class SkillDetail(BaseModel):
    """Full detail page data including triggers, notes."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    short_desc: str
    category: str
    divisions: list[str] = []
    tags: list[str] = []
    author: str | None = None
    author_id: UUID
    author_type: str
    current_version: str
    install_method: str
    data_sensitivity: str
    external_calls: bool
    verified: bool
    featured: bool
    status: str
    install_count: int
    fork_count: int
    favorite_count: int
    view_count: int
    review_count: int
    avg_rating: Decimal
    trending_score: Decimal
    published_at: datetime | None = None
    deprecated_at: datetime | None = None
    trigger_phrases: list[TriggerPhraseResponse] = []
    current_version_content: SkillVersionResponse | None = None

    # Optional user annotations
    user_has_installed: bool | None = None
    user_has_favorited: bool | None = None


class SkillBrowseResponse(BaseModel):
    """Paginated browse response."""

    items: list[SkillSummary]
    total: int
    page: int
    per_page: int
    has_more: bool
