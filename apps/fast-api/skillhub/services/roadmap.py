"""Roadmap service — create, list, transition, ship platform updates."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from opentelemetry import trace
from skillhub_db.models.audit import AuditLog
from skillhub_db.models.feedback import PlatformUpdate, SkillFeedback
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("skillhub.services.roadmap")

VALID_TRANSITIONS: dict[str, set[str]] = {
    "planned": {"in_progress", "cancelled"},
    "in_progress": {"shipped", "cancelled"},
    "shipped": set(),  # terminal
    "cancelled": {"planned"},  # can reopen
}


def _update_to_dict(u: PlatformUpdate) -> dict[str, Any]:
    """Convert a PlatformUpdate ORM object to a dict."""
    return {
        "id": u.id,
        "title": u.title,
        "body": u.body,
        "status": u.status,
        "author_id": u.author_id,
        "target_quarter": u.target_quarter,
        "linked_feedback_ids": u.linked_feedback_ids or [],
        "shipped_at": u.shipped_at,
        "sort_order": u.sort_order,
        "created_at": u.created_at,
        "updated_at": u.updated_at,
    }


def create_update(
    db: Session,
    *,
    title: str,
    body: str,
    author_id: str,
    status: str = "planned",
    target_quarter: str | None = None,
) -> dict[str, Any]:
    """Create a new platform update / roadmap item."""
    with tracer.start_as_current_span("service.roadmap.create"):
        update = PlatformUpdate(
            id=uuid.uuid4(),
            title=title,
            body=body,
            status=status,
            author_id=uuid.UUID(author_id) if isinstance(author_id, str) else author_id,
            target_quarter=target_quarter,
            linked_feedback_ids=[],
            sort_order=0,
        )
        db.add(update)
        db.commit()
        db.refresh(update)
        return _update_to_dict(update)


def list_updates(
    db: Session,
    *,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """List platform updates with optional status filter."""
    with tracer.start_as_current_span("service.roadmap.list"):
        query = db.query(PlatformUpdate)
        if status:
            query = query.filter(PlatformUpdate.status == status)

        total = query.count()
        items = (
            query.order_by(PlatformUpdate.sort_order.asc(), PlatformUpdate.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return [_update_to_dict(u) for u in items], total


def update_status(
    db: Session,
    *,
    update_id: str,
    new_status: str,
    actor_id: str,
) -> dict[str, Any]:
    """Transition a platform update to a new status, validating the transition."""
    with tracer.start_as_current_span("service.roadmap.update_status") as span:
        uid = uuid.UUID(update_id) if isinstance(update_id, str) else update_id
        update = db.query(PlatformUpdate).filter(PlatformUpdate.id == uid).first()
        if not update:
            raise ValueError("Platform update not found")

        current = update.status
        allowed = VALID_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {current} -> {new_status}. "
                f"Allowed: {allowed or 'none (terminal state)'}"
            )

        old_status = update.status
        update.status = new_status

        log_entry = AuditLog(
            id=uuid.uuid4(),
            event_type="platform_update.status_changed",
            actor_id=uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id,
            target_type="platform_update",
            target_id=str(update.id),
            metadata_={"old_status": old_status, "new_status": new_status},
        )
        db.add(log_entry)
        db.commit()
        db.refresh(update)

        span.set_attribute("roadmap.update_id", str(update.id))
        return _update_to_dict(update)


def ship_update(
    db: Session,
    *,
    update_id: str,
    version_tag: str,
    changelog_body: str,
    actor_id: str,
) -> dict[str, Any]:
    """Atomically ship a platform update: set status, shipped_at, resolve linked feedback."""
    with tracer.start_as_current_span("service.roadmap.ship") as span:
        uid = uuid.UUID(update_id) if isinstance(update_id, str) else update_id
        update = db.query(PlatformUpdate).filter(PlatformUpdate.id == uid).first()
        if not update:
            raise ValueError("Platform update not found")

        if update.status not in ("planned", "in_progress"):
            raise ValueError(f"Cannot ship from status: {update.status}")

        update.status = "shipped"
        update.shipped_at = datetime.now(UTC)
        update.body = f"{update.body}\n\n---\n**{version_tag}**: {changelog_body}"

        # Resolve linked feedback
        if update.linked_feedback_ids:
            for fid in update.linked_feedback_ids:
                feedback = db.query(SkillFeedback).filter(
                    SkillFeedback.id == uuid.UUID(str(fid))
                ).first()
                if feedback and feedback.status != "archived":
                    feedback.status = "archived"

        log_entry = AuditLog(
            id=uuid.uuid4(),
            event_type="platform_update.shipped",
            actor_id=uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id,
            target_type="platform_update",
            target_id=str(update.id),
            metadata_={"version_tag": version_tag},
        )
        db.add(log_entry)
        db.commit()
        db.refresh(update)

        span.set_attribute("roadmap.update_id", str(update.id))
        span.set_attribute("roadmap.version_tag", version_tag)
        return _update_to_dict(update)


def reorder_updates(
    db: Session,
    *,
    ordered_ids: list[str],
) -> None:
    """Reorder platform updates by setting sort_order based on position."""
    with tracer.start_as_current_span("service.roadmap.reorder"):
        for idx, uid_str in enumerate(ordered_ids):
            uid = uuid.UUID(uid_str) if isinstance(uid_str, str) else uid_str
            update = db.query(PlatformUpdate).filter(PlatformUpdate.id == uid).first()
            if update:
                update.sort_order = idx
        db.commit()


def delete_update(
    db: Session,
    *,
    update_id: str,
    actor_id: str,
) -> dict[str, Any]:
    """Soft-delete a platform update by setting status to cancelled."""
    with tracer.start_as_current_span("service.roadmap.delete") as span:
        uid = uuid.UUID(update_id) if isinstance(update_id, str) else update_id
        update = db.query(PlatformUpdate).filter(PlatformUpdate.id == uid).first()
        if not update:
            raise ValueError("Platform update not found")

        update.status = "cancelled"

        log_entry = AuditLog(
            id=uuid.uuid4(),
            event_type="platform_update.deleted",
            actor_id=uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id,
            target_type="platform_update",
            target_id=str(update.id),
            metadata_={"title": update.title},
        )
        db.add(log_entry)
        db.commit()
        db.refresh(update)

        span.set_attribute("roadmap.update_id", str(update.id))
        return _update_to_dict(update)
