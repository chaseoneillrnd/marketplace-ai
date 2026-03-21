"""Feature flags endpoint."""

from __future__ import annotations

import logging
from typing import Any

import jwt as pyjwt
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from skillhub.dependencies import get_db
from skillhub.schemas.flags import FlagsListResponse
from skillhub.services.flags import get_flags

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["flags"])


def _optional_auth(request: Request) -> dict[str, Any] | None:
    """Extract user from JWT if present, otherwise return None."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    token = auth.removeprefix("Bearer ")
    settings = request.app.state.settings
    try:
        payload: dict[str, Any] = pyjwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except Exception:
        return None
    return payload


@router.get("/flags", response_model=FlagsListResponse)
def list_flags(
    request: Request,
    db: Session = Depends(get_db),
) -> FlagsListResponse:
    """Return all feature flags with division overrides applied."""
    user = _optional_auth(request)
    division = user.get("division") if user else None
    flags = get_flags(db, user_division=division)
    return FlagsListResponse(flags=flags)
