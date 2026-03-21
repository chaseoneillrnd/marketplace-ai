"""Tests for admin endpoints — feature, deprecate, remove skills, audit log."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from tests.conftest import _make_settings, make_token

PLATFORM_USER_ID = "00000000-0000-0000-0000-000000000001"
SECURITY_USER_ID = "00000000-0000-0000-0000-000000000002"
REGULAR_USER_ID = "00000000-0000-0000-0000-000000000003"


def _platform_token() -> str:
    return make_token(
        {
            "sub": "platform-admin",
            "user_id": PLATFORM_USER_ID,
            "division": "engineering",
            "is_platform_team": True,
            "is_security_team": False,
        }
    )


def _security_token() -> str:
    return make_token(
        {
            "sub": "security-admin",
            "user_id": SECURITY_USER_ID,
            "division": "security",
            "is_platform_team": False,
            "is_security_team": True,
        }
    )


def _regular_token() -> str:
    return make_token(
        {
            "sub": "regular-user",
            "user_id": REGULAR_USER_ID,
            "division": "engineering",
            "is_platform_team": False,
            "is_security_team": False,
        }
    )


@pytest.fixture()
def mock_db() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def client(mock_db: MagicMock) -> TestClient:
    settings = _make_settings()
    application = create_app(settings=settings)
    application.dependency_overrides[get_db] = lambda: mock_db
    return TestClient(application)


class TestFeatureSkill:
    """POST /api/v1/admin/skills/{slug}/feature tests."""

    def test_non_platform_team_gets_403_on_feature(self, client: TestClient) -> None:
        """Regular user cannot feature a skill."""
        response = client.post(
            "/api/v1/admin/skills/test-skill/feature",
            json={"featured": True, "featured_order": 1},
            headers={"Authorization": f"Bearer {_regular_token()}"},
        )
        assert response.status_code == 403

    @patch("skillhub.services.admin.Skill", create=True)
    def test_feature_skill_sets_featured(
        self, _mock_skill_cls: MagicMock, client: TestClient, mock_db: MagicMock
    ) -> None:
        """Platform team can feature a skill."""
        mock_skill = MagicMock()
        mock_skill.slug = "test-skill"
        mock_skill.featured = True
        mock_skill.featured_order = 1

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_skill

        response = client.post(
            "/api/v1/admin/skills/test-skill/feature",
            json={"featured": True, "featured_order": 1},
            headers={"Authorization": f"Bearer {_platform_token()}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "test-skill"
        assert data["featured"] is True
        assert data["featured_order"] == 1

    def test_feature_skill_not_found(self, client: TestClient, mock_db: MagicMock) -> None:
        """Featuring a nonexistent skill returns 404."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        response = client.post(
            "/api/v1/admin/skills/nonexistent/feature",
            json={"featured": True},
            headers={"Authorization": f"Bearer {_platform_token()}"},
        )
        assert response.status_code == 404


class TestDeprecateSkill:
    """POST /api/v1/admin/skills/{slug}/deprecate tests."""

    def test_non_platform_team_gets_403_on_deprecate(self, client: TestClient) -> None:
        """Regular user cannot deprecate a skill."""
        response = client.post(
            "/api/v1/admin/skills/test-skill/deprecate",
            headers={"Authorization": f"Bearer {_regular_token()}"},
        )
        assert response.status_code == 403

    @patch("skillhub.services.admin.Skill", create=True)
    def test_deprecate_skill_sets_deprecated_at(
        self, _mock_skill_cls: MagicMock, client: TestClient, mock_db: MagicMock
    ) -> None:
        """Platform team can deprecate a skill, which sets deprecated_at."""
        now = datetime.now(timezone.utc)
        mock_skill = MagicMock()
        mock_skill.slug = "test-skill"
        mock_skill.status = MagicMock()
        mock_skill.status.value = "deprecated"
        mock_skill.deprecated_at = now

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_skill

        response = client.post(
            "/api/v1/admin/skills/test-skill/deprecate",
            headers={"Authorization": f"Bearer {_platform_token()}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "test-skill"
        assert data["status"] == "deprecated"
        assert data["deprecated_at"] is not None


class TestRemoveSkill:
    """DELETE /api/v1/admin/skills/{slug} tests."""

    def test_non_security_team_gets_403_on_delete(self, client: TestClient) -> None:
        """Regular user cannot remove a skill."""
        response = client.delete(
            "/api/v1/admin/skills/test-skill",
            headers={"Authorization": f"Bearer {_regular_token()}"},
        )
        assert response.status_code == 403

    def test_platform_team_without_security_gets_403(self, client: TestClient) -> None:
        """Platform team member without security role cannot remove a skill."""
        response = client.delete(
            "/api/v1/admin/skills/test-skill",
            headers={"Authorization": f"Bearer {_platform_token()}"},
        )
        assert response.status_code == 403

    @patch("skillhub.services.admin.AuditLog", create=True)
    @patch("skillhub.services.admin.Skill", create=True)
    def test_remove_skill_sets_status_removed_not_physical_delete(
        self,
        _mock_skill_cls: MagicMock,
        _mock_audit_cls: MagicMock,
        client: TestClient,
        mock_db: MagicMock,
    ) -> None:
        """Security team soft-removes a skill (status=removed, not deleted from DB)."""
        mock_skill = MagicMock()
        mock_skill.slug = "test-skill"
        mock_skill.id = uuid.uuid4()
        mock_skill.status = MagicMock()
        mock_skill.status.value = "removed"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_skill

        response = client.delete(
            "/api/v1/admin/skills/test-skill",
            headers={"Authorization": f"Bearer {_security_token()}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "test-skill"
        assert data["status"] == "removed"
        # Verify the skill was NOT physically deleted from db
        mock_db.delete.assert_not_called()

    @patch("skillhub.services.admin.AuditLog", create=True)
    @patch("skillhub.services.admin.Skill", create=True)
    def test_remove_skill_writes_audit_log(
        self,
        _mock_skill_cls: MagicMock,
        _mock_audit_cls: MagicMock,
        client: TestClient,
        mock_db: MagicMock,
    ) -> None:
        """Removing a skill writes an audit log entry."""
        mock_skill = MagicMock()
        mock_skill.slug = "test-skill"
        mock_skill.id = uuid.uuid4()
        mock_skill.status = MagicMock()
        mock_skill.status.value = "removed"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_skill

        response = client.delete(
            "/api/v1/admin/skills/test-skill",
            headers={"Authorization": f"Bearer {_security_token()}"},
        )
        assert response.status_code == 200
        # Verify db.add was called (for the audit log entry)
        mock_db.add.assert_called_once()
        # Verify db.commit was called
        mock_db.commit.assert_called()


class TestAuditLog:
    """GET /api/v1/admin/audit-log tests."""

    def test_non_platform_team_gets_403_on_audit_log(self, client: TestClient) -> None:
        """Regular user cannot access the audit log."""
        response = client.get(
            "/api/v1/admin/audit-log",
            headers={"Authorization": f"Bearer {_regular_token()}"},
        )
        assert response.status_code == 403

    @patch("skillhub.services.admin.User", create=True)
    @patch("skillhub.services.admin.AuditLog", create=True)
    def test_audit_log_returns_entries(
        self,
        _mock_audit_cls: MagicMock,
        _mock_user_cls: MagicMock,
        client: TestClient,
        mock_db: MagicMock,
    ) -> None:
        """Platform team can query audit log entries."""
        actor_uuid = uuid.UUID(PLATFORM_USER_ID)
        entry = MagicMock()
        entry.id = uuid.uuid4()
        entry.event_type = "skill.removed"
        entry.actor_id = actor_uuid
        entry.target_type = "skill"
        entry.target_id = str(uuid.uuid4())
        entry.metadata_ = {"slug": "test-skill"}
        entry.ip_address = "127.0.0.1"
        entry.created_at = datetime.now(timezone.utc)

        user_row = MagicMock()
        user_row.id = actor_uuid
        user_row.name = "Platform Admin"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.side_effect = [[entry], [user_row]]

        response = client.get(
            "/api/v1/admin/audit-log",
            headers={"Authorization": f"Bearer {_platform_token()}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert data["has_more"] is False
        assert len(data["items"]) == 1
        assert data["items"][0]["event_type"] == "skill.removed"

    @patch("skillhub.services.admin.AuditLog", create=True)
    def test_audit_log_query_with_event_type_filter(
        self,
        _mock_audit_cls: MagicMock,
        client: TestClient,
        mock_db: MagicMock,
    ) -> None:
        """Audit log query filters by event_type."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []

        response = client.get(
            "/api/v1/admin/audit-log?event_type=skill.removed",
            headers={"Authorization": f"Bearer {_platform_token()}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        # Verify filter was called (the query chain was exercised)
        mock_query.filter.assert_called()

    def test_unauthenticated_gets_401_on_audit_log(self, client: TestClient) -> None:
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/admin/audit-log")
        assert response.status_code == 401
