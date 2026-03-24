"""Feedback service — create, list, upvote, triage feedback."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from opentelemetry import trace
from skillhub_db.models.audit import AuditLog
from skillhub_db.models.feedback import SkillFeedback
from skillhub_db.models.skill import Skill
from skillhub_db.models.user import User
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("skillhub.services.feedback")

VALID_CATEGORIES = {"feature_request", "bug_report", "praise", "complaint"}
VALID_STATUSES = {"open", "triaged", "planned", "archived"}


def infer_sentiment(body: str) -> str:
    """Simple keyword-based sentiment inference."""
    positive_words = {"love", "great", "amazing", "excellent", "helpful", "awesome", "fantastic", "perfect"}
    negative_words = {"hate", "terrible", "awful", "broken", "bad", "worst", "useless", "frustrating", "bug", "crash"}
    lower = body.lower()
    pos = sum(1 for w in positive_words if w in lower)
    neg = sum(1 for w in negative_words if w in lower)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def create_feedback(
    db: Session,
    *,
    user_id: str,
    category: str,
    body: str,
    skill_id: str | None = None,
    allow_contact: bool = False,
) -> dict[str, Any]:
    """Create a new feedback entry with auto-inferred sentiment."""
    with tracer.start_as_current_span("service.feedback.create") as span:
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")

        sentiment = infer_sentiment(body)
        feedback = SkillFeedback(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            skill_id=uuid.UUID(skill_id) if isinstance(skill_id, str) and skill_id else skill_id,
            category=category,
            body=body,
            sentiment=sentiment,
            upvotes=0,
            status="open",
            allow_contact=allow_contact,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        span.set_attribute("feedback.id", str(feedback.id))
        span.set_attribute("feedback.sentiment", sentiment)

        return {
            "id": feedback.id,
            "user_id": feedback.user_id,
            "skill_id": feedback.skill_id,
            "category": feedback.category,
            "body": feedback.body,
            "sentiment": feedback.sentiment,
            "upvotes": feedback.upvotes,
            "status": feedback.status,
            "allow_contact": feedback.allow_contact,
            "created_at": feedback.created_at,
        }


def list_feedback(
    db: Session,
    *,
    category: str | None = None,
    sentiment: str | None = None,
    status: str | None = None,
    sort: str = "priority",
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """List feedback with optional filters and priority scoring."""
    with tracer.start_as_current_span("service.feedback.list"):
        query = db.query(SkillFeedback)

        if category:
            query = query.filter(SkillFeedback.category == category)
        if sentiment:
            query = query.filter(SkillFeedback.sentiment == sentiment)
        if status:
            query = query.filter(SkillFeedback.status == status)

        total = query.count()

        if sort == "priority":
            # Priority: upvotes desc, bug_reports first, then newest
            query = query.order_by(
                SkillFeedback.upvotes.desc(),
                (SkillFeedback.category == "bug_report").desc(),
                SkillFeedback.created_at.desc(),
            )
        elif sort == "newest":
            query = query.order_by(SkillFeedback.created_at.desc())
        elif sort == "upvotes":
            query = query.order_by(SkillFeedback.upvotes.desc())
        else:
            query = query.order_by(SkillFeedback.created_at.desc())

        feedback_items = query.offset((page - 1) * per_page).limit(per_page).all()

        # Batch-resolve skill names and user display names to avoid N+1 queries.
        skill_ids = {f.skill_id for f in feedback_items if f.skill_id}
        user_ids = {f.user_id for f in feedback_items if f.user_id}

        skill_name_map: dict[Any, str] = {}
        if skill_ids:
            skills = db.query(Skill.id, Skill.name).filter(Skill.id.in_(skill_ids)).all()
            skill_name_map = {s.id: s.name for s in skills}

        user_name_map: dict[Any, str] = {}
        if user_ids:
            users = db.query(User.id, User.name).filter(User.id.in_(user_ids)).all()
            user_name_map = {u.id: u.name for u in users}

        return [
            {
                "id": f.id,
                "user_id": f.user_id,
                "skill_id": f.skill_id,
                "category": f.category,
                "body": f.body,
                "sentiment": f.sentiment,
                "upvotes": f.upvotes,
                "status": f.status,
                "allow_contact": f.allow_contact,
                "created_at": f.created_at,
                "skill_name": skill_name_map.get(f.skill_id),
                "user_display_name": user_name_map.get(f.user_id, ""),
            }
            for f in feedback_items
        ], total


def upvote_feedback(
    db: Session,
    *,
    feedback_id: str,
    user_id: str,
) -> dict[str, Any]:
    """Increment upvote count on a feedback entry."""
    with tracer.start_as_current_span("service.feedback.upvote"):
        fid = uuid.UUID(feedback_id) if isinstance(feedback_id, str) else feedback_id
        feedback = db.query(SkillFeedback).filter(SkillFeedback.id == fid).first()
        if not feedback:
            raise ValueError("Feedback not found")

        feedback.upvotes = feedback.upvotes + 1
        db.commit()
        db.refresh(feedback)

        return {
            "id": feedback.id,
            "upvotes": feedback.upvotes,
        }


def update_feedback_status(
    db: Session,
    *,
    feedback_id: str,
    status: str,
    actor_id: str,
) -> dict[str, Any]:
    """Update feedback status. Writes audit log entry."""
    with tracer.start_as_current_span("service.feedback.update_status") as span:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        fid = uuid.UUID(feedback_id) if isinstance(feedback_id, str) else feedback_id
        feedback = db.query(SkillFeedback).filter(SkillFeedback.id == fid).first()
        if not feedback:
            raise ValueError("Feedback not found")

        old_status = feedback.status
        feedback.status = status

        log_entry = AuditLog(
            id=uuid.uuid4(),
            event_type="feedback.status_changed",
            actor_id=uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id,
            target_type="feedback",
            target_id=str(feedback.id),
            metadata_={"old_status": old_status, "new_status": status},
        )
        db.add(log_entry)
        db.commit()
        db.refresh(feedback)

        span.set_attribute("feedback.id", str(feedback.id))
        span.set_attribute("feedback.new_status", status)

        return {
            "id": feedback.id,
            "user_id": feedback.user_id,
            "skill_id": feedback.skill_id,
            "category": feedback.category,
            "body": feedback.body,
            "sentiment": feedback.sentiment,
            "upvotes": feedback.upvotes,
            "status": feedback.status,
            "allow_contact": feedback.allow_contact,
            "created_at": feedback.created_at,
        }
