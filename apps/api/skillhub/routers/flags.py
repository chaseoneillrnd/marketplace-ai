"""Feature flags endpoints — read and admin CRUD."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_db, get_optional_user, require_platform_team
from skillhub.schemas.flags import (
    FlagCreateRequest,
    FlagDetailResponse,
    FlagUpdateRequest,
    FlagsListResponse,
)
from skillhub.services.flags import create_flag, delete_flag, get_flags, update_flag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["flags"])


@router.get("/flags", response_model=FlagsListResponse)
def list_flags(
    request: Request,
    db: Session = Depends(get_db),
) -> FlagsListResponse:
    """Return all feature flags with division overrides applied."""
    user = get_optional_user(request)
    division = user.get("division") if user else None
    flags = get_flags(db, user_division=division)
    return FlagsListResponse(flags=flags)


@router.post("/admin/flags", response_model=FlagDetailResponse, status_code=status.HTTP_201_CREATED)
def post_flag(
    body: FlagCreateRequest,
    _admin: Annotated[dict[str, Any], Depends(require_platform_team)],
    db: Annotated[Session, Depends(get_db)],
) -> FlagDetailResponse:
    """Create a new feature flag. Platform team only."""
    try:
        result = create_flag(db, body.key, enabled=body.enabled, description=body.description, division_overrides=body.division_overrides)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err)) from err
    return FlagDetailResponse(**result)


@router.patch("/admin/flags/{key}", response_model=FlagDetailResponse)
def patch_flag(
    key: str,
    body: FlagUpdateRequest,
    _admin: Annotated[dict[str, Any], Depends(require_platform_team)],
    db: Annotated[Session, Depends(get_db)],
) -> FlagDetailResponse:
    """Update an existing feature flag. Platform team only."""
    try:
        result = update_flag(db, key, enabled=body.enabled, description=body.description, division_overrides=body.division_overrides)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return FlagDetailResponse(**result)


@router.delete("/admin/flags/{key}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def remove_flag(
    key: str,
    _admin: Annotated[dict[str, Any], Depends(require_platform_team)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a feature flag. Platform team only."""
    try:
        delete_flag(db, key)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
