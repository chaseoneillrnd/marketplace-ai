"""Admin endpoints — feature, deprecate, remove skills, audit log."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from skillhub.dependencies import get_db, require_platform_team, require_security_team
from skillhub.schemas.admin import (
    AuditLogResponse,
    DeprecateSkillResponse,
    FeatureSkillRequest,
    FeatureSkillResponse,
    RemoveSkillResponse,
)
from skillhub.services.admin import (
    deprecate_skill,
    feature_skill,
    query_audit_log,
    remove_skill,
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
    result = feature_skill(
        db, slug=slug, featured=body.featured, featured_order=body.featured_order
    )
    return FeatureSkillResponse(**result)


@router.post("/skills/{slug}/deprecate", response_model=DeprecateSkillResponse)
def deprecate_skill_endpoint(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> DeprecateSkillResponse:
    """Deprecate a skill. Platform Team only."""
    result = deprecate_skill(db, slug=slug)
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
    result = remove_skill(db, slug=slug, actor_id=actor_id, ip_address=ip_address)
    return RemoveSkillResponse(**result)


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
