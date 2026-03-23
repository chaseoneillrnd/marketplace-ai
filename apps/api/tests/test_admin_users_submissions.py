"""Tests for admin user management (#17) and submission queue (#18) endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from skillhub.services.admin import list_all_submissions, list_users, update_user
from tests.conftest import _make_settings, make_token

ADMIN_USER_ID = str(uuid.uuid4())
REGULAR_USER_ID = str(uuid.uuid4())
TARGET_USER_ID = str(uuid.uuid4())


def _admin_headers() -> dict[str, str]:
    token = make_token({
        "sub": "admin",
        "user_id": ADMIN_USER_ID,
        "division": "engineering",
        "role": "admin",
        "is_platform_team": True,
        "is_security_team": False,
        "name": "Admin User",
    })
    return {"Authorization": f"Bearer {token}"}


def _regular_headers() -> dict[str, str]:
    token = make_token({
        "sub": "regular",
        "user_id": REGULAR_USER_ID,
        "division": "engineering",
        "role": "user",
        "is_platform_team": False,
        "is_security_team": False,
        "name": "Regular User",
    })
    return {"Authorization": f"Bearer {token}"}


def _make_client(db_mock: MagicMock) -> TestClient:
    settings = _make_settings()
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = lambda: db_mock
    return TestClient(app)


# --- #17: Admin User List ---


class TestAdminListUsers:
    """Test GET /api/v1/admin/users."""

    @patch("skillhub.routers.admin.list_users")
    def test_list_users_returns_paginated_response(self, mock_list: MagicMock) -> None:
        user_id = uuid.uuid4()
        mock_list.return_value = (
            [
                {
                    "id": user_id,
                    "email": "alice@example.com",
                    "username": "alice",
                    "name": "Alice",
                    "division": "engineering",
                    "role": "developer",
                    "is_platform_team": False,
                    "is_security_team": False,
                    "created_at": datetime.now(UTC),
                    "last_login_at": None,
                }
            ],
            1,
        )
        client = _make_client(MagicMock())
        response = client.get("/api/v1/admin/users", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["username"] == "alice"
        assert data["has_more"] is False

    @patch("skillhub.routers.admin.list_users")
    def test_list_users_passes_filters(self, mock_list: MagicMock) -> None:
        mock_list.return_value = ([], 0)
        client = _make_client(MagicMock())
        response = client.get(
            "/api/v1/admin/users?division=marketing&role=manager&is_platform_team=true",
            headers=_admin_headers(),
        )
        assert response.status_code == 200
        call_kwargs = mock_list.call_args
        assert call_kwargs.kwargs["division"] == "marketing"
        assert call_kwargs.kwargs["role"] == "manager"
        assert call_kwargs.kwargs["is_platform_team"] is True

    def test_list_users_requires_platform_team(self) -> None:
        client = _make_client(MagicMock())
        response = client.get("/api/v1/admin/users", headers=_regular_headers())
        assert response.status_code == 403

    def test_list_users_requires_auth(self) -> None:
        client = _make_client(MagicMock())
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401


# --- #17: Admin User Update ---


class TestAdminUpdateUser:
    """Test PATCH /api/v1/admin/users/{user_id}."""

    @patch("skillhub.routers.admin.update_user")
    def test_update_user_role_succeeds(self, mock_update: MagicMock) -> None:
        user_id = uuid.uuid4()
        mock_update.return_value = {
            "id": user_id,
            "email": "alice@example.com",
            "username": "alice",
            "name": "Alice",
            "division": "engineering",
            "role": "lead",
            "is_platform_team": False,
            "is_security_team": False,
        }
        client = _make_client(MagicMock())
        response = client.patch(
            f"/api/v1/admin/users/{user_id}",
            json={"role": "lead"},
            headers=_admin_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "lead"

    @patch("skillhub.routers.admin.update_user")
    def test_update_user_team_flags(self, mock_update: MagicMock) -> None:
        user_id = uuid.uuid4()
        mock_update.return_value = {
            "id": user_id,
            "email": "bob@example.com",
            "username": "bob",
            "name": "Bob",
            "division": "engineering",
            "role": "user",
            "is_platform_team": True,
            "is_security_team": True,
        }
        client = _make_client(MagicMock())
        response = client.patch(
            f"/api/v1/admin/users/{user_id}",
            json={"is_platform_team": True, "is_security_team": True},
            headers=_admin_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_platform_team"] is True
        assert data["is_security_team"] is True

    @patch("skillhub.routers.admin.update_user")
    def test_update_user_not_found_returns_404(self, mock_update: MagicMock) -> None:
        mock_update.side_effect = ValueError("User not found")
        client = _make_client(MagicMock())
        response = client.patch(
            f"/api/v1/admin/users/{uuid.uuid4()}",
            json={"role": "admin"},
            headers=_admin_headers(),
        )
        assert response.status_code == 404

    def test_update_user_requires_platform_team(self) -> None:
        client = _make_client(MagicMock())
        response = client.patch(
            f"/api/v1/admin/users/{uuid.uuid4()}",
            json={"role": "admin"},
            headers=_regular_headers(),
        )
        assert response.status_code == 403


# --- #17: Admin User Service Tests ---


class TestAdminUserService:
    """Test service-layer functions for user management."""

    def test_list_users_basic(self) -> None:
        db = MagicMock()
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.username = "testuser"
        user.name = "Test User"
        user.division = "engineering"
        user.role = "developer"
        user.is_platform_team = False
        user.is_security_team = False
        user.created_at = datetime.now(UTC)
        user.last_login_at = None

        db.query.return_value.count.return_value = 1
        db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [user]

        items, total = list_users(db, page=1, per_page=20)
        assert total == 1
        assert len(items) == 1
        assert items[0]["username"] == "testuser"

    def test_list_users_with_division_filter(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        items, total = list_users(db, division="marketing", page=1, per_page=20)
        assert total == 0
        assert items == []

    def test_update_user_applies_changes_and_writes_audit_log(self) -> None:
        db = MagicMock()
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.username = "testuser"
        user.name = "Test User"
        user.division = "engineering"
        user.role = "developer"
        user.is_platform_team = False
        user.is_security_team = False

        db.query.return_value.filter.return_value.first.return_value = user

        result = update_user(
            db,
            user_id=str(user.id),
            updates={"role": "lead", "is_platform_team": True},
            actor_id=ADMIN_USER_ID,
        )

        # Audit log entry should have been added
        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result["id"] == user.id

    def test_update_user_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="User not found"):
            update_user(db, user_id=str(uuid.uuid4()), updates={"role": "admin"})

    def test_update_user_no_changes_skips_audit_log(self) -> None:
        db = MagicMock()
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.username = "testuser"
        user.name = "Test User"
        user.division = "engineering"
        user.role = "developer"
        user.is_platform_team = False
        user.is_security_team = False

        db.query.return_value.filter.return_value.first.return_value = user

        # Pass the same role value — no change
        result = update_user(
            db,
            user_id=str(user.id),
            updates={"role": "developer"},
        )

        db.add.assert_not_called()
        db.commit.assert_not_called()
        assert result["role"] == "developer"


# --- #18: Admin Submission Queue ---
# NOTE: The admin submissions endpoint (GET /api/v1/admin/submissions) already
# exists in skillhub/routers/submissions.py. Tests below target that endpoint.


class TestAdminSubmissionQueue:
    """Test GET /api/v1/admin/submissions (lives in submissions router)."""

    @patch("skillhub.routers.submissions.list_admin_submissions")
    def test_list_submissions_returns_paginated_response(self, mock_list: MagicMock) -> None:
        sub_id = uuid.uuid4()
        submitter_id = uuid.uuid4()
        mock_list.return_value = (
            [
                {
                    "id": sub_id,
                    "display_id": "SUB-001",
                    "name": "My Skill",
                    "short_desc": "A skill",
                    "category": "engineering",
                    "status": "submitted",
                    "submitted_by": submitter_id,
                    "submitted_by_name": "Alice",
                    "declared_divisions": ["engineering"],
                    "created_at": datetime.now(UTC),
                }
            ],
            1,
        )
        client = _make_client(MagicMock())
        response = client.get("/api/v1/admin/submissions", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["display_id"] == "SUB-001"

    @patch("skillhub.routers.submissions.list_admin_submissions")
    def test_list_submissions_with_status_filter(self, mock_list: MagicMock) -> None:
        mock_list.return_value = ([], 0)
        client = _make_client(MagicMock())
        response = client.get(
            "/api/v1/admin/submissions?status_filter=approved",
            headers=_admin_headers(),
        )
        assert response.status_code == 200
        call_kwargs = mock_list.call_args
        assert call_kwargs.kwargs["status_filter"] == "approved"

    def test_list_submissions_requires_platform_team(self) -> None:
        client = _make_client(MagicMock())
        response = client.get("/api/v1/admin/submissions", headers=_regular_headers())
        assert response.status_code == 403

    def test_list_submissions_requires_auth(self) -> None:
        client = _make_client(MagicMock())
        response = client.get("/api/v1/admin/submissions")
        assert response.status_code == 401


# --- #18: Admin Submission Service Tests ---


class TestAdminSubmissionService:
    """Test service-layer function for listing all submissions."""

    def test_list_all_submissions_basic(self) -> None:
        db = MagicMock()
        sub = MagicMock()
        sub.id = uuid.uuid4()
        sub.display_id = "SUB-001"
        sub.name = "Test Skill"
        sub.short_desc = "A skill"
        sub.category = "engineering"
        sub.status = MagicMock(value="submitted")
        sub.submitted_by = uuid.uuid4()
        sub.declared_divisions = ["engineering"]
        sub.created_at = datetime.now(UTC)

        user_row = MagicMock()
        user_row.id = sub.submitted_by
        user_row.name = "Alice"

        db.query.return_value.count.return_value = 1
        db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sub]
        # Second db.query call for resolving user names
        db.query.return_value.filter.return_value.all.return_value = [user_row]

        items, total = list_all_submissions(db, page=1, per_page=20)
        assert total == 1
        assert len(items) == 1
        assert items[0]["display_id"] == "SUB-001"
        assert items[0]["submitted_by_name"] == "Alice"

    def test_list_all_submissions_with_status_filter(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        items, total = list_all_submissions(db, status_filter="approved", page=1, per_page=20)
        assert total == 0
        assert items == []

    def test_list_all_submissions_pagination(self) -> None:
        db = MagicMock()
        db.query.return_value.count.return_value = 25
        db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        items, total = list_all_submissions(db, page=2, per_page=10)
        assert total == 25
        # Verify offset was called with correct value
        db.query.return_value.order_by.return_value.offset.assert_called_with(10)
