"""Health check blueprint."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

bp = Blueprint("health", __name__)


@bp.route("/health")
def health_check() -> tuple:
    """Return application health status and version."""
    settings = current_app.extensions["settings"]
    return jsonify({"status": "ok", "version": settings.app_version}), 200
