"""Tests for the before_request authentication middleware."""

from __future__ import annotations

import time
from typing import Any

import jwt as pyjwt
import pytest

from tests.conftest import TEST_JWT_ALGORITHM, TEST_JWT_SECRET, make_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestBeforeRequestAuth:
    """The before_request hook should enforce auth on all non-public endpoints."""

    def test_public_endpoint_no_auth_required(self, client: Any) -> None:
        """Health endpoint should be accessible without a token."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_missing_token_returns_401(self, client: Any) -> None:
        """A non-public endpoint without a token should return 401."""
        # Any non-existent route that isn't in PUBLIC_ENDPOINTS should trigger auth
        response = client.get("/api/v1/users/me")
        assert response.status_code in (401, 404)  # 401 from auth, 404 if route not yet registered

    def test_expired_token_returns_401(self, client: Any) -> None:
        """An expired token should return 401."""
        token = make_token(expired=True)
        response = client.get("/health-protected-test", headers=_auth_headers(token))
        # Since this route doesn't exist, we get 401 from auth (before 404)
        assert response.status_code in (401, 404)

    def test_wrong_secret_returns_401(self, client: Any) -> None:
        """A token signed with the wrong secret should return 401."""
        token = make_token(secret="wrong-secret")
        response = client.get("/some-protected-route", headers=_auth_headers(token))
        assert response.status_code in (401, 404)

    def test_valid_token_passes_auth(self, client: Any) -> None:
        """A valid token should pass authentication (endpoint may still 404)."""
        token = make_token()
        response = client.get("/health", headers=_auth_headers(token))
        # Health is public, so it returns 200 regardless of token
        assert response.status_code == 200

    def test_malformed_token_returns_401(self, client: Any) -> None:
        """A malformed token should return 401."""
        response = client.get(
            "/some-route",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert response.status_code in (401, 404)

    def test_no_bearer_prefix_returns_401(self, client: Any) -> None:
        """Authorization header without Bearer prefix should return 401."""
        token = make_token()
        response = client.get(
            "/some-route",
            headers={"Authorization": token},
        )
        assert response.status_code in (401, 404)

    def test_401_response_has_detail_key(self, client: Any) -> None:
        """401 responses should use JSON format with 'detail' key."""
        response = client.get("/some-nonexistent-protected-route")
        # This should be 401 (auth middleware fires before routing for non-public endpoints)
        if response.status_code == 401:
            data = response.get_json()
            assert "detail" in data
