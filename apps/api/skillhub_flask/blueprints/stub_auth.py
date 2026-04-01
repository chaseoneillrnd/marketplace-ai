"""Stub auth blueprint — conditional, only registered when stub_auth_enabled.

Provides POST /auth/token and GET /auth/dev-users for development testing.
This blueprint MUST NOT be imported in the production app factory.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid5

import jwt
from flask import Blueprint, current_app, jsonify, request
from pydantic import BaseModel


logger = logging.getLogger(__name__)

bp = Blueprint("stub_auth", __name__, url_prefix="/auth")

STUB_USER_NAMESPACE = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _uid(username: str) -> str:
    return str(uuid5(STUB_USER_NAMESPACE, username))


STUB_USERS: dict[str, dict[str, Any]] = {
    "alice": {
        "user_id": _uid("alice"),
        "email": "alice@acme.com",
        "name": "Alice Chen",
        "username": "alice",
        "division": "engineering-org",
        "role": "Staff Engineer",
        "is_platform_team": True,
        "is_security_team": False,
    },
    "bob": {
        "user_id": _uid("bob"),
        "email": "bob@acme.com",
        "name": "Bob Martinez",
        "username": "bob",
        "division": "data-science-org",
        "role": "Senior Data Scientist",
        "is_platform_team": False,
        "is_security_team": False,
    },
    "carol": {
        "user_id": _uid("carol"),
        "email": "carol@acme.com",
        "name": "Carol Park",
        "username": "carol",
        "division": "security-org",
        "role": "Security Lead",
        "is_platform_team": False,
        "is_security_team": True,
    },
    "dave": {
        "user_id": _uid("dave"),
        "email": "dave@acme.com",
        "name": "Dave Thompson",
        "username": "dave",
        "division": "product-org",
        "role": "Senior Product Manager",
        "is_platform_team": False,
        "is_security_team": False,
    },
    "admin": {
        "user_id": _uid("admin"),
        "email": "admin@acme.com",
        "name": "Admin User",
        "username": "admin",
        "division": "engineering-org",
        "role": "Platform Lead",
        "is_platform_team": True,
        "is_security_team": True,
    },
    "test": {
        "user_id": _uid("test"),
        "email": "test@acme.com",
        "name": "Test User",
        "username": "test",
        "division": "engineering-org",
        "role": "Senior Engineer",
        "is_platform_team": False,
        "is_security_team": False,
    },
}


class TokenRequest(BaseModel):
    username: str
    password: str


@bp.route("/token", methods=["POST"])
def login() -> tuple:
    """Issue a JWT token using stub credentials."""
    settings = current_app.extensions["settings"]

    raw = request.get_json(force=True) or {}
    username = raw.get("username", "")
    password = raw.get("password", "")

    if password != "user" or username not in STUB_USERS:
        logger.info("Failed stub login attempt for username=%s", username)
        return jsonify({"detail": "Invalid credentials"}), 401

    user_claims = STUB_USERS[username]
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        **user_claims,
        "sub": user_claims["user_id"],
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    token: str = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    logger.info("Stub token issued for user=%s", username)
    return jsonify({"access_token": token, "token_type": "bearer"}), 200


@bp.route("/dev-users")
def list_dev_users() -> tuple:
    """List available dev stub users."""
    return jsonify([
        {
            "username": u["username"],
            "name": u["name"],
            "division": u["division"],
            "role": u["role"],
            "is_platform_team": u["is_platform_team"],
            "is_security_team": u["is_security_team"],
        }
        for u in STUB_USERS.values()
    ]), 200
