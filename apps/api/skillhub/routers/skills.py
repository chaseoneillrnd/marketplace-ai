"""Skills browse, detail, and version endpoints."""

from __future__ import annotations

import logging
from typing import Annotated, Any
from uuid import UUID

import jwt as pyjwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_current_user, get_db
from skillhub.schemas.skill import (
    SkillBrowseResponse,
    SkillDetail,
    SkillSummary,
    SkillVersionListItem,
    SkillVersionResponse,
    SortOption,
)
from skillhub.services.skills import browse_skills, get_skill_detail, increment_view_count

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


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


@router.get("", response_model=SkillBrowseResponse)
def list_skills(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    q: str | None = None,
    category: str | None = None,
    divisions: Annotated[list[str], Query()] = [],  # noqa: B006
    sort: SortOption = SortOption.TRENDING,
    install_method: str | None = None,
    verified: bool | None = None,
    featured: bool | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> SkillBrowseResponse:
    """Browse/search skills with filters, sorting, and pagination."""
    user = _optional_auth(request)
    current_user_id: UUID | None = None
    if user and user.get("user_id"):
        current_user_id = UUID(user["user_id"])

    items, total = browse_skills(
        db,
        q=q,
        category=category,
        divisions=divisions if divisions else None,
        sort=sort.value,
        install_method=install_method,
        verified=verified,
        featured=featured,
        page=page,
        per_page=per_page,
        current_user_id=current_user_id,
    )

    skill_summaries = [SkillSummary(**item) for item in items]
    has_more = (page * per_page) < total

    return SkillBrowseResponse(
        items=skill_summaries,
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.get("/{slug}", response_model=SkillDetail)
def get_skill(
    slug: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
) -> SkillDetail:
    """Get full skill detail by slug."""
    user = _optional_auth(request)
    current_user_id: UUID | None = None
    if user and user.get("user_id"):
        current_user_id = UUID(user["user_id"])

    result = get_skill_detail(db, slug, current_user_id=current_user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{slug}' not found",
        )

    # Fire-and-forget view count increment
    skill_id = result["id"]
    background_tasks.add_task(increment_view_count, db, skill_id)

    return SkillDetail(**result)


@router.get("/{slug}/versions", response_model=list[SkillVersionListItem])
def list_versions(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> list[SkillVersionListItem]:
    """List all published versions for a skill. Auth required."""
    from skillhub_db.models.skill import Skill as SkillModel
    from skillhub_db.models.skill import SkillVersion as SkillVersionModel

    skill = db.query(SkillModel).filter(SkillModel.slug == slug).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{slug}' not found",
        )

    versions = (
        db.query(SkillVersionModel)
        .filter(SkillVersionModel.skill_id == skill.id)
        .order_by(SkillVersionModel.published_at.desc())
        .all()
    )

    return [
        SkillVersionListItem(
            id=v.id,
            version=v.version,
            changelog=v.changelog,
            published_at=v.published_at,
        )
        for v in versions
    ]


@router.get("/{slug}/versions/latest", response_model=SkillVersionResponse)
def get_latest_version(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> SkillVersionResponse:
    """Get latest version content for a skill. Auth required."""
    from skillhub_db.models.skill import Skill as SkillModel
    from skillhub_db.models.skill import SkillVersion as SkillVersionModel

    skill = db.query(SkillModel).filter(SkillModel.slug == slug).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{slug}' not found",
        )

    version = (
        db.query(SkillVersionModel)
        .filter(
            SkillVersionModel.skill_id == skill.id,
            SkillVersionModel.version == skill.current_version,
        )
        .first()
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current version not found",
        )

    return SkillVersionResponse(
        id=version.id,
        version=version.version,
        content=version.content,
        frontmatter=version.frontmatter,
        changelog=version.changelog,
        published_at=version.published_at,
    )


@router.get("/{slug}/versions/{version}", response_model=SkillVersionResponse)
def get_version(
    slug: str,
    version: str,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> SkillVersionResponse:
    """Get specific version content for a skill. Auth required."""
    from skillhub_db.models.skill import Skill as SkillModel
    from skillhub_db.models.skill import SkillVersion as SkillVersionModel

    skill = db.query(SkillModel).filter(SkillModel.slug == slug).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{slug}' not found",
        )

    # Resolve "latest" alias
    target_version = skill.current_version if version == "latest" else version

    ver = (
        db.query(SkillVersionModel)
        .filter(
            SkillVersionModel.skill_id == skill.id,
            SkillVersionModel.version == target_version,
        )
        .first()
    )
    if not ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version '{version}' not found",
        )

    return SkillVersionResponse(
        id=ver.id,
        version=ver.version,
        content=ver.content,
        frontmatter=ver.frontmatter,
        changelog=ver.changelog,
        published_at=ver.published_at,
    )
