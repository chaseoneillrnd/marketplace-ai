"""Authentication middleware using before_request with PUBLIC_ENDPOINTS allowlist.

Every route is authenticated by default. Public routes must be explicitly listed.
This fails closed — forgetting to add a route to PUBLIC_ENDPOINTS means it requires auth.
"""

from __future__ import annotations

import functools
import logging
from typing import Any

import jwt
from flask import Flask, abort, g, jsonify, request

logger = logging.getLogger(__name__)

# Routes that do NOT require authentication.
# Format: "blueprint_name.view_function_name"
# This set grows as blueprints are registered — see each blueprint's registration.
PUBLIC_ENDPOINTS: set[str] = {
    "health.health_check",
    "static",
    "openapi.spec",
    "_openapi.spec",
}


def register_auth(app: Flask) -> None:
    """Register the before_request authentication hook."""

    @app.before_request
    def enforce_auth() -> Any:
        """Authenticate every request unless endpoint is in PUBLIC_ENDPOINTS."""
        if request.endpoint in PUBLIC_ENDPOINTS:
            return None

        # Also allow OPTIONS for CORS preflight
        if request.method == "OPTIONS":
            return None

        settings = app.extensions["settings"]
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"detail": "Missing or invalid token"}), 401

        token = auth_header.removeprefix("Bearer ")

        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"detail": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"detail": "Invalid token"}), 401

        g.current_user = payload
        return None

    @app.errorhandler(401)
    def handle_401(e: Any) -> tuple[Any, int]:
        return jsonify({"detail": str(e.description) if hasattr(e, "description") else "Unauthorized"}), 401

    @app.errorhandler(403)
    def handle_403(e: Any) -> tuple[Any, int]:
        return jsonify({"detail": str(e.description) if hasattr(e, "description") else "Forbidden"}), 403

    @app.errorhandler(404)
    def handle_404(e: Any) -> tuple[Any, int]:
        return jsonify({"detail": str(e.description) if hasattr(e, "description") else "Not found"}), 404


def require_platform_team(f: Any) -> Any:
    """Decorator that requires the current user to be on the platform team."""

    @functools.wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        user = getattr(g, "current_user", None)
        if not user or not user.get("is_platform_team"):
            abort(403, description="Platform team access required")
        return f(*args, **kwargs)

    decorated._auth_required = True  # type: ignore[attr-defined]  # noqa: SLF001
    return decorated


def require_security_team(f: Any) -> Any:
    """Decorator that requires the current user to be on the security team."""

    @functools.wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        user = getattr(g, "current_user", None)
        if not user or not user.get("is_security_team"):
            abort(403, description="Security team access required")
        return f(*args, **kwargs)

    decorated._auth_required = True  # type: ignore[attr-defined]  # noqa: SLF001
    return decorated


def require_flag(flag_key: str) -> Any:
    """Decorator that returns 404 if a feature flag is disabled for the current user's division."""

    def decorator(f: Any) -> Any:
        @functools.wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            from skillhub_flask.db import get_db
            from skillhub.services.flags import get_flags

            user = getattr(g, "current_user", None)
            division = user.get("division") if user else None
            db = get_db()
            flags = get_flags(db, user_division=division)
            if not flags.get(flag_key, False):
                abort(404)
            return f(*args, **kwargs)

        return decorated

    return decorator
