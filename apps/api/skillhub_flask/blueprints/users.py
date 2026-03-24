"""Users profile and personal collection endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from flask import Blueprint, g, jsonify, request

from skillhub_flask.db import get_db

from skillhub.schemas.user import (
    SubmissionSummary,
    UserProfile,
    UserSkillCollectionResponse,
    UserSkillSummary,
    UserSubmissionsResponse,
)
from skillhub.services.users import (
    get_user_favorites,
    get_user_forks,
    get_user_installs,
    get_user_profile,
    get_user_submissions,
)

logger = logging.getLogger(__name__)

bp = Blueprint("users", __name__)


@bp.route("/api/v1/users/me", methods=["GET"])
def get_me() -> tuple:
    """Get current user profile with stats."""
    db = get_db()
    current_user = g.current_user
    profile = get_user_profile(db, current_user)
    return jsonify(UserProfile(**profile).model_dump(mode="json")), 200


@bp.route("/api/v1/users/me/installs", methods=["GET"])
def list_installs() -> tuple:
    """Get current user's installed skills."""
    db = get_db()
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])

    include_uninstalled = request.args.get("include_uninstalled", "false").lower() in ("true", "1")
    page = max(1, request.args.get("page", 1, type=int))
    per_page = max(1, min(100, request.args.get("per_page", 20, type=int)))

    items, total = get_user_installs(
        db,
        user_id,
        page=page,
        per_page=per_page,
        include_uninstalled=include_uninstalled,
    )
    has_more = (page * per_page) < total
    response = UserSkillCollectionResponse(
        items=[UserSkillSummary(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/users/me/favorites", methods=["GET"])
def list_favorites() -> tuple:
    """Get current user's favorited skills."""
    db = get_db()
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])

    page = max(1, request.args.get("page", 1, type=int))
    per_page = max(1, min(100, request.args.get("per_page", 20, type=int)))

    items, total = get_user_favorites(db, user_id, page=page, per_page=per_page)
    has_more = (page * per_page) < total
    response = UserSkillCollectionResponse(
        items=[UserSkillSummary(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/users/me/forks", methods=["GET"])
def list_forks() -> tuple:
    """Get current user's forked skills."""
    db = get_db()
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])

    page = max(1, request.args.get("page", 1, type=int))
    per_page = max(1, min(100, request.args.get("per_page", 20, type=int)))

    items, total = get_user_forks(db, user_id, page=page, per_page=per_page)
    has_more = (page * per_page) < total
    response = UserSkillCollectionResponse(
        items=[UserSkillSummary(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/users/me/submissions", methods=["GET"])
def list_submissions() -> tuple:
    """Get current user's skill submissions with status."""
    db = get_db()
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])

    page = max(1, request.args.get("page", 1, type=int))
    per_page = max(1, min(100, request.args.get("per_page", 20, type=int)))

    items, total = get_user_submissions(db, user_id, page=page, per_page=per_page)
    has_more = (page * per_page) < total
    response = UserSubmissionsResponse(
        items=[SubmissionSummary(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )
    return jsonify(response.model_dump(mode="json")), 200
