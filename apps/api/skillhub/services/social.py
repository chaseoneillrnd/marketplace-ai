"""Social service — install, favorite, fork, follow actions with audit logging."""

from __future__ import annotations

import logging
import uuid
from typing import Any
from uuid import UUID

from skillhub_db.models.audit import AuditLog
from skillhub_db.models.skill import Skill, SkillDivision, SkillStatus
from skillhub_db.models.social import Favorite, Follow, Fork, Install
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _write_audit(
    db: Session,
    *,
    event_type: str,
    actor_id: UUID,
    target_type: str,
    target_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append a row to the audit log."""
    entry = AuditLog(
        id=uuid.uuid4(),
        event_type=event_type,
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
        metadata_=metadata,
    )
    db.add(entry)


def get_skill_or_404(db: Session, slug: str) -> Skill:
    """Look up a skill by slug; raise ValueError if not found."""
    skill = db.query(Skill).filter(Skill.slug == slug).first()
    if not skill:
        raise ValueError(f"Skill '{slug}' not found")
    return skill


def check_division_authorization(
    db: Session, skill_id: UUID, user_division: str
) -> bool:
    """Return True if the user's division is authorized for this skill."""
    return (
        db.query(func.count())
        .select_from(SkillDivision)
        .filter(
            SkillDivision.skill_id == skill_id,
            SkillDivision.division_slug == user_division,
        )
        .scalar()
        or 0
    ) > 0


def install_skill(
    db: Session,
    slug: str,
    user_id: UUID,
    user_division: str,
    method: str,
    version: str,
) -> dict[str, Any]:
    """Install a skill. Checks division authorization.

    Returns install dict on success.
    Raises ValueError for not found, PermissionError for division restriction.
    """
    skill = get_skill_or_404(db, slug)

    # Check division authorization
    has_divisions = (
        db.query(func.count())
        .select_from(SkillDivision)
        .filter(SkillDivision.skill_id == skill.id)
        .scalar()
        or 0
    )
    if has_divisions > 0 and not check_division_authorization(
        db, skill.id, user_division
    ):
        raise PermissionError("division_restricted")

    install = Install(
        id=uuid.uuid4(),
        skill_id=skill.id,
        user_id=user_id,
        version=version,
        method=method,
    )
    db.add(install)

    # Atomic counter increment
    db.query(Skill).filter(Skill.id == skill.id).update(
        {Skill.install_count: Skill.install_count + 1}
    )

    _write_audit(
        db,
        event_type="skill.installed",
        actor_id=user_id,
        target_type="skill",
        target_id=str(skill.id),
        metadata={"method": method, "version": version, "slug": slug},
    )

    db.commit()
    db.refresh(install)

    return {
        "id": install.id,
        "skill_id": install.skill_id,
        "user_id": install.user_id,
        "version": install.version,
        "method": install.method,
        "installed_at": install.installed_at,
    }


def uninstall_skill(
    db: Session,
    slug: str,
    user_id: UUID,
) -> None:
    """Uninstall a skill (soft delete). Raises ValueError if not found."""
    skill = get_skill_or_404(db, slug)

    install = (
        db.query(Install)
        .filter(
            Install.skill_id == skill.id,
            Install.user_id == user_id,
            Install.uninstalled_at.is_(None),
        )
        .first()
    )
    if not install:
        raise ValueError("No active install found")

    install.uninstalled_at = func.now()

    _write_audit(
        db,
        event_type="skill.uninstalled",
        actor_id=user_id,
        target_type="skill",
        target_id=str(skill.id),
        metadata={"slug": slug},
    )

    db.commit()


def favorite_skill(
    db: Session,
    slug: str,
    user_id: UUID,
) -> dict[str, Any]:
    """Favorite a skill (upsert — idempotent). Returns favorite dict."""
    skill = get_skill_or_404(db, slug)

    existing = (
        db.query(Favorite)
        .filter(Favorite.skill_id == skill.id, Favorite.user_id == user_id)
        .first()
    )
    if existing:
        return {
            "user_id": existing.user_id,
            "skill_id": existing.skill_id,
            "created_at": existing.created_at,
        }

    fav = Favorite(user_id=user_id, skill_id=skill.id)
    db.add(fav)

    db.query(Skill).filter(Skill.id == skill.id).update(
        {Skill.favorite_count: Skill.favorite_count + 1}
    )

    _write_audit(
        db,
        event_type="skill.favorited",
        actor_id=user_id,
        target_type="skill",
        target_id=str(skill.id),
        metadata={"slug": slug},
    )

    db.commit()
    db.refresh(fav)

    return {
        "user_id": fav.user_id,
        "skill_id": fav.skill_id,
        "created_at": fav.created_at,
    }


def unfavorite_skill(
    db: Session,
    slug: str,
    user_id: UUID,
) -> None:
    """Remove a favorite. Raises ValueError if not found."""
    skill = get_skill_or_404(db, slug)

    fav = (
        db.query(Favorite)
        .filter(Favorite.skill_id == skill.id, Favorite.user_id == user_id)
        .first()
    )
    if not fav:
        raise ValueError("Not favorited")

    db.delete(fav)

    db.query(Skill).filter(Skill.id == skill.id).update(
        {Skill.favorite_count: Skill.favorite_count - 1}
    )

    _write_audit(
        db,
        event_type="skill.unfavorited",
        actor_id=user_id,
        target_type="skill",
        target_id=str(skill.id),
        metadata={"slug": slug},
    )

    db.commit()


def fork_skill(
    db: Session,
    slug: str,
    user_id: UUID,
) -> dict[str, Any]:
    """Fork a skill. Creates new Skill row + Fork row.

    Returns dict with forked skill info.
    """
    original = get_skill_or_404(db, slug)

    # Generate a unique slug for the fork
    fork_slug = f"{slug}-fork-{uuid.uuid4().hex[:8]}"

    forked_skill = Skill(
        id=uuid.uuid4(),
        slug=fork_slug,
        name=f"{original.name} (Fork)",
        short_desc=original.short_desc,
        category=original.category,
        author_id=user_id,
        status=SkillStatus.DRAFT,
        current_version=original.current_version,
        install_method=original.install_method,
        data_sensitivity=original.data_sensitivity,
        external_calls=original.external_calls,
    )
    db.add(forked_skill)

    fork_record = Fork(
        id=uuid.uuid4(),
        original_skill_id=original.id,
        forked_skill_id=forked_skill.id,
        forked_by=user_id,
        upstream_version_at_fork=original.current_version,
    )
    db.add(fork_record)

    # Increment fork count on original
    db.query(Skill).filter(Skill.id == original.id).update(
        {Skill.fork_count: Skill.fork_count + 1}
    )

    _write_audit(
        db,
        event_type="skill.forked",
        actor_id=user_id,
        target_type="skill",
        target_id=str(original.id),
        metadata={
            "original_slug": slug,
            "forked_slug": fork_slug,
            "forked_skill_id": str(forked_skill.id),
        },
    )

    db.commit()

    return {
        "id": fork_record.id,
        "original_skill_id": original.id,
        "forked_skill_id": forked_skill.id,
        "forked_skill_slug": fork_slug,
        "forked_by": user_id,
    }


def follow_user(
    db: Session,
    slug: str,
    follower_id: UUID,
) -> dict[str, Any]:
    """Follow the author of a skill (upsert — idempotent)."""
    skill = get_skill_or_404(db, slug)
    followed_user_id = skill.author_id

    existing = (
        db.query(Follow)
        .filter(
            Follow.follower_id == follower_id,
            Follow.followed_user_id == followed_user_id,
        )
        .first()
    )
    if existing:
        return {
            "follower_id": existing.follower_id,
            "followed_user_id": existing.followed_user_id,
            "created_at": existing.created_at,
        }

    follow = Follow(follower_id=follower_id, followed_user_id=followed_user_id)
    db.add(follow)

    _write_audit(
        db,
        event_type="user.followed",
        actor_id=follower_id,
        target_type="user",
        target_id=str(followed_user_id),
        metadata={"via_skill_slug": slug},
    )

    db.commit()
    db.refresh(follow)

    return {
        "follower_id": follow.follower_id,
        "followed_user_id": follow.followed_user_id,
        "created_at": follow.created_at,
    }
