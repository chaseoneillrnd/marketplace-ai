"""Users service — profile stats and collection queries."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from skillhub_db.models.skill import Skill, SkillDivision, SkillTag
from skillhub_db.models.social import Favorite, Fork, Install, Review
from skillhub_db.models.submission import Submission
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)


def get_user_profile(
    db: Session,
    user_claims: dict[str, Any],
) -> dict[str, Any]:
    """Build user profile from JWT claims + stats from DB."""
    user_id = UUID(user_claims["user_id"])

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
    query = (
        db.query(Skill)
        .options(joinedload(Skill.divisions), joinedload(Skill.tags))
        .join(Install, Install.skill_id == Skill.id)
        .filter(Install.user_id == user_id)
    )

    if not include_uninstalled:
        query = query.filter(Install.uninstalled_at.is_(None))

    total = query.count()
    offset = (page - 1) * per_page
    skills = query.order_by(Install.installed_at.desc()).offset(offset).limit(per_page).unique().all()

    return [_skill_to_summary_dict(s) for s in skills], total


def get_user_favorites(
    db: Session,
    user_id: UUID,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Get paginated list of skills favorited by the user."""
    query = (
        db.query(Skill)
        .options(joinedload(Skill.divisions), joinedload(Skill.tags))
        .join(Favorite, Favorite.skill_id == Skill.id)
        .filter(Favorite.user_id == user_id)
    )

    total = query.count()
    offset = (page - 1) * per_page
    skills = query.order_by(Favorite.created_at.desc()).offset(offset).limit(per_page).unique().all()

    return [_skill_to_summary_dict(s) for s in skills], total


def get_user_forks(
    db: Session,
    user_id: UUID,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Get paginated list of skills forked by the user."""
    query = (
        db.query(Skill)
        .options(joinedload(Skill.divisions), joinedload(Skill.tags))
        .join(Fork, Fork.forked_skill_id == Skill.id)
        .filter(Fork.forked_by == user_id)
    )

    total = query.count()
    offset = (page - 1) * per_page
    skills = query.order_by(Fork.forked_at.desc()).offset(offset).limit(per_page).unique().all()

    return [_skill_to_summary_dict(s) for s in skills], total


def get_user_submissions(
    db: Session,
    user_id: UUID,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Get paginated list of submissions by the user."""
    query = db.query(Submission).filter(Submission.submitted_by == user_id)

    total = query.count()
    offset = (page - 1) * per_page
    submissions = query.order_by(Submission.created_at.desc()).offset(offset).limit(per_page).all()

    return [_submission_to_dict(s) for s in submissions], total


def _skill_to_summary_dict(skill: Skill) -> dict[str, Any]:
    """Convert Skill ORM object to summary dict for user collections."""
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
