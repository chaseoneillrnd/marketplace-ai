"""Roadmap and changelog endpoints."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_db, require_platform_team, require_security_team
from skillhub.schemas.feedback import (
    ChangelogEntry,
    ChangelogResponse,
    PlatformUpdateCreate,
    PlatformUpdateListResponse,
    PlatformUpdateResponse,
    ShipRequest,
)
from skillhub.services.roadmap import (
    create_update,
    delete_update,
    list_updates,
    ship_update,
    update_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["roadmap"])


@router.get("/api/v1/admin/platform-updates", response_model=PlatformUpdateListResponse)
def list_platform_updates(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
    update_status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> PlatformUpdateListResponse:
    """List platform updates. Admin only."""
    items, total = list_updates(
        db, status=update_status_filter, page=page, per_page=per_page
    )
    return PlatformUpdateListResponse(
        items=[PlatformUpdateResponse(**i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )


@router.post(
    "/api/v1/admin/platform-updates",
    response_model=PlatformUpdateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_platform_update(
    body: PlatformUpdateCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> PlatformUpdateResponse:
    """Create a platform update. Admin only."""
    result = create_update(
        db,
        title=body.title,
        body=body.body,
        author_id=current_user["user_id"],
        status=body.status,
        target_quarter=body.target_quarter,
    )
    return PlatformUpdateResponse(**result)


@router.patch("/api/v1/admin/platform-updates/{update_id}", response_model=PlatformUpdateResponse)
def patch_platform_update(
    update_id: str,
    body: dict[str, str],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> PlatformUpdateResponse:
    """Update platform update status. Admin only."""
    new_status = body.get("status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="status is required",
        )
    try:
        result = update_status(
            db,
            update_id=update_id,
            new_status=new_status,
            actor_id=current_user["user_id"],
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return PlatformUpdateResponse(**result)


@router.post("/api/v1/admin/platform-updates/{update_id}/ship", response_model=PlatformUpdateResponse)
def ship_platform_update(
    update_id: str,
    body: ShipRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> PlatformUpdateResponse:
    """Ship a platform update. Admin only."""
    try:
        result = ship_update(
            db,
            update_id=update_id,
            version_tag=body.version_tag,
            changelog_body=body.changelog_body,
            actor_id=current_user["user_id"],
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return PlatformUpdateResponse(**result)


@router.delete("/api/v1/admin/platform-updates/{update_id}", response_model=PlatformUpdateResponse)
def delete_platform_update(
    update_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_security_team)],
) -> PlatformUpdateResponse:
    """Delete (soft) a platform update. Security team only."""
    try:
        result = delete_update(
            db,
            update_id=update_id,
            actor_id=current_user["user_id"],
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return PlatformUpdateResponse(**result)


@router.get("/api/v1/changelog", response_model=ChangelogResponse)
def get_changelog(
    db: Annotated[Session, Depends(get_db)],
) -> ChangelogResponse:
    """Public changelog — no auth required. Returns shipped items."""
    items, _ = list_updates(db, status="shipped", page=1, per_page=100)
    changelog_items = []
    for item in items:
        changelog_items.append(
            ChangelogEntry(
                id=item["id"],
                title=item["title"],
                body=item["body"],
                version_tag=None,
                shipped_at=item["shipped_at"],
            )
        )
    return ChangelogResponse(items=changelog_items)
