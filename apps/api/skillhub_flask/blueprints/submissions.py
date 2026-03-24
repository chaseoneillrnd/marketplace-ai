"""Submission pipeline endpoints — create, view, admin review, access requests."""

from __future__ import annotations

import logging
import threading
import uuid
from typing import Any

from flask import Blueprint, g, jsonify, request

from skillhub_flask.auth import require_platform_team
from skillhub_flask.db import get_db

from skillhub_db.session import SessionLocal

from skillhub.schemas.submission import (
    AccessRequestCreateRequest,
    AccessRequestDetail,
    AccessRequestReviewRequest,
    AccessRequestsResponse,
    AdminSubmissionsResponse,
    AdminSubmissionSummary,
    ReviewDecisionRequest,
    SubmissionCreateRequest,
    SubmissionCreateResponse,
    SubmissionDetail,
)
from skillhub.services.submissions import (
    create_access_request,
    create_submission,
    get_submission,
    list_access_requests,
    list_admin_submissions,
    review_access_request,
    review_submission,
)

logger = logging.getLogger(__name__)

bp = Blueprint("submissions", __name__)


# ---------------------------------------------------------------------------
# User endpoints
# ---------------------------------------------------------------------------


@bp.route("/api/v1/submissions", methods=["POST"])
def create_new_submission() -> tuple:
    """Create a new skill submission and run Gate 1 validation."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user
    user_id = uuid.UUID(current_user["user_id"])

    body = SubmissionCreateRequest(**request.get_json(force=True))

    result = create_submission(
        db,
        user_id=user_id,
        name=body.name,
        short_desc=body.short_desc,
        category=body.category,
        content=body.content,
        declared_divisions=body.declared_divisions,
        division_justification=body.division_justification,
        background_tasks=None,  # No FastAPI BackgroundTasks in Flask
    )

    # If Gate 1 passed, trigger Gate 2 in a background thread
    from skillhub_db.models.flags import FeatureFlag

    flag = db.query(FeatureFlag).filter(FeatureFlag.key == "llm_judge_enabled").first()
    if flag and flag.enabled and result.get("status") == "gate1_passed":
        submission_id = result["id"]

        def _bg_gate2(sid: uuid.UUID) -> None:
            import asyncio

            from skillhub.services.submissions import run_gate2_scan

            bg_db = SessionLocal()
            try:
                asyncio.run(run_gate2_scan(bg_db, sid))
            except Exception:
                logger.exception("Background Gate 2 scan failed for %s", sid)
            finally:
                bg_db.close()

        threading.Thread(target=_bg_gate2, args=(submission_id,), daemon=True).start()

    return jsonify(SubmissionCreateResponse(**result).model_dump(mode="json")), 201


@bp.route("/api/v1/submissions/<submission_id>", methods=["GET"])
def get_submission_detail(submission_id: str) -> tuple:
    """Get submission detail. Owner or platform team only."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user
    user_id = uuid.UUID(current_user["user_id"])
    is_platform_team = current_user.get("is_platform_team", False)

    try:
        sub_uuid = uuid.UUID(submission_id)
    except ValueError:
        return jsonify({"detail": "Invalid submission ID"}), 400

    try:
        result = get_submission(
            db,
            sub_uuid,
            user_id=user_id,
            is_platform_team=is_platform_team,
        )
    except PermissionError as exc:
        return jsonify({"detail": str(exc)}), 403

    if not result:
        return jsonify({"detail": "Submission not found"}), 404

    return jsonify(SubmissionDetail(**result).model_dump(mode="json")), 200


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@bp.route("/api/v1/admin/submissions/<submission_id>/scan", methods=["POST"])
@require_platform_team
def scan_submission(submission_id: str) -> tuple:
    """Trigger Gate 2 LLM scan on a submission. Platform team only.

    This is synchronous in Flask (was async in FastAPI).
    """
    import asyncio

    from skillhub.services.submissions import run_gate2_scan

    db = get_db()

    try:
        sub_uuid = uuid.UUID(submission_id)
    except ValueError:
        return jsonify({"detail": "Invalid submission ID"}), 400

    try:
        result = asyncio.run(run_gate2_scan(db, sub_uuid))
    except ValueError as e:
        return jsonify({"detail": str(e)}), 404

    return jsonify(result), 200


@bp.route("/api/v1/admin/submissions", methods=["GET"])
@require_platform_team
def list_submissions_admin() -> tuple:
    """List all submissions. Platform team only."""
    db = get_db()

    status_filter = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Clamp pagination
    page = max(1, page)
    per_page = max(1, min(100, per_page))

    items, total = list_admin_submissions(
        db,
        status_filter=status_filter,
        page=page,
        per_page=per_page,
    )
    has_more = (page * per_page) < total

    response = AdminSubmissionsResponse(
        items=[AdminSubmissionSummary(**i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/admin/submissions/<submission_id>/review", methods=["POST"])
@require_platform_team
def review_submission_endpoint(submission_id: str) -> tuple:
    """Gate 3 human review. Platform team only."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user
    reviewer_id = uuid.UUID(current_user["user_id"])

    try:
        sub_uuid = uuid.UUID(submission_id)
    except ValueError:
        return jsonify({"detail": "Invalid submission ID"}), 400

    body = ReviewDecisionRequest(**request.get_json(force=True))

    try:
        result = review_submission(
            db,
            sub_uuid,
            reviewer_id=reviewer_id,
            decision=body.decision,
            notes=body.notes,
        )
    except ValueError as e:
        return jsonify({"detail": str(e)}), 404

    return jsonify(result), 200


# ---------------------------------------------------------------------------
# Division Access Request endpoints
# ---------------------------------------------------------------------------


@bp.route("/api/v1/skills/<slug>/access-request", methods=["POST"])
def create_skill_access_request(slug: str) -> tuple:
    """Request access to a skill from a different division."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user
    user_id = uuid.UUID(current_user["user_id"])
    user_division = current_user.get("division", "")

    body = AccessRequestCreateRequest(**request.get_json(force=True))

    try:
        result = create_access_request(
            db,
            skill_slug=slug,
            user_id=user_id,
            user_division=user_division,
            reason=body.reason,
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            return jsonify({"detail": error_msg}), 404
        return jsonify({"detail": error_msg}), 400

    return jsonify(AccessRequestDetail(**result).model_dump(mode="json")), 201


@bp.route("/api/v1/admin/access-requests", methods=["GET"])
@require_platform_team
def list_access_requests_admin() -> tuple:
    """List all access requests. Platform team only."""
    db = get_db()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Clamp pagination
    page = max(1, page)
    per_page = max(1, min(100, per_page))

    items, total = list_access_requests(db, page=page, per_page=per_page)
    has_more = (page * per_page) < total

    response = AccessRequestsResponse(
        items=[AccessRequestDetail(**i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/admin/access-requests/<request_id>/review", methods=["POST"])
@require_platform_team
def review_access_request_endpoint(request_id: str) -> tuple:
    """Review a division access request. Platform team only."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user
    reviewer_id = uuid.UUID(current_user["user_id"])

    try:
        req_uuid = uuid.UUID(request_id)
    except ValueError:
        return jsonify({"detail": "Invalid request ID"}), 400

    body = AccessRequestReviewRequest(**request.get_json(force=True))

    try:
        result = review_access_request(db, req_uuid, reviewer_id=reviewer_id, decision=body.decision)
    except ValueError as e:
        return jsonify({"detail": str(e)}), 404

    return jsonify(result), 200
