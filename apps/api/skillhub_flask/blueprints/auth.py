"""Auth blueprint — /auth/me and OAuth placeholders."""

from __future__ import annotations

import logging
import secrets
from typing import Any

from flask import Blueprint, g, jsonify

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__, url_prefix="/auth")

OAUTH_PROVIDERS: set[str] = {"microsoft", "google", "okta", "github", "oidc"}


@bp.route("/me")
def get_me() -> tuple:
    """Return the authenticated user's JWT claims."""
    return jsonify(g.current_user), 200


@bp.route("/oauth/<provider>")
def oauth_redirect(provider: str) -> tuple:
    """Return a placeholder OAuth redirect URL."""
    if provider not in OAUTH_PROVIDERS:
        return jsonify({"detail": f"Unknown provider: {provider}"}), 404
    state = secrets.token_urlsafe(32)
    logger.info("OAuth redirect initiated for provider=%s", provider)
    return jsonify({
        "redirect_url": f"https://auth.example.com/{provider}/authorize?state={state}",
        "state": state,
    }), 200


@bp.route("/oauth/<provider>/callback")
def oauth_callback(provider: str) -> tuple:
    """Placeholder for OAuth callback — not yet implemented."""
    if provider not in OAUTH_PROVIDERS:
        return jsonify({"detail": f"Unknown provider: {provider}"}), 404
    return jsonify({"detail": "OAuth callback not yet implemented"}), 501
