"""Admin endpoints — feature, deprecate, remove skills, audit log, user management."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from flask import Blueprint, g, jsonify, request

from skillhub_flask.auth import require_security_team
from skillhub_flask.db import get_db

from skillhub.schemas.admin import (
    AdminUserListResponse,
    AdminUserUpdateRequest,
    AdminUserUpdateResponse,
    AuditLogResponse,
    DeprecateSkillResponse,
    FeatureSkillRequest,
    FeatureSkillResponse,
    RemoveSkillResponse,
)
from skillhub.services.admin import (
    deprecate_skill,
    feature_skill,
    list_users,
    query_audit_log,
    remove_skill,
    update_user,
)

logger = logging.getLogger(__name__)

bp = Blueprint("admin", __name__)


@bp.before_request
def _enforce_platform_team() -> Any:
    """All admin routes require platform_team, except DELETE /skills/<slug> (security_team).

    The security_team check for DELETE is handled by the route-level decorator,
    so we skip the blanket platform_team check for that specific endpoint.
    OPTIONS requests are passed through for CORS preflight.
    """
    if request.method == "OPTIONS":
        return None

    if request.endpoint == "admin.remove_skill_endpoint":
        return None

    user = getattr(g, "current_user", None)
    if not user or not user.get("is_platform_team"):
        return jsonify({"detail": "Platform team access required"}), 403
    return None


@bp.route("/api/v1/admin/skills/<slug>/feature", methods=["POST"])
def feature_skill_endpoint(slug: str) -> tuple:
    """Set featured status on a skill. Platform Team only."""
    db = get_db()
    body = FeatureSkillRequest.model_validate(request.get_json(force=True))

    try:
        result = feature_skill(
            db,
            slug=slug,
            featured=body.featured,
            featured_order=body.featured_order,
            actor_id=g.current_user.get("user_id"),
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404

    return jsonify(FeatureSkillResponse(**result).model_dump(mode="json")), 200


@bp.route("/api/v1/admin/skills/<slug>/deprecate", methods=["POST"])
def deprecate_skill_endpoint(slug: str) -> tuple:
    """Deprecate a skill. Platform Team only."""
    db = get_db()

    try:
        result = deprecate_skill(db, slug=slug, actor_id=g.current_user.get("user_id"))
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404

    return jsonify(DeprecateSkillResponse(**result).model_dump(mode="json")), 200


@bp.route("/api/v1/admin/skills/<slug>", methods=["DELETE"])
@require_security_team
def remove_skill_endpoint(slug: str) -> tuple:
    """Soft-remove a skill. Security Team only. Writes audit log."""
    db = get_db()
    actor_id = g.current_user.get("user_id", "")
    ip_address = request.remote_addr

    try:
        result = remove_skill(db, slug=slug, actor_id=actor_id, ip_address=ip_address)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404

    return jsonify(RemoveSkillResponse(**result).model_dump(mode="json")), 200


@bp.route("/api/v1/admin/recalculate-trending", methods=["POST"])
def recalculate_trending_endpoint() -> tuple:
    """Recalculate trending scores for all published skills. Platform Team only."""
    from skillhub.services.skills import recalculate_trending_scores

    db = get_db()
    count = recalculate_trending_scores(db)
    return jsonify({"updated": count}), 200


@bp.route("/api/v1/admin/audit-log", methods=["GET"])
def list_audit_log() -> tuple:
    """Query audit log. Platform Team only."""
    db = get_db()

    event_type = request.args.get("event_type")
    actor_id = request.args.get("actor_id")
    target_id = request.args.get("target_id")

    date_from_str = request.args.get("date_from")
    date_to_str = request.args.get("date_to")
    date_from: datetime | None = datetime.fromisoformat(date_from_str) if date_from_str else None
    date_to: datetime | None = datetime.fromisoformat(date_to_str) if date_to_str else None

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    page = max(1, page)
    per_page = max(1, min(100, per_page))

    items, total = query_audit_log(
        db,
        event_type=event_type,
        actor_id=actor_id,
        target_id=target_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )

    response = AuditLogResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/admin/users", methods=["GET"])
def list_users_endpoint() -> tuple:
    """List users with optional filters. Platform Team only."""
    db = get_db()

    division = request.args.get("division")
    role = request.args.get("role")

    is_platform_team_raw = request.args.get("is_platform_team")
    is_platform_team: bool | None = None
    if is_platform_team_raw is not None:
        is_platform_team = is_platform_team_raw.lower() in ("true", "1")

    is_security_team_raw = request.args.get("is_security_team")
    is_security_team: bool | None = None
    if is_security_team_raw is not None:
        is_security_team = is_security_team_raw.lower() in ("true", "1")

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    page = max(1, page)
    per_page = max(1, min(100, per_page))

    items, total = list_users(
        db,
        division=division,
        role=role,
        is_platform_team=is_platform_team,
        is_security_team=is_security_team,
        page=page,
        per_page=per_page,
    )

    response = AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/admin/users/<user_id>", methods=["PATCH"])
def update_user_endpoint(user_id: str) -> tuple:
    """Update a user's role, division, or team flags. Platform Team only."""
    db = get_db()
    body = AdminUserUpdateRequest.model_validate(request.get_json(force=True))

    try:
        result = update_user(
            db,
            user_id=user_id,
            updates=body.model_dump(exclude_unset=True),
            actor_id=g.current_user.get("user_id"),
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404

    return jsonify(AdminUserUpdateResponse(**result).model_dump(mode="json")), 200
