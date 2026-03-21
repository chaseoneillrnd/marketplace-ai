"""Tests for social service — install, favorite, fork, follow with audit logging."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from skillhub.services.social import (
    favorite_skill,
    follow_user,
    fork_skill,
    install_skill,
    unfavorite_skill,
    uninstall_skill,
)

SKILL_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
AUTHOR_ID = uuid.uuid4()


def _mock_skill(**overrides: Any) -> MagicMock:
    """Create a mock Skill object."""
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


class TestInstallSkill:
    """Tests for install_skill service function."""

    def test_install_authorized_division_returns_201_data(self) -> None:
        """Install in authorized division succeeds."""
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        # count for has_divisions = 1
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 1]
        # After commit + refresh, the install should have attrs
        db.refresh = MagicMock()

        result = install_skill(
            db, "test-skill", USER_ID, "engineering", "claude-code", "1.0.0"
        )

        assert result["skill_id"] == SKILL_ID
        assert result["user_id"] == USER_ID
        assert result["method"] == "claude-code"
        assert result["version"] == "1.0.0"
        db.commit.assert_called_once()

    def test_install_unauthorized_division_raises_permission_error(self) -> None:
        """Install in unauthorized division raises PermissionError."""
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        # has_divisions > 0 but authorization check fails
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 0]

        with pytest.raises(PermissionError, match="division_restricted"):
            install_skill(
                db, "test-skill", USER_ID, "marketing", "claude-code", "1.0.0"
            )

    def test_install_writes_audit_log(self) -> None:
        """Install writes audit_log entry."""
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 1]

        install_skill(db, "test-skill", USER_ID, "engineering", "claude-code", "1.0.0")

        # Should have called db.add at least twice: once for Install, once for AuditLog
        add_calls = db.add.call_args_list
        assert len(add_calls) >= 2

    def test_install_increments_counter(self) -> None:
        """Install atomically increments install_count."""
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        db.query.return_value.select_from.return_value.filter.return_value.scalar.side_effect = [1, 1]

        install_skill(db, "test-skill", USER_ID, "engineering", "claude-code", "1.0.0")

        # Verify update was called (for counter increment)
        db.query.return_value.filter.return_value.update.assert_called()

    def test_install_skill_not_found_raises_value_error(self) -> None:
        """Install on non-existent skill raises ValueError."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found"):
            install_skill(
                db, "nonexistent", USER_ID, "engineering", "claude-code", "1.0.0"
            )

    def test_install_no_division_restrictions_succeeds(self) -> None:
        """Install on skill with no division restrictions always succeeds."""
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        # has_divisions = 0 (no restrictions)
        db.query.return_value.select_from.return_value.filter.return_value.scalar.return_value = 0

        result = install_skill(
            db, "test-skill", USER_ID, "any-division", "mcp", "2.0.0"
        )

        assert result["skill_id"] == SKILL_ID


class TestUninstallSkill:
    """Tests for uninstall_skill service function."""

    def test_uninstall_sets_uninstalled_at(self) -> None:
        """Uninstall sets uninstalled_at timestamp."""
        db = MagicMock()
        skill = _mock_skill()
        install = MagicMock()
        install.uninstalled_at = None
        db.query.return_value.filter.return_value.first.side_effect = [skill, install]

        uninstall_skill(db, "test-skill", USER_ID)

        assert install.uninstalled_at is not None
        db.commit.assert_called_once()

    def test_uninstall_no_active_install_raises(self) -> None:
        """Uninstall with no active install raises ValueError."""
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]

        with pytest.raises(ValueError, match="No active install"):
            uninstall_skill(db, "test-skill", USER_ID)


class TestFavoriteSkill:
    """Tests for favorite_skill and unfavorite_skill."""

    def test_favorite_creates_new(self) -> None:
        """First favorite creates new record."""
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]

        result = favorite_skill(db, "test-skill", USER_ID)

        assert result["skill_id"] == SKILL_ID
        db.add.assert_called()
        db.commit.assert_called_once()

    def test_duplicate_favorite_is_idempotent(self) -> None:
        """Second favorite returns 200 (idempotent)."""
        db = MagicMock()
        skill = _mock_skill()
        existing = MagicMock()
        existing.user_id = USER_ID
        existing.skill_id = SKILL_ID
        existing.created_at = datetime.now(UTC)
        db.query.return_value.filter.return_value.first.side_effect = [skill, existing]

        result = favorite_skill(db, "test-skill", USER_ID)

        assert result["user_id"] == USER_ID
        # Should NOT commit (no changes made)
        db.commit.assert_not_called()

    def test_unfavorite_deletes_and_decrements(self) -> None:
        """Unfavorite removes record and decrements counter."""
        db = MagicMock()
        skill = _mock_skill()
        fav = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [skill, fav]

        unfavorite_skill(db, "test-skill", USER_ID)

        db.delete.assert_called_once_with(fav)
        db.commit.assert_called_once()


class TestForkSkill:
    """Tests for fork_skill."""

    def test_fork_creates_new_skill_with_upstream_reference(self) -> None:
        """Fork creates new Skill row + Fork row."""
        db = MagicMock()
        original = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = original

        result = fork_skill(db, "test-skill", USER_ID)

        assert result["original_skill_id"] == SKILL_ID
        assert result["forked_by"] == USER_ID
        assert "fork" in result["forked_skill_slug"]
        # Should add Skill + Fork + AuditLog = at least 3 adds
        assert db.add.call_count >= 3
        db.commit.assert_called_once()

    def test_fork_increments_fork_count(self) -> None:
        """Fork atomically increments fork_count on original skill."""
        db = MagicMock()
        original = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = original

        fork_skill(db, "test-skill", USER_ID)

        db.query.return_value.filter.return_value.update.assert_called()


class TestFollowUser:
    """Tests for follow_user."""

    def test_follow_creates_new_follow(self) -> None:
        """First follow creates Follow record."""
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.side_effect = [skill, None]

        result = follow_user(db, "test-skill", USER_ID)

        assert result["followed_user_id"] == AUTHOR_ID
        assert result["follower_id"] == USER_ID
        db.add.assert_called()
        db.commit.assert_called_once()

    def test_follow_upsert_is_idempotent(self) -> None:
        """Second follow returns existing (no error)."""
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
