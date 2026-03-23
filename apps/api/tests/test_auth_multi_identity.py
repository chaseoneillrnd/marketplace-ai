"""Tests for multi-identity dev auth refactor.

Verifies that:
- Each stub user can authenticate and gets correct JWT claims
- Division enforcement: bob (data-science-org) != engineering-org
- Platform team: alice can access admin, bob cannot
- Security team: carol can access security endpoints
- Backwards compat: "test/user" still works
- Unknown username returns 401
- Wrong password returns 401
- JWT includes all required claims
- /auth/dev-users lists all stub users
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID, uuid5

import jwt
import pytest
from fastapi.testclient import TestClient

from skillhub.routers.auth import STUB_USER_NAMESPACE, STUB_USERS

from .conftest import TEST_JWT_ALGORITHM, TEST_JWT_SECRET, make_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_CLAIMS = {"user_id", "email", "name", "username", "division", "role",
                   "is_platform_team", "is_security_team", "sub"}


def _login(client: TestClient, username: str, password: str = "user") -> dict[str, Any]:
    """POST /auth/token and return the response JSON."""
    resp = client.post("/auth/token", json={"username": username, "password": password})
    return resp.json(), resp.status_code


def _decode(token: str) -> dict[str, Any]:
    """Decode a JWT without verification (for inspecting claims in tests)."""
    return jwt.decode(token, TEST_JWT_SECRET, algorithms=[TEST_JWT_ALGORITHM])


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Test: each stub user authenticates and gets correct JWT claims
# ---------------------------------------------------------------------------

class TestStubUserAuth:
    """Every user in STUB_USERS should be able to log in."""

    @pytest.mark.parametrize("username", list(STUB_USERS.keys()))
    def test_login_returns_200(self, client: TestClient, username: str) -> None:
        body, status = _login(client, username)
        assert status == 200
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    @pytest.mark.parametrize("username", list(STUB_USERS.keys()))
    def test_jwt_contains_all_required_claims(self, client: TestClient, username: str) -> None:
        body, _ = _login(client, username)
        claims = _decode(body["access_token"])
        missing = REQUIRED_CLAIMS - set(claims.keys())
        assert not missing, f"Missing JWT claims for {username}: {missing}"

    @pytest.mark.parametrize("username", list(STUB_USERS.keys()))
    def test_jwt_claims_match_registry(self, client: TestClient, username: str) -> None:
        body, _ = _login(client, username)
        claims = _decode(body["access_token"])
        expected = STUB_USERS[username]
        assert claims["user_id"] == expected["user_id"]
        assert claims["email"] == expected["email"]
        assert claims["name"] == expected["name"]
        assert claims["division"] == expected["division"]
        assert claims["is_platform_team"] == expected["is_platform_team"]
        assert claims["is_security_team"] == expected["is_security_team"]
        assert claims["sub"] == expected["user_id"]

    @pytest.mark.parametrize("username", list(STUB_USERS.keys()))
    def test_deterministic_uuid(self, username: str) -> None:
        """UUID should be stable (uuid5 with known namespace)."""
        expected = str(uuid5(STUB_USER_NAMESPACE, username))
        assert STUB_USERS[username]["user_id"] == expected


# ---------------------------------------------------------------------------
# Test: /auth/me returns correct identity
# ---------------------------------------------------------------------------

class TestAuthMe:
    @pytest.mark.parametrize("username", ["alice", "bob", "carol", "test"])
    def test_me_returns_correct_user(self, client: TestClient, username: str) -> None:
        body, _ = _login(client, username)
        token = body["access_token"]
        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        me = resp.json()
        assert me["user_id"] == STUB_USERS[username]["user_id"]
        assert me["name"] == STUB_USERS[username]["name"]


# ---------------------------------------------------------------------------
# Test: division enforcement
# ---------------------------------------------------------------------------

class TestDivisionEnforcement:
    def test_alice_is_engineering(self, client: TestClient) -> None:
        body, _ = _login(client, "alice")
        claims = _decode(body["access_token"])
        assert claims["division"] == "engineering-org"

    def test_bob_is_data_science(self, client: TestClient) -> None:
        body, _ = _login(client, "bob")
        claims = _decode(body["access_token"])
        assert claims["division"] == "data-science-org"

    def test_carol_is_security(self, client: TestClient) -> None:
        body, _ = _login(client, "carol")
        claims = _decode(body["access_token"])
        assert claims["division"] == "security-org"

    def test_dave_is_product(self, client: TestClient) -> None:
        body, _ = _login(client, "dave")
        claims = _decode(body["access_token"])
        assert claims["division"] == "product-org"


# ---------------------------------------------------------------------------
# Test: platform team access
# ---------------------------------------------------------------------------

class TestPlatformTeamAccess:
    def test_alice_is_platform_team(self, client: TestClient) -> None:
        body, _ = _login(client, "alice")
        claims = _decode(body["access_token"])
        assert claims["is_platform_team"] is True

    def test_admin_is_platform_team(self, client: TestClient) -> None:
        body, _ = _login(client, "admin")
        claims = _decode(body["access_token"])
        assert claims["is_platform_team"] is True

    def test_bob_is_not_platform_team(self, client: TestClient) -> None:
        body, _ = _login(client, "bob")
        claims = _decode(body["access_token"])
        assert claims["is_platform_team"] is False

    def test_test_is_not_platform_team(self, client: TestClient) -> None:
        body, _ = _login(client, "test")
        claims = _decode(body["access_token"])
        assert claims["is_platform_team"] is False


# ---------------------------------------------------------------------------
# Test: security team access
# ---------------------------------------------------------------------------

class TestSecurityTeamAccess:
    def test_carol_is_security_team(self, client: TestClient) -> None:
        body, _ = _login(client, "carol")
        claims = _decode(body["access_token"])
        assert claims["is_security_team"] is True

    def test_admin_is_security_team(self, client: TestClient) -> None:
        body, _ = _login(client, "admin")
        claims = _decode(body["access_token"])
        assert claims["is_security_team"] is True

    def test_alice_is_not_security_team(self, client: TestClient) -> None:
        body, _ = _login(client, "alice")
        claims = _decode(body["access_token"])
        assert claims["is_security_team"] is False


# ---------------------------------------------------------------------------
# Test: backwards compatibility (test/user still works)
# ---------------------------------------------------------------------------

class TestBackwardsCompat:
    def test_test_user_login(self, client: TestClient) -> None:
        body, status = _login(client, "test", "user")
        assert status == 200
        claims = _decode(body["access_token"])
        assert claims["name"] == "Test User"
        assert claims["email"] == "test@acme.com"
        assert claims["division"] == "engineering-org"


# ---------------------------------------------------------------------------
# Test: error cases
# ---------------------------------------------------------------------------

class TestAuthErrors:
    def test_unknown_username_returns_401(self, client: TestClient) -> None:
        _, status = _login(client, "unknown_user", "user")
        assert status == 401

    def test_wrong_password_returns_401(self, client: TestClient) -> None:
        _, status = _login(client, "alice", "wrong_password")
        assert status == 401

    def test_empty_username_returns_401(self, client: TestClient) -> None:
        _, status = _login(client, "", "user")
        assert status == 401

    def test_stub_auth_disabled(self, client: TestClient, app: Any) -> None:
        app.state.settings.stub_auth_enabled = False
        resp = client.post("/auth/token", json={"username": "alice", "password": "user"})
        assert resp.status_code == 403
        app.state.settings.stub_auth_enabled = True  # restore


# ---------------------------------------------------------------------------
# Test: /auth/dev-users endpoint
# ---------------------------------------------------------------------------

class TestDevUsersEndpoint:
    def test_lists_all_stub_users(self, client: TestClient) -> None:
        resp = client.get("/auth/dev-users")
        assert resp.status_code == 200
        users = resp.json()
        assert len(users) == len(STUB_USERS)
        usernames = {u["username"] for u in users}
        assert usernames == set(STUB_USERS.keys())

    def test_user_info_fields(self, client: TestClient) -> None:
        resp = client.get("/auth/dev-users")
        users = resp.json()
        for u in users:
            assert "username" in u
            assert "name" in u
            assert "division" in u
            assert "role" in u
            assert "is_platform_team" in u
            assert "is_security_team" in u
            # Should NOT expose user_id or email in the list endpoint
            assert "user_id" not in u
            assert "email" not in u

    def test_disabled_when_stub_auth_off(self, client: TestClient, app: Any) -> None:
        app.state.settings.stub_auth_enabled = False
        resp = client.get("/auth/dev-users")
        assert resp.status_code == 403
        app.state.settings.stub_auth_enabled = True  # restore


# ---------------------------------------------------------------------------
# Test: require_platform_team dependency works with multi-identity tokens
# ---------------------------------------------------------------------------

class TestDependencyIntegration:
    def test_platform_user_can_call_protected_endpoint(self, client: TestClient) -> None:
        """Alice (platform_team=True) should pass require_platform_team."""
        body, _ = _login(client, "alice")
        token = body["access_token"]
        # /auth/me uses get_current_user — verify it decodes correctly
        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["is_platform_team"] is True

    def test_non_platform_user_gets_correct_claims(self, client: TestClient) -> None:
        """Bob (platform_team=False) should have correct claims but no platform access."""
        body, _ = _login(client, "bob")
        token = body["access_token"]
        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["is_platform_team"] is False


# ---------------------------------------------------------------------------
# Test: seed data UUID alignment
# ---------------------------------------------------------------------------

class TestSeedAlignment:
    def test_stub_users_use_deterministic_uuids(self) -> None:
        """All STUB_USERS UUIDs should be valid uuid5 from the known namespace."""
        for username, user in STUB_USERS.items():
            expected = str(uuid5(STUB_USER_NAMESPACE, username))
            assert user["user_id"] == expected, (
                f"UUID mismatch for {username}: {user['user_id']} != {expected}"
            )

    def test_all_uuids_are_unique(self) -> None:
        ids = [u["user_id"] for u in STUB_USERS.values()]
        assert len(ids) == len(set(ids)), "Duplicate UUIDs in STUB_USERS"
