"""Review queue endpoints — admin HITL review.

Bug fix applied: event_type string generation uses explicit dict lookup
instead of f"submission.{decision}d" which produces "submission.rejectd".
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from flask import Blueprint, g, jsonify, request

from skillhub_flask.db import get_db

from skillhub.schemas.review_queue import (
    ClaimResponse,
    DecisionRequest,
    DecisionResponse,
    ReviewQueueItem,
    ReviewQueueResponse,
)
from skillhub.services.review_queue import (
    claim_submission,
    decide_submission,
    get_review_queue,
)

logger = logging.getLogger(__name__)

bp = Blueprint("review_queue", __name__)

# Fix: explicit mapping instead of buggy f"submission.{decision}d"
# which would produce "submission.rejectd" instead of "submission.rejected"
_DECISION_EVENT = {
    "approve": "submission.approved",
    "reject": "submission.rejected",
    "request_changes": "submission.changes_requested",
}


@bp.before_request
def _enforce_platform_team() -> Any:
    """All review queue routes require platform_team."""
    user = getattr(g, "current_user", None)
    if not user or not user.get("is_platform_team"):
        return jsonify({"detail": "Platform team access required"}), 403
    return None


@bp.route("/api/v1/admin/review-queue", methods=["GET"])
def list_review_queue() -> tuple:
    """List submissions awaiting human review."""
    db = get_db()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    page = max(1, page)
    per_page = max(1, min(100, per_page))

    items, total = get_review_queue(db, page=page, per_page=per_page)

    response = ReviewQueueResponse(
        items=[ReviewQueueItem(**i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/admin/review-queue/<submission_id>/claim", methods=["POST"])
def claim(submission_id: str) -> tuple:
    """Claim a submission for review."""
    db = get_db()

    try:
        result = claim_submission(
            db,
            submission_id=UUID(submission_id),
            reviewer_id=UUID(g.current_user["user_id"]),
        )
        return jsonify(ClaimResponse(**result).model_dump(mode="json")), 200
    except ValueError as e:
        return jsonify({"detail": str(e)}), 404


@bp.route("/api/v1/admin/review-queue/<submission_id>/decision", methods=["POST"])
def decide(submission_id: str) -> tuple:
    """Make a review decision on a submission.

    Uses _DECISION_EVENT lookup to get the correct event_type string.
    Self-approval prevention: PermissionError from service layer -> 403.
    """
    db = get_db()
    body = DecisionRequest.model_validate(request.get_json(force=True))

    # Resolve the correct event_type string via dict lookup
    event_type = _DECISION_EVENT.get(body.decision)
    if event_type is None:
        return jsonify({"detail": f"Invalid decision: {body.decision}"}), 400

    try:
        result = decide_submission(
            db,
            submission_id=UUID(submission_id),
            reviewer_id=UUID(g.current_user["user_id"]),
            decision=body.decision,
            notes=body.notes,
            score=body.score,
        )
        return jsonify(DecisionResponse(**result).model_dump(mode="json")), 200
    except ValueError as e:
        return jsonify({"detail": str(e)}), 404
    except PermissionError as e:
        return jsonify({"detail": str(e)}), 403
