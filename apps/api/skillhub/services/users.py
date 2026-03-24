"""Users service — profile stats and collection queries."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from opentelemetry import trace
from skillhub_db.models.skill import Skill, SkillDivision, SkillTag
from skillhub_db.models.social import Favorite, Fork, Install, Review
from skillhub_db.models.submission import Submission
from skillhub_db.models.user import User
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("skillhub.services.users")


def get_user_profile(
    db: Session,
    user_claims: dict[str, Any],
) -> dict[str, Any]:
    """Build user profile from JWT claims + stats from DB."""
    with tracer.start_as_current_span("service.users.get_user_profile") as span:
        user_id = UUID(user_claims["user_id"])
        span.set_attribute("users.user_id", str(user_id))

        skills_installed = (
            db.query(func.count())
            .select_from(Install)
            .filter(Install.user_id == user_id, Install.uninstalled_at.is_(None))
            .scalar()
            or 0
        )

        skills_submitted = (
            db.query(func.count())
            .select_from(Submission)
            .filter(Submission.submitted_by == user_id)
            .scalar()
            or 0
        )

        reviews_written = (
            db.query(func.count())
            .select_from(Review)
            .filter(Review.user_id == user_id)
            .scalar()
            or 0
        )

        forks_made = (
            db.query(func.count())
            .select_from(Fork)
            .filter(Fork.forked_by == user_id)
            .scalar()
            or 0
        )

        return {
            "user_id": user_claims["user_id"],
            "sub": user_claims.get("sub", ""),
            "name": user_claims.get("name", ""),
            "division": user_claims.get("division", ""),
            "role": user_claims.get("role", ""),
            "is_platform_team": user_claims.get("is_platform_team", False),
            "is_security_team": user_claims.get("is_security_team", False),
            "skills_installed": skills_installed,
            "skills_submitted": skills_submitted,
            "reviews_written": reviews_written,
            "forks_made": forks_made,
        }


def get_user_installs(
    db: Session,
    user_id: UUID,
    *,
    page: int = 1,
    per_page: int = 20,
    include_uninstalled: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    """Get paginated list of skills installed by the user."""
    with tracer.start_as_current_span("service.users.get_user_installs") as span:
        span.set_attribute("users.user_id", str(user_id))
        span.set_attribute("users.page", page)

        query = (
            db.query(Skill)
            .options(joinedload(Skill.divisions), joinedload(Skill.tags))
            .join(Install, Install.skill_id == Skill.id)
            .filter(Install.user_id == user_id)
        )

        if not include_uninstalled:
            query = query.filter(Install.uninstalled_at.is_(None))

        total = query.count()
        span.set_attribute("users.total", total)

        offset = (page - 1) * per_page
        skills = query.order_by(Install.installed_at.desc()).offset(offset).limit(per_page).all()

        author_names = _batch_resolve_authors(db, [s.author_id for s in skills])
        return [
            _skill_to_summary_dict(s, author_name=author_names.get(s.author_id))
            for s in skills
        ], total


def get_user_favorites(
    db: Session,
    user_id: UUID,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Get paginated list of skills favorited by the user."""
    with tracer.start_as_current_span("service.users.get_user_favorites") as span:
        span.set_attribute("users.user_id", str(user_id))
        span.set_attribute("users.page", page)

        query = (
            db.query(Skill)
            .options(joinedload(Skill.divisions), joinedload(Skill.tags))
            .join(Favorite, Favorite.skill_id == Skill.id)
            .filter(Favorite.user_id == user_id)
        )

        total = query.count()
        span.set_attribute("users.total", total)

        offset = (page - 1) * per_page
        skills = query.order_by(Favorite.created_at.desc()).offset(offset).limit(per_page).all()

        author_names = _batch_resolve_authors(db, [s.author_id for s in skills])
        return [
            _skill_to_summary_dict(s, author_name=author_names.get(s.author_id))
            for s in skills
        ], total


def get_user_forks(
    db: Session,
    user_id: UUID,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Get paginated list of skills forked by the user."""
    with tracer.start_as_current_span("service.users.get_user_forks") as span:
        span.set_attribute("users.user_id", str(user_id))
        span.set_attribute("users.page", page)

        query = (
            db.query(Skill)
            .options(joinedload(Skill.divisions), joinedload(Skill.tags))
            .join(Fork, Fork.forked_skill_id == Skill.id)
            .filter(Fork.forked_by == user_id)
        )

        total = query.count()
        span.set_attribute("users.total", total)

        offset = (page - 1) * per_page
        skills = query.order_by(Fork.forked_at.desc()).offset(offset).limit(per_page).all()

        author_names = _batch_resolve_authors(db, [s.author_id for s in skills])
        return [
            _skill_to_summary_dict(s, author_name=author_names.get(s.author_id))
            for s in skills
        ], total


def get_user_submissions(
    db: Session,
    user_id: UUID,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Get paginated list of submissions by the user."""
    with tracer.start_as_current_span("service.users.get_user_submissions") as span:
        span.set_attribute("users.user_id", str(user_id))
        span.set_attribute("users.page", page)

        query = db.query(Submission).filter(Submission.submitted_by == user_id)

        total = query.count()
        span.set_attribute("users.total", total)

        offset = (page - 1) * per_page
        submissions = query.order_by(Submission.created_at.desc()).offset(offset).limit(per_page).all()

        return [_submission_to_dict(s) for s in submissions], total


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


def _skill_to_summary_dict(skill: Skill, *, author_name: str | None = None) -> dict[str, Any]:
    """Convert Skill ORM object to summary dict for user collections."""
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


def _submission_to_dict(submission: Submission) -> dict[str, Any]:
    """Convert Submission ORM object to summary dict."""
    return {
        "id": submission.id,
        "display_id": submission.display_id,
        "name": submission.name,
        "short_desc": submission.short_desc,
        "category": submission.category,
        "status": submission.status.value if hasattr(submission.status, "value") else submission.status,
        "created_at": submission.created_at,
    }
