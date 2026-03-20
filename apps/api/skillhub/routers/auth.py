"""Authentication router — stub login, /me, and OAuth placeholders."""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from skillhub.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Stub user claims
STUB_USER: dict[str, Any] = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "email": "test@skillhub.dev",
    "name": "Test User",
    "username": "test",
    "division": "Engineering Org",
    "role": "Senior Engineer",
    "is_platform_team": False,
    "is_security_team": False,
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
    if body.username != "test" or body.password != "user":
        logger.info("Failed stub login attempt for username=%s", body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        **STUB_USER,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    token: str = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    logger.info("Stub token issued for user=%s", STUB_USER["username"])
    return TokenResponse(access_token=token)


@router.get("/me")
def get_me(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """Return the authenticated user's JWT claims."""
    return current_user


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
