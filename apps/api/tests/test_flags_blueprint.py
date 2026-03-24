"""Tests for the flags blueprint (feature flags read + admin CRUD)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import make_token


def _auth_headers(token: str | None = None) -> dict[str, str]:
    if token is None:
        token = make_token()
    return {"Authorization": f"Bearer {token}"}


def _platform_team_headers() -> dict[str, str]:
    token = make_token(payload={
        "sub": "admin-user",
        "division": "platform",
        "is_platform_team": True,
    })
    return {"Authorization": f"Bearer {token}"}


def _regular_user_headers() -> dict[str, str]:
    token = make_token(payload={
        "sub": "regular-user",
        "division": "engineering",
        "is_platform_team": False,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /api/v1/flags (public)
# ---------------------------------------------------------------------------
class TestListFlags:
    """GET /api/v1/flags — public feature flags endpoint."""

    @patch("skillhub_flask.blueprints.flags.get_flags")
    def test_returns_200_with_flags(self, mock_get_flags: MagicMock, client: Any) -> None:
        mock_get_flags.return_value = {"dark_mode": True, "beta_features": False}

        resp = client.get("/api/v1/flags")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["flags"]["dark_mode"] is True
        assert data["flags"]["beta_features"] is False

    @patch("skillhub_flask.blueprints.flags.get_flags")
    def test_works_without_auth(self, mock_get_flags: MagicMock, client: Any) -> None:
        mock_get_flags.return_value = {}

        resp = client.get("/api/v1/flags")
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.flags.get_flags")
    def test_passes_none_division_without_auth(
        self, mock_get_flags: MagicMock, client: Any
    ) -> None:
        """Public endpoint — auth middleware skips, so g.current_user is never set."""
        mock_get_flags.return_value = {}

        client.get("/api/v1/flags")

        call_kwargs = mock_get_flags.call_args[1]
        assert call_kwargs["user_division"] is None

    @patch("skillhub_flask.blueprints.flags.get_flags")
    def test_empty_flags(self, mock_get_flags: MagicMock, client: Any) -> None:
        mock_get_flags.return_value = {}

        resp = client.get("/api/v1/flags")
        assert resp.status_code == 200
        assert resp.get_json()["flags"] == {}


# ---------------------------------------------------------------------------
# POST /api/v1/admin/flags (platform team only)
# ---------------------------------------------------------------------------
class TestCreateFlag:
    """POST /api/v1/admin/flags — create feature flag."""

    @patch("skillhub_flask.blueprints.flags.create_flag")
    def test_returns_201_on_success(self, mock_create: MagicMock, client: Any) -> None:
        mock_create.return_value = {
            "key": "new_feature",
            "enabled": True,
            "description": "A new feature",
            "division_overrides": None,
        }

        resp = client.post(
            "/api/v1/admin/flags",
            json={"key": "new_feature", "enabled": True, "description": "A new feature"},
            headers=_platform_team_headers(),
        )
        assert resp.status_code == 201

        data = resp.get_json()
        assert data["key"] == "new_feature"
        assert data["enabled"] is True

    @patch("skillhub_flask.blueprints.flags.create_flag")
    def test_returns_409_on_duplicate(self, mock_create: MagicMock, client: Any) -> None:
        mock_create.side_effect = ValueError("Flag 'new_feature' already exists")

        resp = client.post(
            "/api/v1/admin/flags",
            json={"key": "new_feature"},
            headers=_platform_team_headers(),
        )
        assert resp.status_code == 409
        assert "already exists" in resp.get_json()["detail"]

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.post("/api/v1/admin/flags", json={"key": "test"})
        assert resp.status_code == 401

    def test_returns_403_for_regular_user(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/admin/flags",
            json={"key": "test"},
            headers=_regular_user_headers(),
        )
        assert resp.status_code == 403

    @patch("skillhub_flask.blueprints.flags.create_flag")
    def test_passes_division_overrides(self, mock_create: MagicMock, client: Any) -> None:
        mock_create.return_value = {
            "key": "scoped_flag",
            "enabled": False,
            "description": None,
            "division_overrides": {"engineering": True},
        }

        resp = client.post(
            "/api/v1/admin/flags",
            json={"key": "scoped_flag", "enabled": False, "division_overrides": {"engineering": True}},
            headers=_platform_team_headers(),
        )
        assert resp.status_code == 201
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["division_overrides"] == {"engineering": True}


# ---------------------------------------------------------------------------
# PATCH /api/v1/admin/flags/<key> (platform team only)
# ---------------------------------------------------------------------------
class TestUpdateFlag:
    """PATCH /api/v1/admin/flags/<key> — update feature flag."""

    @patch("skillhub_flask.blueprints.flags.update_flag")
    def test_returns_200_on_success(self, mock_update: MagicMock, client: Any) -> None:
        mock_update.return_value = {
            "key": "existing_flag",
            "enabled": False,
            "description": "Updated",
            "division_overrides": None,
        }

        resp = client.patch(
            "/api/v1/admin/flags/existing_flag",
            json={"enabled": False, "description": "Updated"},
            headers=_platform_team_headers(),
        )
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["enabled"] is False
        assert data["description"] == "Updated"

    @patch("skillhub_flask.blueprints.flags.update_flag")
    def test_returns_404_when_not_found(self, mock_update: MagicMock, client: Any) -> None:
        mock_update.side_effect = ValueError("Flag 'missing' not found")

        resp = client.patch(
            "/api/v1/admin/flags/missing",
            json={"enabled": True},
            headers=_platform_team_headers(),
        )
        assert resp.status_code == 404
        assert "not found" in resp.get_json()["detail"].lower()

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.patch("/api/v1/admin/flags/test", json={"enabled": True})
        assert resp.status_code == 401

    def test_returns_403_for_regular_user(self, client: Any) -> None:
        resp = client.patch(
            "/api/v1/admin/flags/test",
            json={"enabled": True},
            headers=_regular_user_headers(),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/v1/admin/flags/<key> (platform team only)
# ---------------------------------------------------------------------------
class TestDeleteFlag:
    """DELETE /api/v1/admin/flags/<key> — delete feature flag."""

    @patch("skillhub_flask.blueprints.flags.delete_flag")
    def test_returns_204_on_success(self, mock_delete: MagicMock, client: Any) -> None:
        resp = client.delete(
            "/api/v1/admin/flags/old_flag",
            headers=_platform_team_headers(),
        )
        assert resp.status_code == 204
        assert resp.data == b""
        mock_delete.assert_called_once()

    @patch("skillhub_flask.blueprints.flags.delete_flag")
    def test_returns_404_when_not_found(self, mock_delete: MagicMock, client: Any) -> None:
        mock_delete.side_effect = ValueError("Flag 'missing' not found")

        resp = client.delete(
            "/api/v1/admin/flags/missing",
            headers=_platform_team_headers(),
        )
        assert resp.status_code == 404

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.delete("/api/v1/admin/flags/test")
        assert resp.status_code == 401

    def test_returns_403_for_regular_user(self, client: Any) -> None:
        resp = client.delete(
            "/api/v1/admin/flags/test",
            headers=_regular_user_headers(),
        )
        assert resp.status_code == 403
