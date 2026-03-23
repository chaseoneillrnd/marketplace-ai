"""Admin service — feature, deprecate, remove skills, audit log query."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from opentelemetry import trace
from skillhub_db.models.audit import AuditLog
from skillhub_db.models.skill import Skill, SkillStatus
from skillhub_db.models.submission import Submission
from skillhub_db.models.user import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("skillhub.services.admin")


def feature_skill(
    db: Session,
    *,
    slug: str,
    featured: bool,
    featured_order: int | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Set featured status on a skill."""
    with tracer.start_as_current_span("service.admin.feature_skill") as span:
        span.set_attribute("admin.slug", slug)
        span.set_attribute("admin.featured", featured)

        skill = db.query(Skill).filter(Skill.slug == slug).first()
        if not skill:
            span.set_attribute("admin.result", "not_found")
            raise ValueError("Skill not found")
        skill.featured = featured
        skill.featured_order = featured_order

        event = "skill.featured" if featured else "skill.unfeatured"
        log_entry = AuditLog(
            id=uuid.uuid4(),
            event_type=event,
            actor_id=uuid.UUID(actor_id) if actor_id else None,
            target_type="skill",
            target_id=str(skill.id),
            metadata_={"slug": slug, "featured": featured, "featured_order": featured_order},
        )
        db.add(log_entry)

        db.commit()
        db.refresh(skill)

        span.set_attribute("admin.result", "success")
        return {
            "slug": skill.slug,
            "featured": skill.featured,
            "featured_order": skill.featured_order,
        }


def deprecate_skill(
    db: Session,
    *,
    slug: str,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Set skill status to deprecated."""
    with tracer.start_as_current_span("service.admin.deprecate_skill") as span:
        span.set_attribute("admin.slug", slug)

        skill = db.query(Skill).filter(Skill.slug == slug).first()
        if not skill:
            span.set_attribute("admin.result", "not_found")
            raise ValueError("Skill not found")
        skill.status = SkillStatus.DEPRECATED
        skill.deprecated_at = datetime.now(timezone.utc)

        log_entry = AuditLog(
            id=uuid.uuid4(),
            event_type="skill.deprecated",
            actor_id=uuid.UUID(actor_id) if actor_id else None,
            target_type="skill",
            target_id=str(skill.id),
            metadata_={"slug": slug},
        )
        db.add(log_entry)

        db.commit()
        db.refresh(skill)

        span.set_attribute("admin.result", "success")
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
    with tracer.start_as_current_span("service.admin.remove_skill") as span:
        span.set_attribute("admin.slug", slug)
        span.set_attribute("admin.actor_id", actor_id)

        skill = db.query(Skill).filter(Skill.slug == slug).first()
        if not skill:
            span.set_attribute("admin.result", "not_found")
            raise ValueError("Skill not found")
        skill.status = SkillStatus.REMOVED
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

        span.set_attribute("admin.result", "success")
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
    with tracer.start_as_current_span("service.admin.query_audit_log") as span:
        span.set_attribute("admin.event_type", event_type or "")
        span.set_attribute("admin.page", page)

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
        span.set_attribute("admin.total", total)

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


# --- Admin User Management (#17) ---


def list_users(
    db: Session,
    *,
    division: str | None = None,
    role: str | None = None,
    is_platform_team: bool | None = None,
    is_security_team: bool | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """List users with optional division/role/team filters and pagination."""
    with tracer.start_as_current_span("service.admin.list_users") as span:
        span.set_attribute("admin.page", page)

        query = db.query(User)
        if division:
            query = query.filter(User.division == division)
        if role:
            query = query.filter(User.role == role)
        if is_platform_team is not None:
            query = query.filter(User.is_platform_team == is_platform_team)
        if is_security_team is not None:
            query = query.filter(User.is_security_team == is_security_team)

        total = query.count()
        span.set_attribute("admin.total", total)

        users = (
            query.order_by(User.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        items = []
        for u in users:
            items.append(
                {
                    "id": u.id,
                    "email": u.email,
                    "username": u.username,
                    "name": u.name,
                    "division": u.division,
                    "role": u.role,
                    "is_platform_team": u.is_platform_team,
                    "is_security_team": u.is_security_team,
                    "created_at": u.created_at,
                    "last_login_at": u.last_login_at,
                }
            )
        return items, total


def update_user(
    db: Session,
    *,
    user_id: str,
    updates: dict[str, Any],
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Update a user's role, division, or team flags. Writes audit log."""
    with tracer.start_as_current_span("service.admin.update_user") as span:
        span.set_attribute("admin.target_user_id", user_id)

        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            span.set_attribute("admin.result", "not_found")
            raise ValueError("User not found")

        changes: dict[str, Any] = {}
        for field in ("role", "division", "is_platform_team", "is_security_team"):
            if field in updates and updates[field] is not None:
                old_val = getattr(user, field)
                new_val = updates[field]
                if old_val != new_val:
                    changes[field] = {"old": old_val, "new": new_val}
                    setattr(user, field, new_val)

        if not changes:
            span.set_attribute("admin.result", "no_changes")
            return {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "name": user.name,
                "division": user.division,
                "role": user.role,
                "is_platform_team": user.is_platform_team,
                "is_security_team": user.is_security_team,
            }

        log_entry = AuditLog(
            id=uuid.uuid4(),
            event_type="user.updated",
            actor_id=uuid.UUID(actor_id) if actor_id else None,
            target_type="user",
            target_id=user_id,
            metadata_={"changes": changes},
        )
        db.add(log_entry)
        db.commit()
        db.refresh(user)

        span.set_attribute("admin.result", "success")
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "name": user.name,
            "division": user.division,
            "role": user.role,
            "is_platform_team": user.is_platform_team,
            "is_security_team": user.is_security_team,
        }


# --- Admin Submission Queue (#18) ---


def list_all_submissions(
    db: Session,
    *,
    status_filter: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """List all submissions for admin review queue, with optional status filter."""
    with tracer.start_as_current_span("service.admin.list_all_submissions") as span:
        span.set_attribute("admin.page", page)
        span.set_attribute("admin.status_filter", status_filter or "")

        query = db.query(Submission)
        if status_filter:
            query = query.filter(Submission.status == status_filter)

        total = query.count()
        span.set_attribute("admin.total", total)

        submissions = (
            query.order_by(Submission.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        # Resolve submitter names
        submitter_ids = {s.submitted_by for s in submissions}
        name_map: dict[uuid.UUID, str] = {}
        if submitter_ids:
            users = db.query(User.id, User.name).filter(User.id.in_(submitter_ids)).all()
            name_map = {u.id: u.name for u in users}

        items = []
        for s in submissions:
            items.append(
                {
                    "id": s.id,
                    "display_id": s.display_id,
                    "name": s.name,
                    "short_desc": s.short_desc,
                    "category": s.category,
                    "status": s.status.value if hasattr(s.status, "value") else s.status,
                    "submitted_by": s.submitted_by,
                    "submitted_by_name": name_map.get(s.submitted_by),
                    "declared_divisions": s.declared_divisions or [],
                    "created_at": s.created_at,
                }
            )
        return items, total
