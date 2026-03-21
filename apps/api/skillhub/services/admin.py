"""Admin service — feature, deprecate, remove skills, audit log query."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from skillhub_db.models.audit import AuditLog
from skillhub_db.models.skill import Skill, SkillStatus
from skillhub_db.models.user import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def feature_skill(
    db: Session,
    *,
    slug: str,
    featured: bool,
    featured_order: int | None = None,
) -> dict[str, Any]:
    """Set featured status on a skill."""
    skill = db.query(Skill).filter(Skill.slug == slug).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )
    skill.featured = featured
    skill.featured_order = featured_order
    db.commit()
    db.refresh(skill)
    return {
        "slug": skill.slug,
        "featured": skill.featured,
        "featured_order": skill.featured_order,
    }


def deprecate_skill(db: Session, *, slug: str) -> dict[str, Any]:
    """Set skill status to deprecated."""
    skill = db.query(Skill).filter(Skill.slug == slug).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )
    skill.status = SkillStatus.DEPRECATED
    skill.deprecated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(skill)
    return {
        "slug": skill.slug,
        "status": skill.status.value,
        "deprecated_at": skill.deprecated_at,
    }


def remove_skill(
    db: Session,
    *,
    slug: str,
    actor_id: str,
    ip_address: str | None = None,
) -> dict[str, Any]:
    """Soft-remove a skill (set status=removed) and write audit log."""
    skill = db.query(Skill).filter(Skill.slug == slug).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )
    skill.status = SkillStatus.REMOVED
    # Write audit log
    log_entry = AuditLog(
        id=uuid.uuid4(),
        event_type="skill.removed",
        actor_id=uuid.UUID(actor_id),
        target_type="skill",
        target_id=str(skill.id),
        metadata_={"slug": slug},
        ip_address=ip_address,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(skill)
    return {"slug": skill.slug, "status": skill.status.value}


def query_audit_log(
    db: Session,
    *,
    event_type: str | None = None,
    actor_id: str | None = None,
    target_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Query audit log with filters and pagination. Resolves actor name."""
    query = db.query(AuditLog)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if actor_id:
        query = query.filter(AuditLog.actor_id == uuid.UUID(actor_id))
    if target_id:
        query = query.filter(AuditLog.target_id == target_id)
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)

    total = query.count()
    entries = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Resolve actor names
    actor_ids = {e.actor_id for e in entries if e.actor_id}
    actor_map: dict[uuid.UUID, str] = {}
    if actor_ids:
        users = db.query(User.id, User.name).filter(User.id.in_(actor_ids)).all()
        actor_map = {u.id: u.name for u in users}

    items = []
    for entry in entries:
        items.append(
            {
                "id": entry.id,
                "event_type": entry.event_type,
                "actor_id": entry.actor_id,
                "actor_name": actor_map.get(entry.actor_id) if entry.actor_id else None,
                "target_type": entry.target_type,
                "target_id": entry.target_id,
                "metadata": entry.metadata_,
                "ip_address": entry.ip_address,
                "created_at": entry.created_at,
            }
        )
    return items, total
