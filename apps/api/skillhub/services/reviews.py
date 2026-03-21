"""Reviews and comments service — CRUD + voting with audit logging."""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Any
from uuid import UUID

from skillhub_db.models.audit import AuditLog
from skillhub_db.models.skill import Skill
from skillhub_db.models.social import (
    Comment,
    CommentVote,
    Reply,
    Review,
    ReviewVote,
    VoteType,
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

# Bayesian rating constants
BAYESIAN_C = 5
BAYESIAN_M = Decimal("3.0")


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


def _get_skill_by_slug(db: Session, slug: str) -> Skill:
    """Look up skill or raise ValueError."""
    skill = db.query(Skill).filter(Skill.slug == slug).first()
    if not skill:
        raise ValueError(f"Skill '{slug}' not found")
    return skill


def _recalculate_avg_rating(db: Session, skill_id: UUID) -> None:
    """Recalculate Bayesian avg_rating for a skill.

    Formula: (C * m + sum_ratings) / (C + count)
    where C=5, m=3.0
    """
    result = (
        db.query(
            func.count(Review.id),
            func.coalesce(func.sum(Review.rating), 0),
        )
        .filter(Review.skill_id == skill_id)
        .first()
    )
    count = result[0] if result else 0
    sum_ratings = Decimal(str(result[1])) if result else Decimal("0")

    avg = (BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + count)
    # Clamp to 2 decimal places
    avg = round(avg, 2)

    db.query(Skill).filter(Skill.id == skill_id).update(
        {Skill.avg_rating: avg, Skill.review_count: count}
    )


# --- Reviews ---


def list_reviews(
    db: Session,
    slug: str,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Get paginated reviews for a skill, sorted by helpful_count DESC."""
    skill = _get_skill_by_slug(db, slug)

    query = db.query(Review).filter(Review.skill_id == skill.id)
    total = query.count()

    offset = (page - 1) * per_page
    reviews = (
        query.order_by(Review.helpful_count.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    return [_review_to_dict(r) for r in reviews], total


def create_review(
    db: Session,
    slug: str,
    user_id: UUID,
    rating: int,
    body: str,
) -> dict[str, Any]:
    """Create a review. Raises DuplicateReviewError if already reviewed."""
    skill = _get_skill_by_slug(db, slug)

    review = Review(
        id=uuid.uuid4(),
        skill_id=skill.id,
        user_id=user_id,
        rating=rating,
        body=body,
        helpful_count=0,
        unhelpful_count=0,
    )
    db.add(review)

    try:
        db.flush()
    except IntegrityError as err:
        db.rollback()
        raise DuplicateReviewError("User has already reviewed this skill") from err

    _recalculate_avg_rating(db, skill.id)

    _write_audit(
        db,
        event_type="review.created",
        actor_id=user_id,
        target_type="review",
        target_id=str(review.id),
        metadata={"skill_slug": slug, "rating": rating},
    )

    db.commit()
    db.refresh(review)

    return _review_to_dict(review)


def update_review(
    db: Session,
    slug: str,
    review_id: UUID,
    user_id: UUID,
    *,
    rating: int | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    """Update a review. Only the owner can update. Raises PermissionError if not owner."""
    skill = _get_skill_by_slug(db, slug)

    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.skill_id == skill.id)
        .first()
    )
    if not review:
        raise ValueError("Review not found")

    if review.user_id != user_id:
        raise PermissionError("Only the review owner can update")

    if rating is not None:
        review.rating = rating
    if body is not None:
        review.body = body

    _recalculate_avg_rating(db, skill.id)

    _write_audit(
        db,
        event_type="review.updated",
        actor_id=user_id,
        target_type="review",
        target_id=str(review.id),
        metadata={"skill_slug": slug},
    )

    db.commit()
    db.refresh(review)

    return _review_to_dict(review)


def vote_on_review(
    db: Session,
    slug: str,
    review_id: UUID,
    user_id: UUID,
    vote: str,
) -> None:
    """Vote on a review (upsert). Updates helpful/unhelpful counts."""
    skill = _get_skill_by_slug(db, slug)

    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.skill_id == skill.id)
        .first()
    )
    if not review:
        raise ValueError("Review not found")

    vote_type = VoteType(vote)

    existing = (
        db.query(ReviewVote)
        .filter(ReviewVote.review_id == review_id, ReviewVote.user_id == user_id)
        .first()
    )

    if existing:
        old_vote = existing.vote
        existing.vote = vote_type
        # Adjust counts
        if old_vote == VoteType.HELPFUL:
            review.helpful_count = max(0, review.helpful_count - 1)
        else:
            review.unhelpful_count = max(0, review.unhelpful_count - 1)
    else:
        rv = ReviewVote(review_id=review_id, user_id=user_id, vote=vote_type)
        db.add(rv)

    if vote_type == VoteType.HELPFUL:
        review.helpful_count += 1
    else:
        review.unhelpful_count += 1

    _write_audit(
        db,
        event_type="review.voted",
        actor_id=user_id,
        target_type="review",
        target_id=str(review_id),
        metadata={"vote": vote, "skill_slug": slug},
    )

    db.commit()


# --- Comments ---


def list_comments(
    db: Session,
    slug: str,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Get paginated comments with nested replies."""
    skill = _get_skill_by_slug(db, slug)

    query = (
        db.query(Comment)
        .options(joinedload(Comment.replies))
        .filter(Comment.skill_id == skill.id)
    )
    total = query.count()

    offset = (page - 1) * per_page
    comments = (
        query.order_by(Comment.created_at.desc())
        .offset(offset)
        .limit(per_page)
        .unique()
        .all()
    )

    return [_comment_to_dict(c) for c in comments], total


def create_comment(
    db: Session,
    slug: str,
    user_id: UUID,
    body: str,
) -> dict[str, Any]:
    """Create a comment on a skill."""
    skill = _get_skill_by_slug(db, slug)

    comment = Comment(
        id=uuid.uuid4(),
        skill_id=skill.id,
        user_id=user_id,
        body=body,
        upvote_count=0,
    )
    db.add(comment)

    _write_audit(
        db,
        event_type="comment.created",
        actor_id=user_id,
        target_type="comment",
        target_id=str(comment.id),
        metadata={"skill_slug": slug},
    )

    db.commit()
    db.refresh(comment)

    return _comment_to_dict(comment)


def delete_comment(
    db: Session,
    slug: str,
    comment_id: UUID,
    user_id: UUID,
    is_platform_team: bool = False,
) -> dict[str, Any]:
    """Soft delete a comment. Owner or platform team only."""
    skill = _get_skill_by_slug(db, slug)

    comment = (
        db.query(Comment)
        .options(joinedload(Comment.replies))
        .filter(Comment.id == comment_id, Comment.skill_id == skill.id)
        .first()
    )
    if not comment:
        raise ValueError("Comment not found")

    if comment.user_id != user_id and not is_platform_team:
        raise PermissionError("Only the comment owner or platform team can delete")

    comment.body = "[deleted]"
    comment.deleted_at = func.now()

    _write_audit(
        db,
        event_type="comment.deleted",
        actor_id=user_id,
        target_type="comment",
        target_id=str(comment_id),
        metadata={"skill_slug": slug},
    )

    db.commit()
    db.refresh(comment)

    return _comment_to_dict(comment)


def create_reply(
    db: Session,
    slug: str,
    comment_id: UUID,
    user_id: UUID,
    body: str,
) -> dict[str, Any]:
    """Create a reply to a comment."""
    skill = _get_skill_by_slug(db, slug)

    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id, Comment.skill_id == skill.id)
        .first()
    )
    if not comment:
        raise ValueError("Comment not found")

    reply = Reply(
        id=uuid.uuid4(),
        comment_id=comment_id,
        user_id=user_id,
        body=body,
    )
    db.add(reply)

    _write_audit(
        db,
        event_type="comment.replied",
        actor_id=user_id,
        target_type="reply",
        target_id=str(reply.id),
        metadata={"skill_slug": slug, "comment_id": str(comment_id)},
    )

    db.commit()
    db.refresh(reply)

    return _reply_to_dict(reply)


def vote_on_comment(
    db: Session,
    slug: str,
    comment_id: UUID,
    user_id: UUID,
) -> None:
    """Upvote a comment (upsert — idempotent)."""
    skill = _get_skill_by_slug(db, slug)

    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id, Comment.skill_id == skill.id)
        .first()
    )
    if not comment:
        raise ValueError("Comment not found")

    existing = (
        db.query(CommentVote)
        .filter(CommentVote.comment_id == comment_id, CommentVote.user_id == user_id)
        .first()
    )
    if existing:
        # Already voted — idempotent
        return

    cv = CommentVote(comment_id=comment_id, user_id=user_id)
    db.add(cv)

    comment.upvote_count += 1

    _write_audit(
        db,
        event_type="comment.voted",
        actor_id=user_id,
        target_type="comment",
        target_id=str(comment_id),
        metadata={"skill_slug": slug},
    )

    db.commit()


# --- Helpers ---


def _review_to_dict(review: Review) -> dict[str, Any]:
    """Convert Review ORM to dict."""
    return {
        "id": review.id,
        "skill_id": review.skill_id,
        "user_id": review.user_id,
        "rating": review.rating,
        "body": review.body,
        "helpful_count": review.helpful_count,
        "unhelpful_count": review.unhelpful_count,
        "created_at": review.created_at,
        "updated_at": review.updated_at,
    }


def _comment_to_dict(comment: Comment) -> dict[str, Any]:
    """Convert Comment ORM to dict with nested replies."""
    return {
        "id": comment.id,
        "skill_id": comment.skill_id,
        "user_id": comment.user_id,
        "body": comment.body,
        "upvote_count": comment.upvote_count,
        "deleted_at": comment.deleted_at,
        "created_at": comment.created_at,
        "replies": [_reply_to_dict(r) for r in comment.replies],
    }


def _reply_to_dict(reply: Reply) -> dict[str, Any]:
    """Convert Reply ORM to dict."""
    return {
        "id": reply.id,
        "comment_id": reply.comment_id,
        "user_id": reply.user_id,
        "body": reply.body,
        "deleted_at": reply.deleted_at,
        "created_at": reply.created_at,
    }


class DuplicateReviewError(Exception):
    """Raised when a user tries to review a skill they already reviewed."""
