"""Comprehensive tests for division access control enforcement."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from skillhub.services.social import install_skill
from skillhub.services.submissions import create_access_request, review_access_request
from tests.conftest import _make_settings, make_token

USER_ID = str(uuid.uuid4())
ADMIN_USER_ID = str(uuid.uuid4())
SKILL_ID = uuid.uuid4()


def _auth_headers(
    division: str = "engineering",
    is_platform_team: bool = False,
    user_id: str = USER_ID,
) -> dict[str, str]:
    token = make_token({
        "sub": "test-user",
        "user_id": user_id,
        "division": division,
        "role": "user",
        "is_platform_team": is_platform_team,
        "is_security_team": False,
        "name": "Test User",
    })
    return {"Authorization": f"Bearer {token}"}


def _admin_headers() -> dict[str, str]:
    return _auth_headers(user_id=ADMIN_USER_ID, is_platform_team=True)


def _make_client(db_mock: MagicMock) -> TestClient:
    settings = _make_settings()
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = lambda: db_mock
    return TestClient(app)


def _mock_skill(**overrides: Any) -> MagicMock:
    """Create a mock Skill object."""
    skill = MagicMock()
    skill.id = overrides.get("id", SKILL_ID)
    skill.slug = overrides.get("slug", "test-skill")
    skill.name = overrides.get("name", "Test Skill")
    skill.short_desc = overrides.get("short_desc", "A test")
    skill.category = overrides.get("category", "engineering")
    skill.author_id = overrides.get("author_id", uuid.uuid4())
    skill.current_version = overrides.get("current_version", "1.0.0")
    skill.install_method = overrides.get("install_method", "all")
    skill.install_count = overrides.get("install_count", 0)
    skill.fork_count = overrides.get("fork_count", 0)
    skill.favorite_count = overrides.get("favorite_count", 0)
    return skill


# --- Install Blocked by Division ---


class TestInstallDivisionBlocked:
    """Test install is blocked when user division is not in skill.divisions."""

    def test_install_unauthorized_division_raises_permission_error(self) -> None:
        """Service layer raises PermissionError for wrong division."""
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        # has_divisions = 1 (skill has division restrictions)
        # user_in_division = 0 (user not in allowed divisions)
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 0]

        with pytest.raises(PermissionError, match="division_restricted"):
            install_skill(
                db, "test-skill", uuid.UUID(USER_ID), "marketing", "claude-code", "1.0.0"
            )

    def test_install_authorized_division_succeeds(self) -> None:
        """Service layer allows install for correct division."""
        db = MagicMock()
        skill = _mock_skill()
        # First .first() returns skill, second returns None (no existing install)
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 1]
        db.refresh = MagicMock()

        result = install_skill(
            db, "test-skill", uuid.UUID(USER_ID), "engineering", "claude-code", "1.0.0"
        )
        assert result["skill_id"] == SKILL_ID

    def test_install_no_division_restrictions_always_succeeds(self) -> None:
        """Skills with no division rows are accessible to everyone."""
        db = MagicMock()
        skill = _mock_skill()
        # First .first() returns skill, second returns None (no existing install)
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]
        # has_divisions = 0 (no restrictions)
        db.query.return_value.select_from.return_value.filter.return_value.scalar.return_value = 0

        result = install_skill(
            db, "test-skill", uuid.UUID(USER_ID), "any-division", "mcp", "2.0.0"
        )
        assert result["skill_id"] == SKILL_ID


# --- 403 Responses ---


class TestDivision403Responses:
    """Test that 403 responses contain correct error messages."""

    @patch("skillhub.routers.social.install_skill")
    def test_403_contains_division_restricted_error(
        self, mock_install: MagicMock
    ) -> None:
        mock_install.side_effect = PermissionError("division_restricted")
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/skills/test-skill/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(division="marketing"),
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "division_restricted"

    @patch("skillhub.routers.social.install_skill")
    def test_403_message_format(self, mock_install: MagicMock) -> None:
        """Error detail structure matches expected format."""
        mock_install.side_effect = PermissionError("division_restricted")
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/skills/test-skill/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(),
        )
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]


# --- Division Access Request Workflow ---


class TestDivisionAccessRequestWorkflow:
    """Test request -> approve -> install flow."""

    def test_create_access_request_for_restricted_skill(self) -> None:
        """User in wrong division can request access."""
        db = MagicMock()
        skill = _mock_skill()
        # skill found, division NOT authorized (None = no existing SkillDivision match)
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="pending"))
        )

        result = create_access_request(
            db,
            skill_slug="test-skill",
            user_id=uuid.UUID(USER_ID),
            user_division="marketing",
            reason="Need this for marketing campaigns",
        )

        assert result["status"] == "pending"
        assert result["user_division"] == "marketing"
        db.add.assert_called()

    def test_access_request_already_authorized_raises(self) -> None:
        """If user's division already has access, request is rejected."""
        db = MagicMock()
        skill = _mock_skill()
        # skill found, division IS authorized
        db.query.return_value.filter.return_value.first.side_effect = [
            skill, MagicMock()
        ]

        with pytest.raises(ValueError, match="already has access"):
            create_access_request(
                db,
                skill_slug="test-skill",
                user_id=uuid.UUID(USER_ID),
                user_division="engineering",
                reason="I already have access",
            )

    def test_approve_access_request_adds_division(self) -> None:
        """Approving an access request adds the division to the skill."""
        db = MagicMock()
        db.commit = MagicMock()
        db.add = MagicMock()

        access_req = MagicMock()
        access_req.id = uuid.uuid4()
        access_req.skill_id = SKILL_ID
        access_req.user_division = "marketing"
        db.query.return_value.filter.return_value.first.return_value = access_req

        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="approved"))
        )

        result = review_access_request(
            db, access_req.id, decision="approved", reviewer_id=uuid.uuid4()
        )
        assert result["status"] == "approved"
        # Should have added a SkillDivision row
        assert db.add.called

    def test_reject_access_request_does_not_add_division(self) -> None:
        """Rejecting an access request does NOT add the division."""
        db = MagicMock()
        db.commit = MagicMock()
        db.add = MagicMock()

        access_req = MagicMock()
        access_req.id = uuid.uuid4()
        access_req.skill_id = SKILL_ID
        access_req.user_division = "marketing"
        db.query.return_value.filter.return_value.first.return_value = access_req

        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="denied"))
        )

        result = review_access_request(
            db, access_req.id, decision="denied", reviewer_id=uuid.uuid4()
        )
        assert result["status"] == "denied"


# --- Admin Override ---


class TestAdminDivisionOverride:
    """Test that platform team members can bypass division restrictions."""

    @patch("skillhub.routers.submissions.list_access_requests")
    def test_admin_can_list_access_requests(self, mock_list: MagicMock) -> None:
        """Platform team can view all access requests."""
        mock_list.return_value = ([], 0)
        client = _make_client(MagicMock())
        response = client.get(
            "/api/v1/admin/access-requests",
            headers=_admin_headers(),
        )
        assert response.status_code == 200

    def test_non_admin_cannot_list_access_requests(self) -> None:
        """Regular user gets 403 on admin access requests endpoint."""
        client = _make_client(MagicMock())
        response = client.get(
            "/api/v1/admin/access-requests",
            headers=_auth_headers(),
        )
        assert response.status_code == 403

    @patch("skillhub.routers.submissions.review_access_request")
    def test_admin_can_approve_access_request(self, mock_review: MagicMock) -> None:
        req_id = uuid.uuid4()
        mock_review.return_value = {
            "id": req_id,
            "status": "approved",
            "decision": "approved",
        }
        client = _make_client(MagicMock())
        response = client.post(
            f"/api/v1/admin/access-requests/{req_id}/review",
            json={"decision": "approved"},
            headers=_admin_headers(),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"


# --- Audit Log for Access Denials ---


class TestAuditLogAccessDenials:
    """Test audit log entries for division enforcement events."""

    def test_install_writes_audit_log_on_success(self) -> None:
        """Successful install writes audit_log entry."""
        db = MagicMock()
        skill = _mock_skill()
        # First .first() returns skill, second returns None (no existing install)
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 1]

        install_skill(db, "test-skill", uuid.UUID(USER_ID), "engineering", "claude-code", "1.0.0")

        # Should have called db.add at least twice: Install + AuditLog
        add_calls = db.add.call_args_list
        assert len(add_calls) >= 2

    def test_division_restricted_does_not_write_install(self) -> None:
        """Failed division check does not create install record."""
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 0]

        with pytest.raises(PermissionError):
            install_skill(
                db, "test-skill", uuid.UUID(USER_ID), "marketing", "claude-code", "1.0.0"
            )

        # db.commit should NOT have been called
        db.commit.assert_not_called()

    def test_skill_not_found_does_not_write_audit(self) -> None:
        """Nonexistent skill does not write any records."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError):
            install_skill(
                db, "nonexistent", uuid.UUID(USER_ID), "engineering", "claude-code", "1.0.0"
            )

        db.add.assert_not_called()
        db.commit.assert_not_called()


# --- Router-Level Access Request Endpoints ---


class TestAccessRequestRouterEndpoints:
    """Test the access request API endpoints."""

    @patch("skillhub.routers.submissions.create_access_request")
    def test_create_access_request_returns_201(self, mock_create: MagicMock) -> None:
        req_id = uuid.uuid4()
        mock_create.return_value = {
            "id": req_id,
            "skill_id": SKILL_ID,
            "requested_by": uuid.UUID(USER_ID),
            "user_division": "marketing",
            "reason": "Need access",
            "status": "pending",
            "created_at": "2026-01-01T00:00:00",
        }
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/skills/test-skill/access-request",
            json={"reason": "Need access"},
            headers=_auth_headers(division="marketing"),
        )
        assert response.status_code == 201
        assert response.json()["status"] == "pending"

    @patch("skillhub.routers.submissions.create_access_request")
    def test_already_authorized_returns_400(self, mock_create: MagicMock) -> None:
        mock_create.side_effect = ValueError("User's division already has access to this skill")
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/skills/test-skill/access-request",
            json={"reason": "I want it"},
            headers=_auth_headers(),
        )
        assert response.status_code == 400

    def test_unauthenticated_access_request_returns_401(self) -> None:
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/skills/test-skill/access-request",
            json={"reason": "Please"},
        )
        assert response.status_code == 401
