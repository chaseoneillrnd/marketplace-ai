"""Analytics endpoints — admin only."""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, g, jsonify, request

from skillhub_flask.db import get_db

from skillhub.schemas.analytics import (
    AnalyticsSummary,
    FunnelResponse,
    TimeSeriesResponse,
    TopSkillsResponse,
)
from skillhub.services.analytics import (
    get_submission_funnel,
    get_summary,
    get_time_series,
    get_top_skills,
)

logger = logging.getLogger(__name__)

bp = Blueprint("analytics", __name__)


@bp.before_request
def _enforce_platform_team() -> Any:
    """All analytics routes require platform_team."""
    user = getattr(g, "current_user", None)
    if not user or not user.get("is_platform_team"):
        return jsonify({"detail": "Platform team access required"}), 403
    return None


@bp.route("/api/v1/admin/analytics/summary", methods=["GET"])
def analytics_summary() -> tuple:
    """Get analytics summary with optional division filter."""
    db = get_db()
    division = request.args.get("division", "__all__")

    result = get_summary(db, division=division)
    return jsonify(AnalyticsSummary(**result).model_dump(mode="json")), 200


@bp.route("/api/v1/admin/analytics/time-series", methods=["GET"])
def analytics_time_series() -> tuple:
    """Get time-series analytics data."""
    db = get_db()
    days = request.args.get("days", 30, type=int)
    days = max(1, min(365, days))
    division = request.args.get("division", "__all__")

    series = get_time_series(db, days=days, division=division)
    response = TimeSeriesResponse(series=series, days=days, division=division)
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/admin/analytics/submission-funnel", methods=["GET"])
def analytics_funnel() -> tuple:
    """Get submission funnel analytics."""
    db = get_db()
    days = request.args.get("days", 30, type=int)
    days = max(1, min(365, days))
    division = request.args.get("division", "__all__")

    result = get_submission_funnel(db, days=days, division=division)
    return jsonify(FunnelResponse(**result).model_dump(mode="json")), 200


@bp.route("/api/v1/admin/analytics/top-skills", methods=["GET"])
def analytics_top_skills() -> tuple:
    """Get top skills by usage."""
    db = get_db()
    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(50, limit))

    items = get_top_skills(db, limit=limit)
    return jsonify(TopSkillsResponse(items=items).model_dump(mode="json")), 200
