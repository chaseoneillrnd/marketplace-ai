"""Pydantic v2 schemas for feature flags."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FlagCreateRequest(BaseModel):
    """Body for POST /admin/flags."""

    key: str = Field(..., min_length=1, max_length=100)
    enabled: bool = True
    description: str | None = None
    division_overrides: dict[str, bool] | None = None


class FlagUpdateRequest(BaseModel):
    """Body for PATCH /admin/flags/{key}."""

    enabled: bool | None = None
    description: str | None = None
    division_overrides: dict[str, bool] | None = None


class FlagDetailResponse(BaseModel):
    """Full flag detail including overrides."""

    model_config = ConfigDict(from_attributes=True)

    key: str
    enabled: bool
    description: str | None = None
    division_overrides: dict[str, bool] | None = None


class FlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    enabled: bool
    description: str | None = None


class FlagsListResponse(BaseModel):
    flags: dict[str, bool]  # key -> effective enabled value
