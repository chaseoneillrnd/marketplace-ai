"""Comprehensive tests for social layer — favorites, installs, forks, follows, counters, audit."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from skillhub.services.social import (
    favorite_skill,
    follow_user,
    fork_skill,
    install_skill,
    unfavorite_skill,
    uninstall_skill,
)
from tests.conftest import _make_settings, make_token

SKILL_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
AUTHOR_ID = uuid.uuid4()


def _mock_skill(**overrides: Any) -> MagicMock:
    skill = MagicMock()
    skill.id = overrides.get("id", SKILL_ID)
    skill.slug = overrides.get("slug", "test-skill")
    skill.name = overrides.get("name", "Test Skill")
    skill.short_desc = overrides.get("short_desc", "A test")
    skill.category = overrides.get("category", "engineering")
    skill.author_id = overrides.get("author_id", AUTHOR_ID)
    skill.current_version = overrides.get("current_version", "1.0.0")
    skill.install_method = overrides.get("install_method", "all")
    skill.data_sensitivity = overrides.get("data_sensitivity", "low")
    skill.external_calls = overrides.get("external_calls", False)
    skill.install_count = overrides.get("install_count", 0)
    skill.fork_count = overrides.get("fork_count", 0)
    skill.favorite_count = overrides.get("favorite_count", 0)
    return skill


def _auth_headers(**extra_claims: Any) -> dict[str, str]:
    claims: dict[str, Any] = {
        "user_id": str(USER_ID),
        "sub": "test-user",
        "name": "Test User",
        "division": "engineering",
        "role": "engineer",
        "is_platform_team": False,
        "is_security_team": False,
    }
    claims.update(extra_claims)
    token = make_token(claims)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def mock_db() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def app_with_db(mock_db: MagicMock) -> Any:
    settings = _make_settings()
    application = create_app(settings=settings)
    application.dependency_overrides[get_db] = lambda: mock_db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app_with_db: Any) -> TestClient:
    return TestClient(app_with_db)


@pytest.fixture()
def auth_headers_fixture() -> dict[str, str]:
    return _auth_headers()


# --- Favorite Toggle ---


class TestFavoriteToggle:
    """Test adding and removing favorites."""

    def test_first_favorite_creates_record(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]

        result = favorite_skill(db, "test-skill", USER_ID)

        assert result["skill_id"] == SKILL_ID
        assert result["user_id"] == USER_ID
        db.add.assert_called()
        db.commit.assert_called_once()

    def test_duplicate_favorite_is_idempotent(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        existing = MagicMock()
        existing.user_id = USER_ID
        existing.skill_id = SKILL_ID
        existing.created_at = datetime.now(UTC)
        db.query.return_value.filter.return_value.first.side_effect = [skill, existing]

        result = favorite_skill(db, "test-skill", USER_ID)

        assert result["user_id"] == USER_ID
        db.commit.assert_not_called()

    def test_unfavorite_removes_record(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        fav = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [skill, fav]

        unfavorite_skill(db, "test-skill", USER_ID)

        db.delete.assert_called_once_with(fav)
        db.commit.assert_called_once()

    def test_unfavorite_nonexistent_skill_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises((ValueError, AttributeError)):
            unfavorite_skill(db, "nonexistent", USER_ID)


# --- Install with Division Enforcement ---


class TestInstallWithDivision:
    """Test install respects division enforcement."""

    def test_install_authorized_creates_record(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        # First .first() returns skill, second returns None (no existing install)
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 1]
        db.refresh = MagicMock()

        result = install_skill(db, "test-skill", USER_ID, "engineering", "claude-code", "1.0.0")

        assert result["skill_id"] == SKILL_ID
        assert result["method"] == "claude-code"
        db.commit.assert_called_once()

    def test_install_unauthorized_raises(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 0]

        with pytest.raises(PermissionError, match="division_restricted"):
            install_skill(db, "test-skill", USER_ID, "marketing", "claude-code", "1.0.0")

    def test_install_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found"):
            install_skill(db, "nonexistent", USER_ID, "engineering", "claude-code", "1.0.0")

    def test_uninstall_sets_timestamp(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        install = MagicMock()
        install.uninstalled_at = None
        db.query.return_value.filter.return_value.first.side_effect = [skill, install]

        uninstall_skill(db, "test-skill", USER_ID)

        # uninstalled_at is now set via query-based update, verify update was called
        db.query.return_value.filter.return_value.update.assert_called()
        db.commit.assert_called_once()

    def test_uninstall_no_active_raises(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]

        with pytest.raises(ValueError, match="No active install"):
            uninstall_skill(db, "test-skill", USER_ID)


# --- Fork Creation ---


class TestForkCreation:
    """Test fork with upstream tracking."""

    def test_fork_creates_new_skill_and_fork_record(self) -> None:
        db = MagicMock()
        original = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = original

        result = fork_skill(db, "test-skill", USER_ID)

        assert result["original_skill_id"] == SKILL_ID
        assert result["forked_by"] == USER_ID
        assert "fork" in result["forked_skill_slug"]
        # Skill + Fork + AuditLog = at least 3 adds
        assert db.add.call_count >= 3
        db.commit.assert_called_once()

    def test_fork_increments_fork_count(self) -> None:
        db = MagicMock()
        original = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = original

        fork_skill(db, "test-skill", USER_ID)

        db.query.return_value.filter.return_value.update.assert_called()

    def test_fork_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises((ValueError, AttributeError)):
            fork_skill(db, "nonexistent", USER_ID)


# --- Follow / Unfollow ---


class TestFollowUnfollow:
    """Test follow/unfollow author."""

    def test_follow_creates_record(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]

        result = follow_user(db, "test-skill", USER_ID)

        assert result["followed_user_id"] == AUTHOR_ID
        assert result["follower_id"] == USER_ID
        db.add.assert_called()
        db.commit.assert_called_once()

    def test_follow_idempotent(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        existing = MagicMock()
        existing.follower_id = USER_ID
        existing.followed_user_id = AUTHOR_ID
        existing.created_at = datetime.now(UTC)
        db.query.return_value.filter.return_value.first.side_effect = [skill, existing]

        result = follow_user(db, "test-skill", USER_ID)

        assert result["follower_id"] == USER_ID
        db.commit.assert_not_called()


# --- Denormalized Counter Accuracy ---


class TestDenormalizedCounters:
    """Test that counters are correctly incremented/decremented."""

    def test_install_increments_install_count(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 1]

        install_skill(db, "test-skill", USER_ID, "engineering", "claude-code", "1.0.0")

        db.query.return_value.filter.return_value.update.assert_called()

    def test_fork_increments_fork_count(self) -> None:
        db = MagicMock()
        original = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = original

        fork_skill(db, "test-skill", USER_ID)

        db.query.return_value.filter.return_value.update.assert_called()

    def test_favorite_increments_favorite_count(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]

        favorite_skill(db, "test-skill", USER_ID)

        # Verify update was called for counter
        db.query.return_value.filter.return_value.update.assert_called()

    def test_unfavorite_decrements_favorite_count(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        fav = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [skill, fav]

        unfavorite_skill(db, "test-skill", USER_ID)

        # Should decrement
        db.query.return_value.filter.return_value.update.assert_called()


# --- Audit Log Entries ---


class TestSocialAuditLog:
    """Test audit log entries for social actions."""

    def test_install_creates_audit_entry(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 1]

        install_skill(db, "test-skill", USER_ID, "engineering", "claude-code", "1.0.0")

        add_calls = db.add.call_args_list
        assert len(add_calls) >= 2  # Install + AuditLog

    def test_fork_creates_audit_entry(self) -> None:
        db = MagicMock()
        original = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = original

        fork_skill(db, "test-skill", USER_ID)

        # Skill + Fork + AuditLog = at least 3
        assert db.add.call_count >= 3


# --- Router-Level Social Endpoints ---


class TestSocialRouterEndpoints:
    """Test router endpoints for social features."""

    @patch("skillhub.routers.social.install_skill")
    def test_install_returns_201(
        self, mock_install: MagicMock, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        mock_install.return_value = {
            "id": uuid.uuid4(),
            "skill_id": SKILL_ID,
            "user_id": USER_ID,
            "version": "1.0.0",
            "method": "claude-code",
            "installed_at": datetime.now(UTC),
        }
        response = client.post(
            "/api/v1/skills/test-skill/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=auth_headers_fixture,
        )
        assert response.status_code == 201

    @patch("skillhub.routers.social.favorite_skill")
    def test_favorite_returns_200(
        self, mock_fav: MagicMock, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        mock_fav.return_value = {
            "user_id": USER_ID,
            "skill_id": SKILL_ID,
            "created_at": datetime.now(UTC),
        }
        response = client.post(
            "/api/v1/skills/test-skill/favorite",
            headers=auth_headers_fixture,
        )
        assert response.status_code == 200

    @patch("skillhub.routers.social.unfavorite_skill")
    def test_unfavorite_returns_204(
        self, mock_unfav: MagicMock, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        mock_unfav.return_value = None
        response = client.delete(
            "/api/v1/skills/test-skill/favorite",
            headers=auth_headers_fixture,
        )
        assert response.status_code == 204

    @patch("skillhub.routers.social.fork_skill")
    def test_fork_returns_201(
        self, mock_fork: MagicMock, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        mock_fork.return_value = {
            "id": uuid.uuid4(),
            "original_skill_id": SKILL_ID,
            "forked_skill_id": uuid.uuid4(),
            "forked_skill_slug": "test-skill-fork-abc123",
            "forked_by": USER_ID,
        }
        response = client.post(
            "/api/v1/skills/test-skill/fork",
            headers=auth_headers_fixture,
        )
        assert response.status_code == 201

    @patch("skillhub.routers.social.follow_user")
    def test_follow_returns_200(
        self, mock_follow: MagicMock, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        mock_follow.return_value = {
            "follower_id": USER_ID,
            "followed_user_id": AUTHOR_ID,
            "created_at": datetime.now(UTC),
        }
        response = client.post(
            "/api/v1/skills/test-skill/follow",
            headers=auth_headers_fixture,
        )
        assert response.status_code == 200

    def test_install_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/install",
            json={"method": "claude-code", "version": "1.0.0"},
        )
        assert response.status_code == 401

    def test_fork_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.post("/api/v1/skills/test-skill/fork")
        assert response.status_code == 401

    def test_favorite_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.post("/api/v1/skills/test-skill/favorite")
        assert response.status_code == 401

    def test_invalid_install_method_returns_422(
        self, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/install",
            json={"method": "invalid-method", "version": "1.0.0"},
            headers=auth_headers_fixture,
        )
        assert response.status_code == 422
