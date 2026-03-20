"""FastAPI dependency injection functions."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from skillhub_db.session import SessionLocal
from sqlalchemy.orm import Session

from skillhub.config import Settings


def get_settings(request: Request) -> Settings:
    """Retrieve the Settings instance stored on app state."""
    settings: Settings = request.app.state.settings
    return settings


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session, ensuring it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
) -> dict[str, Any]:
    """Extract and validate JWT from the Authorization header."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token",
        )
    token = auth.removeprefix("Bearer ")
    settings: Settings = request.app.state.settings
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from err
    except jwt.InvalidTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from err
    return payload


def require_platform_team(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """Ensure the current user belongs to the platform team."""
    if not current_user.get("is_platform_team"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform team access required",
        )
    return current_user


def require_security_team(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """Ensure the current user belongs to the security team."""
    if not current_user.get("is_security_team"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security team access required",
        )
    return current_user
