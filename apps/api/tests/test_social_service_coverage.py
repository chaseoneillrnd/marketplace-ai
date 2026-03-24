"""Coverage tests for skillhub.services.social — install, favorite, fork, follow."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from skillhub.services.social import (
    check_division_authorization,
    favorite_skill,
    follow_user,
    fork_skill,
    get_skill_or_404,
    install_skill,
    unfollow_user,
    unfavorite_skill,
    uninstall_skill,
)


def _mock_skill(slug: str = "test-skill") -> MagicMock:
    skill = MagicMock()
    skill.id = uuid.uuid4()
    skill.slug = slug
    skill.name = "Test Skill"
    skill.short_desc = "A test skill"
    skill.category = "productivity"
    skill.author_id = uuid.uuid4()
    skill.current_version = "1.0.0"
    skill.install_method = "mcp"
    skill.data_sensitivity = "low"
    skill.external_calls = False
    return skill


def _db_returning_skill(skill: MagicMock) -> MagicMock:
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = skill
    return db


class TestGetSkillOr404:
    def test_found_returns_skill(self) -> None:
        skill = _mock_skill()
        db = _db_returning_skill(skill)
        result = get_skill_or_404(db, "test-skill")
        assert result is skill

    def test_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="not found"):
            get_skill_or_404(db, "missing-slug")


class TestCheckDivisionAuthorization:
    def test_authorized_division_returns_true(self) -> None:
        db = MagicMock()
        db.query.return_value.select_from.return_value.filter.return_value.scalar.return_value = 1
        result = check_division_authorization(db, uuid.uuid4(), "engineering")
        assert result is True

    def test_unauthorized_division_returns_false(self) -> None:
        db = MagicMock()
        db.query.return_value.select_from.return_value.filter.return_value.scalar.return_value = 0
        result = check_division_authorization(db, uuid.uuid4(), "finance")
        assert result is False


class TestInstallSkill:
    def _setup_db(
        self,
        skill: MagicMock,
        has_divisions: int = 0,
        existing_install: Any = None,
    ) -> MagicMock:
        db = MagicMock()
        call_count = 0

        def query_side_effect(model: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            q = MagicMock()
            q.filter.return_value = q
            q.select_from.return_value = q
            q.first.return_value = skill if call_count == 1 else existing_install
            q.scalar.return_value = has_divisions
            q.update.return_value = 1
            return q

        db.query.side_effect = query_side_effect
        return db

    def test_successful_install(self) -> None:
        skill = _mock_skill()
        user_id = uuid.uuid4()

        db = MagicMock()
        install_obj = MagicMock()
        install_obj.id = uuid.uuid4()
        install_obj.skill_id = skill.id
        install_obj.user_id = user_id
        install_obj.version = "1.0.0"
        install_obj.method = "mcp"
        install_obj.installed_at = None

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.select_from.return_value = query_mock
        query_mock.scalar.return_value = 0  # no divisions
        query_mock.first.side_effect = [skill, None]  # skill found, no existing install
        query_mock.update.return_value = 1
        db.query.return_value = query_mock

        with patch("skillhub.services.social.Install") as MockInstall:
            MockInstall.return_value = install_obj
            result = install_skill(db, "test-skill", user_id, "engineering", "mcp", "1.0.0")

        db.add.assert_called()
        db.commit.assert_called_once()
        assert result["skill_id"] == skill.id
        assert result["user_id"] == user_id

    def test_already_installed_raises(self) -> None:
        skill = _mock_skill()
        existing = MagicMock()

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.select_from.return_value = query_mock
        query_mock.scalar.return_value = 0
        query_mock.first.side_effect = [skill, existing]
        db.query.return_value = query_mock

        with pytest.raises(ValueError, match="already installed"):
            install_skill(db, "test-skill", uuid.uuid4(), "engineering", "mcp", "1.0.0")

    def test_division_restricted_raises(self) -> None:
        skill = _mock_skill()

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.select_from.return_value = query_mock
        # First scalar call: has_divisions > 0, second scalar call: not authorized
        query_mock.scalar.side_effect = [1, 0]
        query_mock.first.return_value = skill
        db.query.return_value = query_mock

        with pytest.raises(PermissionError, match="division_restricted"):
            install_skill(db, "test-skill", uuid.uuid4(), "finance", "mcp", "1.0.0")


class TestUninstallSkill:
    def test_successful_uninstall(self) -> None:
        skill = _mock_skill()
        existing_install = MagicMock()
        existing_install.id = uuid.uuid4()

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [skill, existing_install]
        query_mock.update.return_value = 1
        db.query.return_value = query_mock

        uninstall_skill(db, "test-skill", uuid.uuid4())

        db.commit.assert_called_once()

    def test_no_active_install_raises(self) -> None:
        skill = _mock_skill()

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [skill, None]
        db.query.return_value = query_mock

        with pytest.raises(ValueError, match="No active install found"):
            uninstall_skill(db, "test-skill", uuid.uuid4())


class TestFavoriteSkill:
    def test_favorite_new(self) -> None:
        skill = _mock_skill()
        user_id = uuid.uuid4()
        fav_obj = MagicMock()
        fav_obj.user_id = user_id
        fav_obj.skill_id = skill.id
        fav_obj.created_at = None

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [skill, None]
        query_mock.update.return_value = 1
        db.query.return_value = query_mock

        with patch("skillhub.services.social.Favorite") as MockFav:
            MockFav.return_value = fav_obj
            result = favorite_skill(db, "test-skill", user_id)

        db.add.assert_called()
        db.commit.assert_called_once()
        assert result["skill_id"] == skill.id

    def test_already_favorited_is_idempotent(self) -> None:
        skill = _mock_skill()
        user_id = uuid.uuid4()
        existing_fav = MagicMock()
        existing_fav.user_id = user_id
        existing_fav.skill_id = skill.id
        existing_fav.created_at = None

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [skill, existing_fav]
        db.query.return_value = query_mock

        result = favorite_skill(db, "test-skill", user_id)
        db.commit.assert_not_called()
        assert result["skill_id"] == skill.id


class TestUnfavoriteSkill:
    def test_successful_unfavorite(self) -> None:
        skill = _mock_skill()
        fav = MagicMock()

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [skill, fav]
        query_mock.update.return_value = 1
        db.query.return_value = query_mock

        unfavorite_skill(db, "test-skill", uuid.uuid4())
        db.delete.assert_called_once_with(fav)
        db.commit.assert_called_once()

    def test_not_favorited_raises(self) -> None:
        skill = _mock_skill()

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [skill, None]
        db.query.return_value = query_mock

        with pytest.raises(ValueError, match="Not favorited"):
            unfavorite_skill(db, "test-skill", uuid.uuid4())


class TestForkSkill:
    def test_successful_fork(self) -> None:
        original = _mock_skill()
        user_id = uuid.uuid4()

        version_obj = MagicMock()
        version_obj.version = "1.0.0"
        version_obj.content = "skill content"
        version_obj.frontmatter = {}
        version_obj.content_hash = "abc123"
        version_obj.changelog = None

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [original, version_obj]
        query_mock.update.return_value = 1
        db.query.return_value = query_mock

        result = fork_skill(db, "test-skill", user_id)

        db.add.assert_called()
        db.commit.assert_called_once()
        assert result["original_skill_id"] == original.id
        assert result["forked_by"] == user_id
        assert "fork" in result["forked_skill_slug"]

    def test_fork_without_version(self) -> None:
        """Fork succeeds even if no current version exists."""
        original = _mock_skill()
        user_id = uuid.uuid4()

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [original, None]  # no upstream version
        query_mock.update.return_value = 1
        db.query.return_value = query_mock

        result = fork_skill(db, "test-skill", user_id)
        assert result["forked_by"] == user_id


class TestFollowUser:
    def test_successful_follow(self) -> None:
        skill = _mock_skill()
        follower_id = uuid.uuid4()
        # Make sure follower != author
        skill.author_id = uuid.uuid4()
        follow_obj = MagicMock()
        follow_obj.follower_id = follower_id
        follow_obj.followed_user_id = skill.author_id
        follow_obj.created_at = None

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [skill, None]
        db.query.return_value = query_mock

        with patch("skillhub.services.social.Follow") as MockFollow:
            MockFollow.return_value = follow_obj
            result = follow_user(db, "test-skill", follower_id)

        db.add.assert_called()
        db.commit.assert_called_once()

    def test_cannot_follow_self(self) -> None:
        skill = _mock_skill()
        skill.author_id = uuid.uuid4()
        follower_id = skill.author_id  # same user

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = skill
        db.query.return_value = query_mock

        with pytest.raises(ValueError, match="Cannot follow yourself"):
            follow_user(db, "test-skill", follower_id)

    def test_already_following_idempotent(self) -> None:
        skill = _mock_skill()
        follower_id = uuid.uuid4()
        skill.author_id = uuid.uuid4()
        existing_follow = MagicMock()
        existing_follow.follower_id = follower_id
        existing_follow.followed_user_id = skill.author_id
        existing_follow.created_at = None

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [skill, existing_follow]
        db.query.return_value = query_mock

        result = follow_user(db, "test-skill", follower_id)
        db.commit.assert_not_called()


class TestUnfollowUser:
    def test_successful_unfollow(self) -> None:
        skill = _mock_skill()
        follower_id = uuid.uuid4()
        skill.author_id = uuid.uuid4()
        follow_obj = MagicMock()

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [skill, follow_obj]
        db.query.return_value = query_mock

        unfollow_user(db, "test-skill", follower_id)
        db.delete.assert_called_once_with(follow_obj)
        db.commit.assert_called_once()

    def test_not_following_raises(self) -> None:
        skill = _mock_skill()
        skill.author_id = uuid.uuid4()

        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [skill, None]
        db.query.return_value = query_mock

        with pytest.raises(ValueError, match="Not following"):
            unfollow_user(db, "test-skill", uuid.uuid4())
