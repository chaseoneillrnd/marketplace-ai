"""Tests for admin blueprint — feature, deprecate, remove, trending, audit log, users."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tests.conftest import make_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _platform_token() -> str:
    return make_token(
        payload={
            "sub": "admin",
            "user_id": str(uuid4()),
            "division": "eng",
            "is_platform_team": True,
            "is_security_team": False,
        }
    )


def _security_token() -> str:
    return make_token(
        payload={
            "sub": "admin",
            "user_id": str(uuid4()),
            "division": "eng",
            "is_platform_team": False,
            "is_security_team": True,
        }
    )


def _regular_token() -> str:
    return make_token(
        payload={
            "sub": "user",
            "user_id": str(uuid4()),
            "division": "eng",
            "is_platform_team": False,
            "is_security_team": False,
        }
    )


# ---------------------------------------------------------------------------
# POST /api/v1/admin/skills/<slug>/feature
# ---------------------------------------------------------------------------


class TestFeatureSkill:
    """POST /admin/skills/<slug>/feature — platform team only."""

    @patch("skillhub_flask.blueprints.admin.feature_skill")
    def test_feature_200_platform(self, mock_fs: MagicMock, client: Any) -> None:
        mock_fs.return_value = {
            "slug": "my-skill",
            "featured": True,
            "featured_order": 1,
        }
        resp = client.post(
            "/api/v1/admin/skills/my-skill/feature",
            json={"featured": True, "featured_order": 1},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["featured"] is True
        assert data["slug"] == "my-skill"
        mock_fs.assert_called_once()

    def test_feature_403_regular(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/admin/skills/my-skill/feature",
            json={"featured": True},
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403

    def test_feature_401_no_token(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/admin/skills/my-skill/feature",
            json={"featured": True},
        )
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.admin.feature_skill")
    def test_feature_404_not_found(self, mock_fs: MagicMock, client: Any) -> None:
        mock_fs.side_effect = ValueError("Skill not found")
        resp = client.post(
            "/api/v1/admin/skills/missing/feature",
            json={"featured": True},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/admin/skills/<slug>/deprecate
# ---------------------------------------------------------------------------


class TestDeprecateSkill:
    """POST /admin/skills/<slug>/deprecate — platform team only."""

    @patch("skillhub_flask.blueprints.admin.deprecate_skill")
    def test_deprecate_200_platform(self, mock_ds: MagicMock, client: Any) -> None:
        mock_ds.return_value = {
            "slug": "old-skill",
            "status": "deprecated",
            "deprecated_at": "2026-03-01T00:00:00",
        }
        resp = client.post(
            "/api/v1/admin/skills/old-skill/deprecate",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "deprecated"
        mock_ds.assert_called_once()

    def test_deprecate_403_regular(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/admin/skills/old-skill/deprecate",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403

    def test_deprecate_401_no_token(self, client: Any) -> None:
        resp = client.post("/api/v1/admin/skills/old-skill/deprecate")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.admin.deprecate_skill")
    def test_deprecate_404_not_found(self, mock_ds: MagicMock, client: Any) -> None:
        mock_ds.side_effect = ValueError("Skill not found")
        resp = client.post(
            "/api/v1/admin/skills/missing/deprecate",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/admin/skills/<slug> — security_team required
# ---------------------------------------------------------------------------


class TestRemoveSkill:
    """DELETE /admin/skills/<slug> — security team only."""

    @patch("skillhub_flask.blueprints.admin.remove_skill")
    def test_remove_200_security(self, mock_rs: MagicMock, client: Any) -> None:
        mock_rs.return_value = {"slug": "bad-skill", "status": "removed"}
        resp = client.delete(
            "/api/v1/admin/skills/bad-skill",
            headers=_auth_headers(_security_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "removed"
        mock_rs.assert_called_once()

    def test_remove_403_platform_only(self, client: Any) -> None:
        """Platform team without security flag should be rejected."""
        resp = client.delete(
            "/api/v1/admin/skills/bad-skill",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 403

    def test_remove_401_no_token(self, client: Any) -> None:
        resp = client.delete("/api/v1/admin/skills/bad-skill")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.admin.remove_skill")
    def test_remove_404_not_found(self, mock_rs: MagicMock, client: Any) -> None:
        mock_rs.side_effect = ValueError("Skill not found")
        resp = client.delete(
            "/api/v1/admin/skills/missing",
            headers=_auth_headers(_security_token()),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/admin/recalculate-trending
# ---------------------------------------------------------------------------


class TestRecalculateTrending:
    """POST /admin/recalculate-trending — platform team only."""

    @patch("skillhub.services.skills.recalculate_trending_scores")
    def test_trending_200_platform(self, mock_rt: MagicMock, client: Any) -> None:
        mock_rt.return_value = 42
        resp = client.post(
            "/api/v1/admin/recalculate-trending",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        assert resp.get_json()["updated"] == 42

    def test_trending_403_regular(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/admin/recalculate-trending",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/admin/audit-log
# ---------------------------------------------------------------------------


class TestAuditLog:
    """GET /admin/audit-log — platform team only."""

    @patch("skillhub_flask.blueprints.admin.query_audit_log")
    def test_audit_log_200_platform(self, mock_ql: MagicMock, client: Any) -> None:
        entry_id = str(uuid4())
        actor_id = str(uuid4())
        mock_ql.return_value = (
            [
                {
                    "id": entry_id,
                    "event_type": "skill.featured",
                    "actor_id": actor_id,
                    "actor_name": "Admin User",
                    "target_type": "skill",
                    "target_id": "my-skill",
                    "metadata": {},
                    "ip_address": "127.0.0.1",
                    "created_at": "2026-01-01T00:00:00",
                }
            ],
            1,
        )
        resp = client.get(
            "/api/v1/admin/audit-log",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["page"] == 1
        assert data["has_more"] is False

    def test_audit_log_403_regular(self, client: Any) -> None:
        resp = client.get(
            "/api/v1/admin/audit-log",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/admin/users
# ---------------------------------------------------------------------------


class TestListUsers:
    """GET /admin/users — platform team only."""

    @patch("skillhub_flask.blueprints.admin.list_users")
    def test_users_200_platform(self, mock_lu: MagicMock, client: Any) -> None:
        uid = str(uuid4())
        mock_lu.return_value = (
            [
                {
                    "id": uid,
                    "email": "alice@example.com",
                    "username": "alice",
                    "name": "Alice Admin",
                    "division": "eng",
                    "role": "admin",
                    "is_platform_team": True,
                    "is_security_team": False,
                    "created_at": "2026-01-01T00:00:00",
                    "last_login_at": None,
                }
            ],
            1,
        )
        resp = client.get(
            "/api/v1/admin/users",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["username"] == "alice"

    def test_users_403_regular(self, client: Any) -> None:
        resp = client.get(
            "/api/v1/admin/users",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /api/v1/admin/users/<user_id>
# ---------------------------------------------------------------------------


class TestUpdateUser:
    """PATCH /admin/users/<user_id> — platform team only."""

    @patch("skillhub_flask.blueprints.admin.update_user")
    def test_update_user_200_platform(self, mock_uu: MagicMock, client: Any) -> None:
        uid = str(uuid4())
        mock_uu.return_value = {
            "id": uid,
            "email": "bob@example.com",
            "username": "bob",
            "name": "Bob User",
            "division": "eng",
            "role": "viewer",
            "is_platform_team": False,
            "is_security_team": False,
        }
        resp = client.patch(
            f"/api/v1/admin/users/{uid}",
            json={"role": "viewer"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["role"] == "viewer"
        mock_uu.assert_called_once()

    def test_update_user_403_regular(self, client: Any) -> None:
        uid = str(uuid4())
        resp = client.patch(
            f"/api/v1/admin/users/{uid}",
            json={"role": "viewer"},
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403

    @patch("skillhub_flask.blueprints.admin.update_user")
    def test_update_user_404_not_found(self, mock_uu: MagicMock, client: Any) -> None:
        mock_uu.side_effect = ValueError("User not found")
        uid = str(uuid4())
        resp = client.patch(
            f"/api/v1/admin/users/{uid}",
            json={"role": "viewer"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 404
