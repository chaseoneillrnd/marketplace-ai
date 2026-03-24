"""Feature flags endpoints -- read and admin CRUD."""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, g, jsonify, request

from skillhub_flask.auth import require_platform_team
from skillhub_flask.db import get_db

from skillhub.schemas.flags import (
    FlagCreateRequest,
    FlagDetailResponse,
    FlagUpdateRequest,
    FlagsListResponse,
)
from skillhub.services.flags import create_flag, delete_flag, get_flags, update_flag

logger = logging.getLogger(__name__)

bp = Blueprint("flags", __name__)


@bp.route("/api/v1/flags", methods=["GET"])
def list_flags() -> tuple:
    """Return all feature flags with division overrides applied."""
    db = get_db()

    # Optional user on public route
    user: dict[str, Any] | None = getattr(g, "current_user", None)
    division = user.get("division") if user else None

    flags = get_flags(db, user_division=division)
    response = FlagsListResponse(flags=flags)
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/admin/flags", methods=["POST"])
@require_platform_team
def post_flag() -> tuple:
    """Create a new feature flag. Platform team only."""
    db = get_db()
    body = FlagCreateRequest(**request.get_json(force=True))

    try:
        result = create_flag(
            db,
            body.key,
            enabled=body.enabled,
            description=body.description,
            division_overrides=body.division_overrides,
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 409

    return jsonify(FlagDetailResponse(**result).model_dump(mode="json")), 201


@bp.route("/api/v1/admin/flags/<key>", methods=["PATCH"])
@require_platform_team
def patch_flag(key: str) -> tuple:
    """Update an existing feature flag. Platform team only."""
    db = get_db()
    body = FlagUpdateRequest(**request.get_json(force=True))

    try:
        result = update_flag(
            db,
            key,
            enabled=body.enabled,
            description=body.description,
            division_overrides=body.division_overrides,
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404

    return jsonify(FlagDetailResponse(**result).model_dump(mode="json")), 200


@bp.route("/api/v1/admin/flags/<key>", methods=["DELETE"])
@require_platform_team
def remove_flag(key: str) -> tuple:
    """Delete a feature flag. Platform team only."""
    db = get_db()

    try:
        delete_flag(db, key)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404

    return "", 204
