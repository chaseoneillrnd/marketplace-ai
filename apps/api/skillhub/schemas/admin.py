"""Pydantic v2 schemas for admin endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FeatureSkillRequest(BaseModel):
    featured: bool
    featured_order: int | None = None


class FeatureSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    featured: bool
    featured_order: int | None = None


class DeprecateSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    status: str
    deprecated_at: datetime | None = None


class RemoveSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    status: str


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    actor_id: UUID | None = None
    actor_name: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    metadata: dict | None = None
    ip_address: str | None = None
    created_at: datetime


class AuditLogResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int
    page: int
    per_page: int
    has_more: bool


# --- Admin User Management Schemas (#17) ---


class AdminUserSummary(BaseModel):
    """User summary for admin list endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    name: str
    division: str
    role: str
    is_platform_team: bool
    is_security_team: bool
    created_at: datetime | None = None
    last_login_at: datetime | None = None


class AdminUserListResponse(BaseModel):
    """Paginated response for admin user list."""

    items: list[AdminUserSummary]
    total: int
    page: int
    per_page: int
    has_more: bool


class AdminUserUpdateRequest(BaseModel):
    """Request body for updating a user's role/division/team flags."""

    role: str | None = None
    division: str | None = None
    is_platform_team: bool | None = None
    is_security_team: bool | None = None


class AdminUserUpdateResponse(BaseModel):
    """Response after updating a user."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    name: str
    division: str
    role: str
    is_platform_team: bool
    is_security_team: bool


# --- Admin Submission Queue Schemas (#18) ---


class AdminSubmissionSummary(BaseModel):
    """Submission summary for admin queue view."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_id: str
    name: str
    short_desc: str
    category: str
    status: str
    submitted_by: UUID
    submitted_by_name: str | None = None
    declared_divisions: list[str] = []
    created_at: datetime | None = None


class AdminSubmissionListResponse(BaseModel):
    """Paginated response for admin submission queue."""

    items: list[AdminSubmissionSummary]
    total: int
    page: int
    per_page: int
    has_more: bool
