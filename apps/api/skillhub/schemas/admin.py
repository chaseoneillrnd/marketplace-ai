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
