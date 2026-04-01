"""Feedback endpoints — submit, list, upvote, triage.

BUG #5 FIX: The list_feedback service already performs batch JOINs to resolve
user_display_name and skill_name. This blueprint passes those enriched fields
through to the FeedbackResponse schema, which has optional skill_name and
user_display_name fields.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, g, jsonify, request

from skillhub_flask.auth import require_platform_team
from skillhub_flask.db import get_db

from skillhub.schemas.feedback import (
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackResponse,
)
from skillhub.services.feedback import (
    create_feedback,
    list_feedback,
    update_feedback_status,
    upvote_feedback,
)

logger = logging.getLogger(__name__)

bp = Blueprint("feedback", __name__)


@bp.route("/api/v1/feedback", methods=["GET"])
def list_public_feedback() -> tuple:
    """Public feedback list — shows all non-archived feedback with upvote counts."""
    db = get_db()

    category = request.args.get("category")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Clamp pagination
    page = max(1, page)
    per_page = max(1, min(100, per_page))

    items, total = list_feedback(
        db,
        category=category,
        status=None,  # list_feedback has no archived-exclusion built in; filter below
        page=page,
        per_page=per_page,
    )

    # Exclude archived items (service doesn't filter these out by default)
    non_archived = [i for i in items if i.get("status") != "archived"]

    response = FeedbackListResponse(
        items=[FeedbackResponse(**i) for i in non_archived],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/feedback", methods=["POST"])
def submit_feedback() -> tuple:
    """Submit feedback. Any authenticated user."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user

    body = FeedbackCreate.model_validate(request.get_json(force=True) or {})

    result = create_feedback(
        db,
        user_id=current_user["user_id"],
        category=body.category,
        body=body.body,
        skill_id=str(body.skill_id) if body.skill_id else None,
        allow_contact=body.allow_contact,
    )
    return jsonify(FeedbackResponse(**result).model_dump(mode="json")), 201


@bp.route("/api/v1/admin/feedback", methods=["GET"])
@require_platform_team
def list_feedback_admin() -> tuple:
    """List all feedback. Admin only, filtered/sorted/paginated.

    BUG #5 FIX: The service already enriches each item with skill_name and
    user_display_name via batch queries against the skills and users tables.
    We pass them through here so the response includes display names.
    """
    db = get_db()

    category = request.args.get("category")
    sentiment = request.args.get("sentiment")
    feedback_status = request.args.get("status")
    sort = request.args.get("sort", "priority")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Clamp pagination
    page = max(1, page)
    per_page = max(1, min(100, per_page))

    items, total = list_feedback(
        db,
        category=category,
        sentiment=sentiment,
        status=feedback_status,
        sort=sort,
        page=page,
        per_page=per_page,
    )

    response = FeedbackListResponse(
        items=[FeedbackResponse(**i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/feedback/<feedback_id>/upvote", methods=["POST"])
def upvote_feedback_endpoint(feedback_id: str) -> tuple:
    """Upvote a feedback entry. Any authenticated user."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user

    try:
        result = upvote_feedback(
            db,
            feedback_id=feedback_id,
            user_id=current_user["user_id"],
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404

    return jsonify(result), 200


@bp.route("/api/v1/admin/feedback/<feedback_id>/status", methods=["PATCH"])
@require_platform_team
def update_feedback_status_endpoint(feedback_id: str) -> tuple:
    """Update feedback status. Admin only."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user

    data: dict[str, str] = request.get_json(force=True)
    new_status = data.get("status")
    if not new_status:
        return jsonify({"detail": "status is required"}), 422

    try:
        result = update_feedback_status(
            db,
            feedback_id=feedback_id,
            status=new_status,
            actor_id=current_user["user_id"],
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 400

    return jsonify(FeedbackResponse(**result).model_dump(mode="json")), 200
