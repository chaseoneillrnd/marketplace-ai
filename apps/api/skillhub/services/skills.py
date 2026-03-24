"""Skills service — query logic for browse, search, and detail."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from opentelemetry import trace
from skillhub_db.models.skill import Skill, SkillDivision, SkillTag
from skillhub_db.models.social import Favorite, Install
from skillhub_db.models.user import User
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("skillhub.services.skills")

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
    with tracer.start_as_current_span("service.skills.browse_skills") as span:
        span.set_attribute("skills.query", q or "")
        span.set_attribute("skills.category", category or "")
        span.set_attribute("skills.sort", sort)
        span.set_attribute("skills.page", page)
        span.set_attribute("skills.per_page", per_page)

        query = (
            db.query(Skill)
            .options(joinedload(Skill.divisions), joinedload(Skill.tags))
            .filter(Skill.status == "published")
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
        span.set_attribute("skills.total_results", total)

        # Sorting
        order_clause = SORT_COLUMNS.get(sort, Skill.trending_score.desc())
        query = query.order_by(order_clause)

        # Pagination
        offset = (page - 1) * per_page
        skills = query.offset(offset).limit(per_page).all()

        # Batch resolve author names (1 query instead of N)
        author_names = _batch_resolve_authors(db, [s.author_id for s in skills])

        # Batch resolve user annotations (2 queries instead of 2*N)
        installed_ids: set[UUID] = set()
        favorited_ids: set[UUID] = set()
        if current_user_id:
            skill_ids = [s.id for s in skills]
            installed_ids = _batch_user_installed(db, current_user_id, skill_ids)
            favorited_ids = _batch_user_favorited(db, current_user_id, skill_ids)

        # Build result dicts
        items: list[dict[str, Any]] = []
        for skill in skills:
            item = _skill_to_summary_dict(skill, author_name=author_names.get(skill.author_id))
            if current_user_id:
                item["user_has_installed"] = skill.id in installed_ids
                item["user_has_favorited"] = skill.id in favorited_ids
            items.append(item)

        return items, total


def get_skill_detail(
    db: Session,
    slug: str,
    current_user_id: UUID | None = None,
) -> dict[str, Any] | None:
    """Get full skill detail by slug. Returns None if not found."""
    with tracer.start_as_current_span("service.skills.get_skill_detail") as span:
        span.set_attribute("skills.slug", slug)

        skill = (
            db.query(Skill)
            .options(
                joinedload(Skill.divisions),
                joinedload(Skill.tags),
                joinedload(Skill.trigger_phrases),
                joinedload(Skill.versions),
            )
            .filter(Skill.slug == slug, Skill.status == "published")
            .first()
        )
        if not skill:
            span.set_attribute("skills.found", False)
            return None

        span.set_attribute("skills.found", True)
        span.set_attribute("skills.skill_id", str(skill.id))

        # Resolve author name
        author_names = _batch_resolve_authors(db, [skill.author_id])
        result = _skill_to_detail_dict(skill, author_name=author_names.get(skill.author_id))

        if current_user_id:
            installed_ids = _batch_user_installed(db, current_user_id, [skill.id])
            favorited_ids = _batch_user_favorited(db, current_user_id, [skill.id])
            result["user_has_installed"] = skill.id in installed_ids
            result["user_has_favorited"] = skill.id in favorited_ids

        return result


def increment_view_count(db: Session, skill_id: UUID) -> None:
    """Increment view count (fire-and-forget)."""
    with tracer.start_as_current_span("service.skills.increment_view_count") as span:
        span.set_attribute("skills.skill_id", str(skill_id))
        db.query(Skill).filter(Skill.id == skill_id).update({Skill.view_count: Skill.view_count + 1})
        db.commit()


def recalculate_trending_scores(db: Session) -> int:
    """Recalculate trending_score for all published skills.

    Formula: (installs*3 + favorites*2 + views*0.1 + avg_rating*10) * decay
    Where decay = 1 / (1 + days_since_published / 30)

    Returns count of updated skills.
    """
    with tracer.start_as_current_span("service.skills.recalculate_trending") as span:
        skills = db.query(Skill).filter(Skill.status == "published").all()
        now = datetime.now(UTC)
        count = 0

        for skill in skills:
            days_since = 0.0
            if skill.published_at:
                delta = now - skill.published_at
                days_since = delta.total_seconds() / 86400

            decay = 1.0 / (1.0 + days_since / 30.0)
            raw = (
                float(skill.install_count) * 3
                + float(skill.favorite_count) * 2
                + float(skill.view_count) * 0.1
                + float(skill.avg_rating) * 10
            )
            score = Decimal(str(round(raw * decay, 4)))

            db.query(Skill).filter(Skill.id == skill.id).update(
                {Skill.trending_score: score}
            )
            count += 1

        db.commit()
        span.set_attribute("skills.updated_count", count)
        return count


def _compute_days_ago(published_at: datetime | None) -> int | None:
    """Compute number of days since publication."""
    if not published_at:
        return None
    delta = datetime.now(UTC) - published_at
    return max(0, delta.days)


def _batch_resolve_authors(db: Session, author_ids: list[UUID]) -> dict[UUID, str]:
    """Batch resolve author UUIDs to names. Returns {author_id: name}."""
    unique_ids = list(set(aid for aid in author_ids if aid))
    if not unique_ids:
        return {}
    users = db.query(User.id, User.name).filter(User.id.in_(unique_ids)).all()
    return {u.id: u.name for u in users}


def _batch_user_installed(db: Session, user_id: UUID, skill_ids: list[UUID]) -> set[UUID]:
    """Batch check which skills the user has installed. Returns set of skill IDs."""
    if not skill_ids:
        return set()
    rows = (
        db.query(Install.skill_id)
        .filter(
            Install.user_id == user_id,
            Install.skill_id.in_(skill_ids),
            Install.uninstalled_at.is_(None),
        )
        .all()
    )
    return {r.skill_id for r in rows}


def _batch_user_favorited(db: Session, user_id: UUID, skill_ids: list[UUID]) -> set[UUID]:
    """Batch check which skills the user has favorited. Returns set of skill IDs."""
    if not skill_ids:
        return set()
    rows = (
        db.query(Favorite.skill_id)
        .filter(
            Favorite.user_id == user_id,
            Favorite.skill_id.in_(skill_ids),
        )
        .all()
    )
    return {r.skill_id for r in rows}


def _skill_to_summary_dict(skill: Skill, *, author_name: str | None = None) -> dict[str, Any]:
    """Convert Skill ORM object to summary dict."""
    return {
        "id": skill.id,
        "slug": skill.slug,
        "name": skill.name,
        "short_desc": skill.short_desc,
        "category": skill.category,
        "divisions": [sd.division_slug for sd in skill.divisions],
        "tags": [st.tag for st in skill.tags],
        "author": author_name,
        "author_type": skill.author_type or "community",
        "version": skill.current_version,
        "install_method": skill.install_method or "all",
        "verified": skill.verified,
        "featured": skill.featured,
        "install_count": skill.install_count,
        "fork_count": skill.fork_count,
        "favorite_count": skill.favorite_count,
        "avg_rating": skill.avg_rating,
        "review_count": skill.review_count,
        "days_ago": _compute_days_ago(skill.published_at),
        "user_has_installed": None,
        "user_has_favorited": None,
    }


def _skill_to_detail_dict(skill: Skill, *, author_name: str | None = None) -> dict[str, Any]:
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
        "author": author_name,
        "author_id": skill.author_id,
        "author_type": skill.author_type or "community",
        "current_version": skill.current_version,
        "install_method": skill.install_method or "all",
        "data_sensitivity": skill.data_sensitivity or "low",
        "external_calls": skill.external_calls,
        "verified": skill.verified,
        "featured": skill.featured,
        "status": skill.status or "draft",
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
