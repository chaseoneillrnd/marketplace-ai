"""Tests for the roadmap blueprint endpoints.

Includes verification of BUG #6 fix: version_tag must appear in responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import make_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_token(**extra: Any) -> str:
    payload = {"sub": "test-user", "user_id": str(uuid.uuid4()), "division": "engineering"}
    payload.update(extra)
    return make_token(payload=payload)


def _platform_token(**extra: Any) -> str:
    payload = {
        "sub": "admin-user",
        "user_id": str(uuid.uuid4()),
        "division": "platform",
        "is_platform_team": True,
    }
    payload.update(extra)
    return make_token(payload=payload)


def _security_token(**extra: Any) -> str:
    payload = {
        "sub": "security-user",
        "user_id": str(uuid.uuid4()),
        "division": "security",
        "is_security_team": True,
    }
    payload.update(extra)
    return make_token(payload=payload)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_UPDATE_ID = str(uuid.uuid4())
_AUTHOR_ID = str(uuid.uuid4())
_NOW = datetime.now(timezone.utc).isoformat()

_BODY_WITH_VERSION = "Some update body\n\n---\n**v1.2.0**: Released new feature"

_UPDATE_RESULT = {
    "id": _UPDATE_ID,
    "title": "New Feature",
    "body": _BODY_WITH_VERSION,
    "status": "planned",
    "author_id": _AUTHOR_ID,
    "target_quarter": "Q1-2026",
    "linked_feedback_ids": [],
    "shipped_at": None,
    "version_tag": None,
    "sort_order": 0,
    "created_at": _NOW,
    "updated_at": _NOW,
}

_SHIPPED_RESULT = {
    **_UPDATE_RESULT,
    "status": "shipped",
    "shipped_at": _NOW,
}


# ---------------------------------------------------------------------------
# GET /api/v1/admin/platform-updates
# ---------------------------------------------------------------------------


class TestListPlatformUpdates:
    """GET /api/v1/admin/platform-updates — platform team only."""

    @patch("skillhub_flask.blueprints.roadmap.list_updates")
    @patch("skillhub_flask.blueprints.roadmap.get_db")
    def test_success_returns_200_with_version_tag(
        self, mock_get_db: MagicMock, mock_list: MagicMock, client: Any
    ) -> None:
        mock_get_db.return_value = MagicMock()
        mock_list.return_value = ([{**_UPDATE_RESULT}], 1)

        token = _platform_token()
        resp = client.get("/api/v1/admin/platform-updates", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        # BUG #6: version_tag should be extracted from body
        item = data["items"][0]
        assert "version_tag" in item
        assert item["version_tag"] == "v1.2.0"

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/platform-updates")
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.get("/api/v1/admin/platform-updates", headers=_auth_headers(token))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/admin/platform-updates
# ---------------------------------------------------------------------------


class TestCreatePlatformUpdate:
    """POST /api/v1/admin/platform-updates — platform team only."""

    @patch("skillhub_flask.blueprints.roadmap.create_update")
    @patch("skillhub_flask.blueprints.roadmap.get_db")
    def test_success_returns_201(self, mock_get_db: MagicMock, mock_create: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_create.return_value = {**_UPDATE_RESULT}

        token = _platform_token()
        resp = client.post(
            "/api/v1/admin/platform-updates",
            json={
                "title": "New Feature",
                "body": "This is a body that is long enough for validation",
                "status": "planned",
                "target_quarter": "Q1-2026",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "New Feature"
        # BUG #6: version_tag key present in response
        assert "version_tag" in data

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.post("/api/v1/admin/platform-updates", json={"title": "x", "body": "y"})
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.post(
            "/api/v1/admin/platform-updates",
            json={"title": "New Feature", "body": "This is a long enough body"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /api/v1/admin/platform-updates/<id>
# ---------------------------------------------------------------------------


class TestPatchPlatformUpdate:
    """PATCH /api/v1/admin/platform-updates/<id> — platform team only."""

    @patch("skillhub_flask.blueprints.roadmap.update_status")
    @patch("skillhub_flask.blueprints.roadmap.get_db")
    def test_success_returns_200(self, mock_get_db: MagicMock, mock_update: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_update.return_value = {**_UPDATE_RESULT, "status": "in_progress"}

        token = _platform_token()
        resp = client.patch(
            f"/api/v1/admin/platform-updates/{_UPDATE_ID}",
            json={"status": "in_progress"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "in_progress"
        # BUG #6: version_tag present
        assert "version_tag" in data

    @patch("skillhub_flask.blueprints.roadmap.get_db")
    def test_missing_status_returns_422(self, mock_get_db: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()

        token = _platform_token()
        resp = client.patch(
            f"/api/v1/admin/platform-updates/{_UPDATE_ID}",
            json={},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 422

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.patch(f"/api/v1/admin/platform-updates/{_UPDATE_ID}", json={"status": "in_progress"})
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.patch(
            f"/api/v1/admin/platform-updates/{_UPDATE_ID}",
            json={"status": "in_progress"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/admin/platform-updates/<id>/ship
# ---------------------------------------------------------------------------


class TestShipPlatformUpdate:
    """POST /api/v1/admin/platform-updates/<id>/ship — platform team only."""

    @patch("skillhub_flask.blueprints.roadmap.ship_update")
    @patch("skillhub_flask.blueprints.roadmap.get_db")
    def test_success_returns_200_with_version_tag(
        self, mock_get_db: MagicMock, mock_ship: MagicMock, client: Any
    ) -> None:
        mock_get_db.return_value = MagicMock()
        mock_ship.return_value = {**_SHIPPED_RESULT}

        token = _platform_token()
        resp = client.post(
            f"/api/v1/admin/platform-updates/{_UPDATE_ID}/ship",
            json={"version_tag": "v1.2.0", "changelog_body": "Released the new feature for all users"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        # BUG #6: version_tag extracted from body
        assert "version_tag" in data
        assert data["version_tag"] == "v1.2.0"

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.post(
            f"/api/v1/admin/platform-updates/{_UPDATE_ID}/ship",
            json={"version_tag": "v1.0", "changelog_body": "Released new stuff here"},
        )
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.post(
            f"/api/v1/admin/platform-updates/{_UPDATE_ID}/ship",
            json={"version_tag": "v1.0", "changelog_body": "Released new stuff here"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/v1/admin/platform-updates/<id>
# ---------------------------------------------------------------------------


class TestDeletePlatformUpdate:
    """DELETE /api/v1/admin/platform-updates/<id> — SECURITY TEAM only (not platform!)."""

    @patch("skillhub_flask.blueprints.roadmap.delete_update")
    @patch("skillhub_flask.blueprints.roadmap.get_db")
    def test_success_security_team_returns_200(
        self, mock_get_db: MagicMock, mock_delete: MagicMock, client: Any
    ) -> None:
        mock_get_db.return_value = MagicMock()
        mock_delete.return_value = {**_UPDATE_RESULT, "status": "deleted"}

        token = _security_token()
        resp = client.delete(
            f"/api/v1/admin/platform-updates/{_UPDATE_ID}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200

    def test_platform_team_returns_403(self, client: Any) -> None:
        """Platform team does NOT have delete access — only security team."""
        token = _platform_token()
        resp = client.delete(
            f"/api/v1/admin/platform-updates/{_UPDATE_ID}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403

    def test_regular_user_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.delete(
            f"/api/v1/admin/platform-updates/{_UPDATE_ID}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.delete(f"/api/v1/admin/platform-updates/{_UPDATE_ID}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/changelog — PUBLIC (no auth required)
# ---------------------------------------------------------------------------


class TestGetChangelog:
    """GET /api/v1/changelog — public, no auth required."""

    @patch("skillhub_flask.blueprints.roadmap.list_updates")
    @patch("skillhub_flask.blueprints.roadmap.get_db")
    def test_success_no_auth_returns_200(self, mock_get_db: MagicMock, mock_list: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_list.return_value = ([{**_SHIPPED_RESULT}], 1)

        # No auth headers — this is a public endpoint
        resp = client.get("/api/v1/changelog")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["items"]) == 1
        # BUG #6: version_tag extracted from body text
        item = data["items"][0]
        assert "version_tag" in item
        assert item["version_tag"] == "v1.2.0"

    @patch("skillhub_flask.blueprints.roadmap.list_updates")
    @patch("skillhub_flask.blueprints.roadmap.get_db")
    def test_version_tag_none_when_not_in_body(
        self, mock_get_db: MagicMock, mock_list: MagicMock, client: Any
    ) -> None:
        mock_get_db.return_value = MagicMock()
        result_no_tag = {**_SHIPPED_RESULT, "body": "Simple body without version info"}
        mock_list.return_value = ([result_no_tag], 1)

        resp = client.get("/api/v1/changelog")
        assert resp.status_code == 200
        data = resp.get_json()
        item = data["items"][0]
        assert item["version_tag"] is None

    @patch("skillhub_flask.blueprints.roadmap.list_updates")
    @patch("skillhub_flask.blueprints.roadmap.get_db")
    def test_calls_list_updates_with_shipped_status(
        self, mock_get_db: MagicMock, mock_list: MagicMock, client: Any
    ) -> None:
        mock_get_db.return_value = MagicMock()
        mock_list.return_value = ([], 0)

        resp = client.get("/api/v1/changelog")
        assert resp.status_code == 200
        mock_list.assert_called_once_with(mock_get_db.return_value, status="shipped", page=1, per_page=100)
