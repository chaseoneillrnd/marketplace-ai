"""Pydantic v2 schemas for the Social domain."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Install ---

class InstallRequest(BaseModel):
    """Body for POST /skills/{slug}/install."""

    method: str = Field(..., pattern=r"^(claude-code|mcp|manual)$")
    version: str


class InstallResponse(BaseModel):
    """Response after installing a skill."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    skill_id: UUID
    user_id: UUID
    version: str
    method: str
    installed_at: datetime


# --- Favorite ---

class FavoriteResponse(BaseModel):
    """Response after favoriting a skill."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    skill_id: UUID
    created_at: datetime


# --- Fork ---

class ForkResponse(BaseModel):
    """Response after forking a skill."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_skill_id: UUID
    forked_skill_id: UUID
    forked_skill_slug: str
    forked_by: UUID


# --- Follow ---

class FollowResponse(BaseModel):
    """Response after following a user."""

    model_config = ConfigDict(from_attributes=True)

    follower_id: UUID
    followed_user_id: UUID
    created_at: datetime


# --- Review ---

class ReviewCreateRequest(BaseModel):
    """Body for POST /skills/{slug}/reviews."""

    rating: int = Field(..., ge=1, le=5)
    body: str = Field(..., min_length=1)


class ReviewUpdateRequest(BaseModel):
    """Body for PATCH /skills/{slug}/reviews/{id}."""

    rating: int | None = Field(default=None, ge=1, le=5)
    body: str | None = Field(default=None, min_length=1)


class ReviewVoteRequest(BaseModel):
    """Body for POST /skills/{slug}/reviews/{id}/vote."""

    vote: str = Field(..., pattern=r"^(helpful|unhelpful)$")


class ReviewResponse(BaseModel):
    """Single review in response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    skill_id: UUID
    user_id: UUID
    rating: int
    body: str
    helpful_count: int
    unhelpful_count: int
    created_at: datetime
    updated_at: datetime


class ReviewListResponse(BaseModel):
    """Paginated list of reviews."""

    items: list[ReviewResponse]
    total: int
    page: int
    per_page: int
    has_more: bool


# --- Comment ---

class CommentCreateRequest(BaseModel):
    """Body for POST /skills/{slug}/comments."""

    body: str = Field(..., min_length=1)


class ReplyCreateRequest(BaseModel):
    """Body for POST /skills/{slug}/comments/{id}/replies."""

    body: str = Field(..., min_length=1)


class ReplyResponse(BaseModel):
    """Single reply in a comment thread."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    comment_id: UUID
    user_id: UUID
    body: str
    deleted_at: datetime | None = None
    created_at: datetime


class CommentResponse(BaseModel):
    """Single comment with nested replies."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    skill_id: UUID
    user_id: UUID
    body: str
    upvote_count: int
    deleted_at: datetime | None = None
    created_at: datetime
    replies: list[ReplyResponse] = []


class CommentListResponse(BaseModel):
    """Paginated list of comments."""

    items: list[CommentResponse]
    total: int
    page: int
    per_page: int
    has_more: bool
