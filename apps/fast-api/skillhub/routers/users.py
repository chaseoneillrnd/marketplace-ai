"""Users profile and personal collection endpoints."""

from __future__ import annotations

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from skillhub.dependencies import get_current_user, get_db
from skillhub.schemas.user import (
    SubmissionSummary,
    UserProfile,
    UserSkillCollectionResponse,
    UserSkillSummary,
    UserSubmissionsResponse,
)
from skillhub.services.users import (
    get_user_favorites,
    get_user_forks,
    get_user_installs,
    get_user_profile,
    get_user_submissions,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def get_me(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfile:
    """Get current user profile with stats."""
    profile = get_user_profile(db, current_user)
    return UserProfile(**profile)


@router.get("/me/installs", response_model=UserSkillCollectionResponse)
def list_installs(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    include_uninstalled: bool = False,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> UserSkillCollectionResponse:
    """Get current user's installed skills."""
    user_id = UUID(current_user["user_id"])
    items, total = get_user_installs(
        db,
        user_id,
        page=page,
        per_page=per_page,
        include_uninstalled=include_uninstalled,
    )
    has_more = (page * per_page) < total
    return UserSkillCollectionResponse(
        items=[UserSkillSummary(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.get("/me/favorites", response_model=UserSkillCollectionResponse)
def list_favorites(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> UserSkillCollectionResponse:
    """Get current user's favorited skills."""
    user_id = UUID(current_user["user_id"])
    items, total = get_user_favorites(db, user_id, page=page, per_page=per_page)
    has_more = (page * per_page) < total
    return UserSkillCollectionResponse(
        items=[UserSkillSummary(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.get("/me/forks", response_model=UserSkillCollectionResponse)
def list_forks(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> UserSkillCollectionResponse:
    """Get current user's forked skills."""
    user_id = UUID(current_user["user_id"])
    items, total = get_user_forks(db, user_id, page=page, per_page=per_page)
    has_more = (page * per_page) < total
    return UserSkillCollectionResponse(
        items=[UserSkillSummary(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.get("/me/submissions", response_model=UserSubmissionsResponse)
def list_submissions(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> UserSubmissionsResponse:
    """Get current user's skill submissions with status."""
    user_id = UUID(current_user["user_id"])
    items, total = get_user_submissions(db, user_id, page=page, per_page=per_page)
    has_more = (page * per_page) < total
    return UserSubmissionsResponse(
        items=[SubmissionSummary(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )
