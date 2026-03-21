"""Pydantic v2 schemas for feature flags."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    enabled: bool
    description: str | None = None


class FlagsListResponse(BaseModel):
    flags: dict[str, bool]  # key -> effective enabled value
