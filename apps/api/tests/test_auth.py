"""Tests for the auth router (stub login, /me, OAuth placeholders)."""

from __future__ import annotations

import time
from typing import Any

import jwt as pyjwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from skillhub.routers.auth import STUB_USER, router

# ---------------------------------------------------------------------------
# Local test constants & helpers
# ---------------------------------------------------------------------------

_JWT_SECRET = "test-secret-for-testing"
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE_MINUTES = 60


class _FakeSettings:
    """Minimal stand-in for Settings so tests are self-contained."""

    jwt_secret: str = _JWT_SECRET
    jwt_algorithm: str = _JWT_ALGORITHM
    jwt_expire_minutes: int = _JWT_EXPIRE_MINUTES
    stub_auth_enabled: bool = True


class _FakeSettingsStubDisabled(_FakeSettings):
    stub_auth_enabled: bool = False


def _create_test_app(settings: Any = None) -> FastAPI:
    """Build a minimal FastAPI app with the auth router mounted."""
    app = FastAPI()
    app.state.settings = settings or _FakeSettings()
    app.include_router(router)
    return app


def _make_valid_token(**extra: Any) -> str:
    """Generate a valid JWT with STUB_USER claims."""
    payload: dict[str, Any] = {
        **STUB_USER,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        **extra,
    }
    return pyjwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    """TestClient with stub auth enabled."""
    return TestClient(_create_test_app())


@pytest.fixture()
def client_stub_disabled() -> TestClient:
    """TestClient with stub auth disabled."""
    return TestClient(_create_test_app(settings=_FakeSettingsStubDisabled()))


# ---------------------------------------------------------------------------
# POST /auth/token
# ---------------------------------------------------------------------------


class TestLoginToken:
    """Tests for the stub login endpoint."""

    def test_valid_credentials_returns_200(self, client: TestClient) -> None:
        response = client.post(
            "/auth/token",
            json={"username": "test", "password": "user"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/auth/token",
            json={"username": "test", "password": "wrong"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_wrong_username_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/auth/token",
            json={"username": "wrong", "password": "user"},
        )
        assert response.status_code == 401

    def test_stub_disabled_returns_403(self, client_stub_disabled: TestClient) -> None:
        response = client_stub_disabled.post(
            "/auth/token",
            json={"username": "test", "password": "user"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Stub auth is disabled"

    def test_token_contains_correct_claims(self, client: TestClient) -> None:
        response = client.post(
            "/auth/token",
            json={"username": "test", "password": "user"},
        )
        token = response.json()["access_token"]
        decoded: dict[str, Any] = pyjwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        assert decoded["division"] == "Engineering Org"
        assert decoded["email"] == "test@skillhub.dev"
        assert decoded["user_id"] == "00000000-0000-0000-0000-000000000001"
        assert decoded["username"] == "test"
        assert decoded["is_platform_team"] is False
        assert decoded["is_security_team"] is False


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


class TestGetMe:
    """Tests for the /me endpoint."""

    def test_with_valid_token_returns_user(self, client: TestClient) -> None:
        token = _make_valid_token()
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["division"] == "Engineering Org"
        assert data["email"] == "test@skillhub.dev"

    def test_without_token_returns_401(self, client: TestClient) -> None:
        response = client.get("/auth/me")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/oauth/{provider}
# ---------------------------------------------------------------------------


class TestOAuthRedirect:
    """Tests for the OAuth redirect placeholder."""

    def test_known_provider_returns_redirect(self, client: TestClient) -> None:
        response = client.get("/auth/oauth/microsoft")
        assert response.status_code == 200
        data = response.json()
        assert "redirect_url" in data
        assert "state" in data
        assert "microsoft" in data["redirect_url"]

    def test_unknown_provider_returns_404(self, client: TestClient) -> None:
        response = client.get("/auth/oauth/unknown")
        assert response.status_code == 404
        assert "Unknown provider" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /auth/oauth/{provider}/callback
# ---------------------------------------------------------------------------


class TestOAuthCallback:
    """Tests for the OAuth callback placeholder."""

    def test_known_provider_returns_501(self, client: TestClient) -> None:
        response = client.get("/auth/oauth/microsoft/callback")
        assert response.status_code == 501
        assert "not yet implemented" in response.json()["detail"]

    def test_unknown_provider_returns_404(self, client: TestClient) -> None:
        response = client.get("/auth/oauth/unknown/callback")
        assert response.status_code == 404
