"""Skills service — query logic for browse, search, and detail."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from skillhub_db.models.skill import Skill, SkillDivision, SkillStatus, SkillTag
from skillhub_db.models.social import Favorite, Install
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

# Sort column mapping
SORT_COLUMNS = {
    "trending": Skill.trending_score.desc(),
    "installs": Skill.install_count.desc(),
    "rating": Skill.avg_rating.desc(),
    "newest": Skill.published_at.desc().nulls_last(),
    "updated": Skill.updated_at.desc(),
}


def browse_skills(
    db: Session,
    *,
    q: str | None = None,
    category: str | None = None,
    divisions: list[str] | None = None,
    sort: str = "trending",
    install_method: str | None = None,
    verified: bool | None = None,
    featured: bool | None = None,
    page: int = 1,
    per_page: int = 20,
    current_user_id: UUID | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Browse/search skills with filtering, sorting, and pagination.

    Returns (items, total_count).
    """
    query = (
        db.query(Skill)
        .options(joinedload(Skill.divisions), joinedload(Skill.tags))
        .filter(Skill.status == SkillStatus.PUBLISHED)
    )

    # Text search
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Skill.name.ilike(pattern),
                Skill.short_desc.ilike(pattern),
                Skill.id.in_(db.query(SkillTag.skill_id).filter(SkillTag.tag.ilike(pattern))),
            )
        )

    # Filters
    if category:
        query = query.filter(Skill.category == category)

    if divisions:
        query = query.filter(
            Skill.id.in_(db.query(SkillDivision.skill_id).filter(SkillDivision.division_slug.in_(divisions)))
        )

    if install_method:
        query = query.filter(Skill.install_method == install_method)

    if verified is not None:
        query = query.filter(Skill.verified == verified)

    if featured is not None:
        query = query.filter(Skill.featured == featured)

    # Count before pagination
    total = query.count()

    # Sorting
    order_clause = SORT_COLUMNS.get(sort, Skill.trending_score.desc())
    query = query.order_by(order_clause)

    # Pagination
    offset = (page - 1) * per_page
    skills = query.offset(offset).limit(per_page).unique().all()

    # Build result dicts with user annotations
    items: list[dict[str, Any]] = []
    for skill in skills:
        item = _skill_to_summary_dict(skill)
        if current_user_id:
            item["user_has_installed"] = _user_has_installed(db, current_user_id, skill.id)
            item["user_has_favorited"] = _user_has_favorited(db, current_user_id, skill.id)
        items.append(item)

    return items, total


def get_skill_detail(
    db: Session,
    slug: str,
    current_user_id: UUID | None = None,
) -> dict[str, Any] | None:
    """Get full skill detail by slug. Returns None if not found."""
    skill = (
        db.query(Skill)
        .options(
            joinedload(Skill.divisions),
            joinedload(Skill.tags),
            joinedload(Skill.trigger_phrases),
            joinedload(Skill.versions),
        )
        .filter(Skill.slug == slug)
        .first()
    )
    if not skill:
        return None

    result = _skill_to_detail_dict(skill)

    if current_user_id:
        result["user_has_installed"] = _user_has_installed(db, current_user_id, skill.id)
        result["user_has_favorited"] = _user_has_favorited(db, current_user_id, skill.id)

    return result


def increment_view_count(db: Session, skill_id: UUID) -> None:
    """Increment view count (fire-and-forget)."""
    db.query(Skill).filter(Skill.id == skill_id).update({Skill.view_count: Skill.view_count + 1})
    db.commit()


def _skill_to_summary_dict(skill: Skill) -> dict[str, Any]:
    """Convert Skill ORM object to summary dict."""
    return {
        "id": skill.id,
        "slug": skill.slug,
        "name": skill.name,
        "short_desc": skill.short_desc,
        "category": skill.category,
        "divisions": [sd.division_slug for sd in skill.divisions],
        "tags": [st.tag for st in skill.tags],
        "author": None,
        "author_type": skill.author_type.value if skill.author_type else "community",
        "version": skill.current_version,
        "install_method": skill.install_method.value if skill.install_method else "all",
        "verified": skill.verified,
        "featured": skill.featured,
        "install_count": skill.install_count,
        "fork_count": skill.fork_count,
        "favorite_count": skill.favorite_count,
        "avg_rating": skill.avg_rating,
        "rating_count": skill.review_count,
        "days_ago": None,
        "user_has_installed": None,
        "user_has_favorited": None,
    }


def _skill_to_detail_dict(skill: Skill) -> dict[str, Any]:
    """Convert Skill ORM object to full detail dict."""
    # Find the current version content
    current_version_content = None
    for v in skill.versions:
        if v.version == skill.current_version:
            current_version_content = {
                "id": v.id,
                "version": v.version,
                "content": v.content,
                "frontmatter": v.frontmatter,
                "changelog": v.changelog,
                "published_at": v.published_at,
            }
            break

    return {
        "id": skill.id,
        "slug": skill.slug,
        "name": skill.name,
        "short_desc": skill.short_desc,
        "category": skill.category,
        "divisions": [sd.division_slug for sd in skill.divisions],
        "tags": [st.tag for st in skill.tags],
        "author": None,
        "author_id": skill.author_id,
        "author_type": skill.author_type.value if skill.author_type else "community",
        "current_version": skill.current_version,
        "install_method": skill.install_method.value if skill.install_method else "all",
        "data_sensitivity": skill.data_sensitivity.value if skill.data_sensitivity else "low",
        "external_calls": skill.external_calls,
        "verified": skill.verified,
        "featured": skill.featured,
        "status": skill.status.value if skill.status else "draft",
        "install_count": skill.install_count,
        "fork_count": skill.fork_count,
        "favorite_count": skill.favorite_count,
        "view_count": skill.view_count,
        "review_count": skill.review_count,
        "avg_rating": skill.avg_rating,
        "trending_score": skill.trending_score,
        "published_at": skill.published_at,
        "deprecated_at": skill.deprecated_at,
        "trigger_phrases": [{"id": tp.id, "phrase": tp.phrase} for tp in skill.trigger_phrases],
        "current_version_content": current_version_content,
        "user_has_installed": None,
        "user_has_favorited": None,
    }


def _user_has_installed(db: Session, user_id: UUID, skill_id: UUID) -> bool:
    """Check if user has an active install for the skill."""
    return (
        db.query(func.count())
        .select_from(Install)
        .filter(
            Install.skill_id == skill_id,
            Install.user_id == user_id,
            Install.uninstalled_at.is_(None),
        )
        .scalar()
        or 0
    ) > 0


def _user_has_favorited(db: Session, user_id: UUID, skill_id: UUID) -> bool:
    """Check if user has favorited the skill."""
    return (
        db.query(func.count())
        .select_from(Favorite)
        .filter(
            Favorite.skill_id == skill_id,
            Favorite.user_id == user_id,
        )
        .scalar()
        or 0
    ) > 0
