"""Admin endpoints — feature, deprecate, remove skills, audit log."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_db, require_platform_team, require_security_team
from skillhub.schemas.admin import (
    AdminUserListResponse,
    AdminUserUpdateRequest,
    AdminUserUpdateResponse,
    AuditLogResponse,
    DeprecateSkillResponse,
    FeatureSkillRequest,
    FeatureSkillResponse,
    RemoveSkillResponse,
)
from skillhub.services.admin import (
    deprecate_skill,
    feature_skill,
    list_users,
    query_audit_log,
    remove_skill,
    update_user,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/skills/{slug}/feature", response_model=FeatureSkillResponse)
def feature_skill_endpoint(
    slug: str,
    body: FeatureSkillRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> FeatureSkillResponse:
    """Set featured status on a skill. Platform Team only."""
    try:
        result = feature_skill(
            db, slug=slug, featured=body.featured, featured_order=body.featured_order,
            actor_id=current_user.get("user_id"),
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return FeatureSkillResponse(**result)


@router.post("/skills/{slug}/deprecate", response_model=DeprecateSkillResponse)
def deprecate_skill_endpoint(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> DeprecateSkillResponse:
    """Deprecate a skill. Platform Team only."""
    try:
        result = deprecate_skill(db, slug=slug, actor_id=current_user.get("user_id"))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return DeprecateSkillResponse(**result)


@router.delete("/skills/{slug}", response_model=RemoveSkillResponse)
def remove_skill_endpoint(
    slug: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_security_team)],
) -> RemoveSkillResponse:
    """Soft-remove a skill. Security Team only. Writes audit log."""
    actor_id = current_user.get("user_id", "")
    ip_address = request.client.host if request.client else None
    try:
        result = remove_skill(db, slug=slug, actor_id=actor_id, ip_address=ip_address)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return RemoveSkillResponse(**result)


@router.post("/recalculate-trending")
def recalculate_trending_endpoint(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> dict[str, Any]:
    """Recalculate trending scores for all published skills. Platform Team only."""
    from skillhub.services.skills import recalculate_trending_scores

    count = recalculate_trending_scores(db)
    return {"updated": count}


@router.get("/audit-log", response_model=AuditLogResponse)
def list_audit_log(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
    event_type: str | None = None,
    actor_id: str | None = None,
    target_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> AuditLogResponse:
    """Query audit log. Platform Team only."""
    items, total = query_audit_log(
        db,
        event_type=event_type,
        actor_id=actor_id,
        target_id=target_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )
    return AuditLogResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )


# --- Admin User Management (#17) ---


@router.get("/users", response_model=AdminUserListResponse)
def list_users_endpoint(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
    division: str | None = None,
    role: str | None = None,
    is_platform_team: bool | None = None,
    is_security_team: bool | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> AdminUserListResponse:
    """List users with optional filters. Platform Team only."""
    items, total = list_users(
        db,
        division=division,
        role=role,
        is_platform_team=is_platform_team,
        is_security_team=is_security_team,
        page=page,
        per_page=per_page,
    )
    return AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )


@router.patch("/users/{user_id}", response_model=AdminUserUpdateResponse)
def update_user_endpoint(
    user_id: str,
    body: AdminUserUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> AdminUserUpdateResponse:
    """Update a user's role, division, or team flags. Platform Team only."""
    try:
        result = update_user(
            db,
            user_id=user_id,
            updates=body.model_dump(exclude_unset=True),
            actor_id=current_user.get("user_id"),
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return AdminUserUpdateResponse(**result)

# NOTE: Admin submission queue (GET /api/v1/admin/submissions) already exists
# in skillhub/routers/submissions.py as list_submissions_admin(). The service
# function list_all_submissions in services/admin.py is available for reuse.
