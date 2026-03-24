"""Comprehensive tests for feature flags — resolution, division overrides, caching behavior."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from tests.conftest import _make_settings, make_token


def _make_flag(key: str, enabled: bool, division_overrides: dict | None = None) -> MagicMock:
    """Create a mock FeatureFlag object."""
    flag = MagicMock()
    flag.key = key
    flag.enabled = enabled
    flag.description = f"Description for {key}"
    flag.division_overrides = division_overrides
    return flag


def _make_client(mock_db: MagicMock) -> TestClient:
    settings = _make_settings()
    application = create_app(settings=settings)
    application.dependency_overrides[get_db] = lambda: mock_db
    return TestClient(application)


def _make_auth_headers(division: str = "engineering", **extra: Any) -> dict[str, str]:
    claims: dict[str, Any] = {
        "sub": "test-user",
        "division": division,
        "exp": 9999999999,
    }
    claims.update(extra)
    token = make_token(claims)
    return {"Authorization": f"Bearer {token}"}


# --- Flag Resolution with Division Overrides ---


class TestFlagResolutionWithOverrides:
    """Test that division_overrides correctly override the global flag value."""

    def test_globally_enabled_returns_true(self) -> None:
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_x", True),
        ]
        client = _make_client(mock_db)

        response = client.get("/api/v1/flags")
        assert response.status_code == 200
        assert response.json()["flags"]["feature_x"] is True

    def test_globally_disabled_returns_false(self) -> None:
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_x", False),
        ]
        client = _make_client(mock_db)

        response = client.get("/api/v1/flags")
        assert response.status_code == 200
        assert response.json()["flags"]["feature_x"] is False

    def test_division_override_enables_disabled_flag(self) -> None:
        """Globally disabled flag is enabled for specific division."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_x", False, division_overrides={"engineering": True}),
        ]
        client = _make_client(mock_db)

        response = client.get(
            "/api/v1/flags",
            headers=_make_auth_headers(division="engineering"),
        )
        assert response.status_code == 200
        assert response.json()["flags"]["feature_x"] is True

    def test_division_override_disables_enabled_flag(self) -> None:
        """Globally enabled flag can be disabled for a specific division."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_x", True, division_overrides={"sales": False}),
        ]
        client = _make_client(mock_db)

        response = client.get(
            "/api/v1/flags",
            headers=_make_auth_headers(division="sales"),
        )
        assert response.status_code == 200
        assert response.json()["flags"]["feature_x"] is False

    def test_override_for_different_division_not_applied(self) -> None:
        """Override for division A does not affect division B."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_x", False, division_overrides={"sales": True}),
        ]
        client = _make_client(mock_db)

        response = client.get(
            "/api/v1/flags",
            headers=_make_auth_headers(division="engineering"),
        )
        assert response.status_code == 200
        assert response.json()["flags"]["feature_x"] is False

    def test_multiple_division_overrides(self) -> None:
        """Flag with overrides for multiple divisions."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag(
                "feature_x",
                False,
                division_overrides={"engineering": True, "product": True, "sales": False},
            ),
        ]
        client = _make_client(mock_db)

        # Engineering sees it enabled
        response = client.get(
            "/api/v1/flags",
            headers=_make_auth_headers(division="engineering"),
        )
        assert response.json()["flags"]["feature_x"] is True

        # Product also sees it enabled
        response = client.get(
            "/api/v1/flags",
            headers=_make_auth_headers(division="product"),
        )
        assert response.json()["flags"]["feature_x"] is True

    def test_null_overrides_uses_global(self) -> None:
        """Null division_overrides means use global value."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_x", True, division_overrides=None),
        ]
        client = _make_client(mock_db)

        response = client.get(
            "/api/v1/flags",
            headers=_make_auth_headers(division="engineering"),
        )
        assert response.json()["flags"]["feature_x"] is True


# --- Authenticated vs Anonymous Users ---


class TestFlagsAuthenticatedVsAnonymous:
    """Test flag behavior for authenticated and anonymous users."""

    def test_anonymous_gets_global_values(self) -> None:
        """Unauthenticated users see global flag values only."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_a", True),
            _make_flag("feature_b", False, division_overrides={"engineering": True}),
        ]
        client = _make_client(mock_db)

        response = client.get("/api/v1/flags")
        assert response.status_code == 200
        data = response.json()
        assert data["flags"]["feature_a"] is True
        # Division override should NOT apply for anonymous user
        assert data["flags"]["feature_b"] is False

    def test_authenticated_gets_division_overrides(self) -> None:
        """Authenticated users see division-specific values."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_a", True),
            _make_flag("feature_b", False, division_overrides={"engineering": True}),
        ]
        client = _make_client(mock_db)

        response = client.get(
            "/api/v1/flags",
            headers=_make_auth_headers(division="engineering"),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["flags"]["feature_a"] is True
        assert data["flags"]["feature_b"] is True

    def test_expired_token_treated_as_anonymous(self) -> None:
        """Expired JWT is treated as anonymous."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_a", False, division_overrides={"engineering": True}),
        ]
        client = _make_client(mock_db)

        expired_token = make_token(
            {"sub": "test-user", "division": "engineering"},
            expired=True,
        )
        response = client.get(
            "/api/v1/flags",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 200
        # Should see global value (False) since token is expired
        assert response.json()["flags"]["feature_a"] is False


# --- All Seed Flags Present ---


class TestSeedFlags:
    """Test that the flags endpoint returns all configured flags."""

    def test_empty_flags_table_returns_empty(self) -> None:
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []
        client = _make_client(mock_db)

        response = client.get("/api/v1/flags")
        assert response.status_code == 200
        assert response.json()["flags"] == {}

    def test_multiple_flags_returned(self) -> None:
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("enable_llm_judge", True),
            _make_flag("enable_mcp_server", True),
            _make_flag("enable_social_features", False),
            _make_flag("enable_admin_panel", True),
        ]
        client = _make_client(mock_db)

        response = client.get("/api/v1/flags")
        assert response.status_code == 200
        flags = response.json()["flags"]
        assert len(flags) == 4
        assert flags["enable_llm_judge"] is True
        assert flags["enable_mcp_server"] is True
        assert flags["enable_social_features"] is False
        assert flags["enable_admin_panel"] is True

    def test_flags_response_structure(self) -> None:
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("test_flag", True),
        ]
        client = _make_client(mock_db)

        response = client.get("/api/v1/flags")
        assert response.status_code == 200
        data = response.json()
        assert "flags" in data
        assert isinstance(data["flags"], dict)
        assert all(isinstance(v, bool) for v in data["flags"].values())


# --- Flag Caching Behavior ---


class TestFlagCaching:
    """Test that flags endpoint handles repeated requests correctly."""

    def test_consecutive_requests_return_same_result(self) -> None:
        """Two consecutive requests return consistent flags."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_a", True),
        ]
        client = _make_client(mock_db)

        response1 = client.get("/api/v1/flags")
        response2 = client.get("/api/v1/flags")

        assert response1.json() == response2.json()

    def test_flag_changes_reflected_on_next_request(self) -> None:
        """Flag changes in DB are visible on subsequent requests."""
        mock_db = MagicMock()
        # First request: feature enabled
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_a", True),
        ]
        client = _make_client(mock_db)

        response1 = client.get("/api/v1/flags")
        assert response1.json()["flags"]["feature_a"] is True

        # Second request: feature disabled (simulating DB change)
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_a", False),
        ]

        response2 = client.get("/api/v1/flags")
        assert response2.json()["flags"]["feature_a"] is False

    def test_different_users_see_different_flag_values(self) -> None:
        """Different divisions should see different flag values."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag(
                "beta_feature",
                False,
                division_overrides={"engineering": True},
            ),
        ]
        client = _make_client(mock_db)

        # Engineering user sees it enabled
        eng_response = client.get(
            "/api/v1/flags",
            headers=_make_auth_headers(division="engineering"),
        )
        assert eng_response.json()["flags"]["beta_feature"] is True

        # Sales user sees it disabled
        sales_response = client.get(
            "/api/v1/flags",
            headers=_make_auth_headers(division="sales"),
        )
        assert sales_response.json()["flags"]["beta_feature"] is False
