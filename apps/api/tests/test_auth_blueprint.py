"""Tests for auth and stub_auth blueprints."""

from __future__ import annotations

import jwt as pyjwt
import pytest
from typing import Any

from skillhub_flask.app import create_app
from skillhub_flask.config import AppConfig, Settings
from tests.conftest import TEST_JWT_SECRET, TEST_JWT_ALGORITHM, _make_settings, make_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestAuthMe:
    """GET /auth/me returns the authenticated user's claims."""

    def test_me_returns_claims(self, client: Any) -> None:
        token = make_token(payload={"sub": "test-user", "division": "eng", "name": "Test"})
        response = client.get("/auth/me", headers=_auth_headers(token))
        assert response.status_code == 200
        data = response.get_json()
        assert data["sub"] == "test-user"
        assert data["division"] == "eng"

    def test_me_without_token_returns_401(self, client: Any) -> None:
        response = client.get("/auth/me")
        assert response.status_code == 401


class TestOAuthPlaceholders:
    """OAuth routes are public but return placeholder responses."""

    def test_oauth_redirect_known_provider(self, client: Any) -> None:
        response = client.get("/auth/oauth/github")
        assert response.status_code == 200
        data = response.get_json()
        assert "redirect_url" in data
        assert "state" in data

    def test_oauth_redirect_unknown_provider(self, client: Any) -> None:
        response = client.get("/auth/oauth/unknown")
        assert response.status_code == 404

    def test_oauth_callback_returns_501(self, client: Any) -> None:
        response = client.get("/auth/oauth/github/callback")
        assert response.status_code == 501

    def test_oauth_no_auth_required(self, client: Any) -> None:
        """OAuth routes should be accessible without a token."""
        response = client.get("/auth/oauth/google")
        assert response.status_code == 200


class TestStubAuth:
    """Stub auth blueprint — conditional registration."""

    def test_stub_login_returns_token(self) -> None:
        settings = _make_settings(stub_auth_enabled=True)
        config = AppConfig(settings=settings, session_factory=lambda: None)
        app = create_app(config=config)
        client = app.test_client()
        response = client.post("/auth/token", json={"username": "alice", "password": "user"})
        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_stub_login_invalid_credentials(self) -> None:
        settings = _make_settings(stub_auth_enabled=True)
        config = AppConfig(settings=settings, session_factory=lambda: None)
        app = create_app(config=config)
        client = app.test_client()
        response = client.post("/auth/token", json={"username": "alice", "password": "wrong"})
        assert response.status_code == 401

    def test_stub_login_disabled_returns_404(self) -> None:
        """When stub auth disabled, /auth/token route doesn't exist."""
        settings = _make_settings(stub_auth_enabled=False)
        config = AppConfig(settings=settings, session_factory=lambda: None)
        app = create_app(config=config)
        client = app.test_client()
        response = client.post("/auth/token", json={"username": "alice", "password": "user"})
        # Route not registered, so 404 (or 401 from auth middleware)
        assert response.status_code in (401, 404)

    def test_stub_dev_users_returns_list(self) -> None:
        settings = _make_settings(stub_auth_enabled=True)
        config = AppConfig(settings=settings, session_factory=lambda: None)
        app = create_app(config=config)
        client = app.test_client()
        response = client.get("/auth/dev-users")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 6
        usernames = {u["username"] for u in data}
        assert "alice" in usernames
        assert "bob" in usernames

    def test_stub_token_has_correct_claims(self) -> None:
        settings = _make_settings(stub_auth_enabled=True)
        config = AppConfig(settings=settings, session_factory=lambda: None)
        app = create_app(config=config)
        client = app.test_client()
        response = client.post("/auth/token", json={"username": "alice", "password": "user"})
        assert response.status_code == 200
        token = response.get_json()["access_token"]
        decoded = pyjwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert decoded["username"] == "alice"
        assert decoded["is_platform_team"] is True
        assert "exp" in decoded
        assert "iat" in decoded
