"""Authentication router — stub login, /me, and OAuth placeholders."""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID, uuid5

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from skillhub.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Deterministic UUID namespace for dev stub users.
# uuid5(NAMESPACE, username) produces a stable, reproducible UUID per user.
# ---------------------------------------------------------------------------
STUB_USER_NAMESPACE = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _uid(username: str) -> str:
    """Return a deterministic UUID string for a stub username."""
    return str(uuid5(STUB_USER_NAMESPACE, username))


# ---------------------------------------------------------------------------
# Dev user registry — covers all roles/divisions for multi-identity testing.
# Every identity uses password "user".
# ---------------------------------------------------------------------------
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

OAUTH_PROVIDERS: set[str] = {"microsoft", "google", "okta", "github", "oidc"}


class TokenRequest(BaseModel):
    """Request body for stub login."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Response body containing a JWT access token."""

    access_token: str
    token_type: str = "bearer"


class StubUserInfo(BaseModel):
    """Public info about a stub user (for dev user picker)."""

    username: str
    name: str
    division: str
    role: str
    is_platform_team: bool
    is_security_team: bool


@router.post("/token", response_model=TokenResponse)
def login(body: TokenRequest, request: Request) -> TokenResponse:
    """Issue a JWT token using stub credentials (dev/test only)."""
    settings = request.app.state.settings
    if not settings.stub_auth_enabled:
        logger.warning("Stub auth login attempt while disabled")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Stub auth is disabled",
        )

    if body.password != "user" or body.username not in STUB_USERS:
        logger.info("Failed stub login attempt for username=%s", body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    user_claims = STUB_USERS[body.username]
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        **user_claims,
        "sub": user_claims["user_id"],
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    token: str = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    logger.info("Stub token issued for user=%s", body.username)
    return TokenResponse(access_token=token)


@router.get("/me")
def get_me(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """Return the authenticated user's JWT claims."""
    return current_user


@router.get("/dev-users", response_model=list[StubUserInfo])
def list_dev_users(request: Request) -> list[dict[str, Any]]:
    """List available dev stub users (only when stub auth is enabled)."""
    settings = request.app.state.settings
    if not settings.stub_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Stub auth is disabled",
        )
    return [
        {
            "username": u["username"],
            "name": u["name"],
            "division": u["division"],
            "role": u["role"],
            "is_platform_team": u["is_platform_team"],
            "is_security_team": u["is_security_team"],
        }
        for u in STUB_USERS.values()
    ]


@router.get("/oauth/{provider}")
def oauth_redirect(provider: str, request: Request) -> dict[str, Any]:
    """Return a placeholder OAuth redirect URL for the given provider."""
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown provider: {provider}",
        )
    state = secrets.token_urlsafe(32)
    logger.info("OAuth redirect initiated for provider=%s", provider)
    return {
        "redirect_url": f"https://auth.example.com/{provider}/authorize?state={state}",
        "state": state,
    }


@router.get("/oauth/{provider}/callback")
def oauth_callback(provider: str) -> None:
    """Placeholder for OAuth callback — not yet implemented."""
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown provider: {provider}",
        )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OAuth callback not yet implemented",
    )
