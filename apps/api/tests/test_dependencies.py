"""Tests for FastAPI dependency functions."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from skillhub.dependencies import get_current_user, require_platform_team, require_security_team
from tests.conftest import _make_settings, make_token


def _build_app_with_auth_route() -> FastAPI:
    """Create a minimal app with a protected route for testing auth deps."""
    settings = _make_settings()
    app = FastAPI()
    app.state.settings = settings

    @app.get("/protected")
    def protected(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
        return user

    @app.get("/platform-only")
    def platform_only(user: Annotated[dict[str, Any], Depends(require_platform_team)]) -> dict[str, Any]:
        return user

    @app.get("/security-only")
    def security_only(user: Annotated[dict[str, Any], Depends(require_security_team)]) -> dict[str, Any]:
        return user

    return app


def test_get_current_user_raises_401_on_missing_token() -> None:
    app = _build_app_with_auth_route()
    client = TestClient(app)
    response = client.get("/protected")
    assert response.status_code == 401
    assert "Missing or invalid token" in response.json()["detail"]


def test_get_current_user_raises_401_on_expired_token() -> None:
    app = _build_app_with_auth_route()
    client = TestClient(app)
    token = make_token(expired=True)
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "Token expired" in response.json()["detail"]


def test_get_current_user_raises_401_on_invalid_token() -> None:
    app = _build_app_with_auth_route()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


def test_get_current_user_returns_payload_on_valid_token() -> None:
    app = _build_app_with_auth_route()
    client = TestClient(app)
    token = make_token(payload={"sub": "user-42", "division": "sales"})
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["sub"] == "user-42"
    assert body["division"] == "sales"


def test_require_platform_team_raises_403_for_non_platform_user() -> None:
    app = _build_app_with_auth_route()
    client = TestClient(app)
    token = make_token(payload={"sub": "user-1", "is_platform_team": False})
    response = client.get("/platform-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert "Platform team access required" in response.json()["detail"]


def test_require_platform_team_passes_for_platform_user() -> None:
    app = _build_app_with_auth_route()
    client = TestClient(app)
    token = make_token(payload={"sub": "admin-1", "is_platform_team": True})
    response = client.get("/platform-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["sub"] == "admin-1"


def test_require_security_team_raises_403_for_non_security_user() -> None:
    app = _build_app_with_auth_route()
    client = TestClient(app)
    token = make_token(payload={"sub": "user-1", "is_security_team": False})
    response = client.get("/security-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert "Security team access required" in response.json()["detail"]
