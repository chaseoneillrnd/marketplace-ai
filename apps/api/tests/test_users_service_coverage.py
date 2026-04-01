"""Coverage tests for skillhub.services.users — profile, installs, favorites, forks, submissions."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from skillhub.services.users import (
    _batch_resolve_authors,
    _compute_days_ago,
    _skill_to_summary_dict,
    _submission_to_dict,
    get_user_favorites,
    get_user_forks,
    get_user_installs,
    get_user_profile,
    get_user_submissions,
)


def _mock_skill() -> MagicMock:
    skill = MagicMock()
    skill.id = uuid.uuid4()
    skill.slug = "test-skill"
    skill.name = "Test Skill"
    skill.short_desc = "Short desc"
    skill.category = "productivity"
    skill.author_id = uuid.uuid4()
    skill.author_type = "community"
    skill.current_version = "1.0.0"
    skill.install_method = "mcp"
    skill.verified = True
    skill.featured = False
    skill.install_count = 10
    skill.fork_count = 2
    skill.favorite_count = 5
    skill.avg_rating = 4.0
    skill.review_count = 3
    skill.published_at = datetime.now(UTC) - timedelta(days=7)
    skill.divisions = []
    skill.tags = []
    return skill


def _mock_submission() -> MagicMock:
    sub = MagicMock()
    sub.id = uuid.uuid4()
    sub.display_id = "SKL-TEST01"
    sub.name = "Test Skill"
    sub.short_desc = "A test"
    sub.category = "productivity"
    sub.status = MagicMock()
    sub.status.value = "submitted"
    sub.created_at = None
    return sub


class TestComputeDaysAgo:
    def test_computes_days(self) -> None:
        published = datetime.now(UTC) - timedelta(days=5)
        assert _compute_days_ago(published) == 5

    def test_none_returns_none(self) -> None:
        assert _compute_days_ago(None) is None


class TestBatchResolveAuthors:
    def test_resolves_names(self) -> None:
        author_id = uuid.uuid4()
        user_row = MagicMock()
        user_row.id = author_id
        user_row.name = "Alice"

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [user_row]

        result = _batch_resolve_authors(db, [author_id])
        assert result[author_id] == "Alice"

    def test_empty_list_returns_empty(self) -> None:
        result = _batch_resolve_authors(MagicMock(), [])
        assert result == {}


class TestSkillToSummaryDict:
    def test_returns_expected_fields(self) -> None:
        skill = _mock_skill()
        result = _skill_to_summary_dict(skill, author_name="Alice")
        assert result["slug"] == skill.slug
        assert result["author"] == "Alice"
        assert result["install_count"] == skill.install_count
        assert result["user_has_installed"] is None

    def test_defaults_for_none_fields(self) -> None:
        skill = _mock_skill()
        skill.author_type = None
        skill.install_method = None
        result = _skill_to_summary_dict(skill)
        assert result["author_type"] == "community"
        assert result["install_method"] == "all"


class TestSubmissionToDict:
    def test_returns_expected_fields(self) -> None:
        sub = _mock_submission()
        result = _submission_to_dict(sub)
        assert result["display_id"] == "SKL-TEST01"
        assert result["status"] == "submitted"

    def test_handles_string_status(self) -> None:
        sub = _mock_submission()
        sub.status = "draft"  # plain string, no .value
        result = _submission_to_dict(sub)
        assert result["status"] == "draft"


class TestGetUserProfile:
    def test_returns_profile_with_stats(self) -> None:
        user_id = uuid.uuid4()
        claims: dict[str, Any] = {
            "user_id": str(user_id),
            "sub": "alice@example.com",
            "name": "Alice",
            "division": "engineering",
            "role": "user",
            "is_platform_team": False,
            "is_security_team": False,
        }

        db = MagicMock()
        q = MagicMock()
        q.select_from.return_value = q
        q.filter.return_value = q
        q.scalar.side_effect = [5, 3, 2, 1]  # installs, submissions, reviews, forks
        db.query.return_value = q

        result = get_user_profile(db, claims)

        assert result["user_id"] == str(user_id)
        assert result["name"] == "Alice"
        assert result["skills_installed"] == 5
        assert result["skills_submitted"] == 3
        assert result["reviews_written"] == 2
        assert result["forks_made"] == 1

    def test_handles_none_scalars(self) -> None:
        user_id = uuid.uuid4()
        claims: dict[str, Any] = {
            "user_id": str(user_id),
        }

        db = MagicMock()
        q = MagicMock()
        q.select_from.return_value = q
        q.filter.return_value = q
        q.scalar.return_value = None  # all counts return None, should default to 0
        db.query.return_value = q

        result = get_user_profile(db, claims)
        assert result["skills_installed"] == 0
        assert result["skills_submitted"] == 0


class TestGetUserInstalls:
    def test_returns_installed_skills(self) -> None:
        user_id = uuid.uuid4()
        skill = _mock_skill()

        db = MagicMock()
        q = MagicMock()
        q.options.return_value = q
        q.join.return_value = q
        q.filter.return_value = q
        q.count.return_value = 1
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = [skill]
        db.query.return_value = q

        with patch("skillhub.services.users._batch_resolve_authors", return_value={skill.author_id: "Alice"}):
            items, total = get_user_installs(db, user_id)

        assert total == 1
        assert items[0]["slug"] == skill.slug

    def test_include_uninstalled(self) -> None:
        user_id = uuid.uuid4()

        db = MagicMock()
        q = MagicMock()
        q.options.return_value = q
        q.join.return_value = q
        q.filter.return_value = q
        q.count.return_value = 0
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        with patch("skillhub.services.users._batch_resolve_authors", return_value={}):
            items, total = get_user_installs(db, user_id, include_uninstalled=True)

        assert total == 0


class TestGetUserFavorites:
    def test_returns_favorited_skills(self) -> None:
        user_id = uuid.uuid4()
        skill = _mock_skill()

        db = MagicMock()
        q = MagicMock()
        q.options.return_value = q
        q.join.return_value = q
        q.filter.return_value = q
        q.count.return_value = 1
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = [skill]
        db.query.return_value = q

        with patch("skillhub.services.users._batch_resolve_authors", return_value={}):
            items, total = get_user_favorites(db, user_id)

        assert total == 1
        assert items[0]["slug"] == skill.slug


class TestGetUserForks:
    def test_returns_forked_skills(self) -> None:
        user_id = uuid.uuid4()
        skill = _mock_skill()

        db = MagicMock()
        q = MagicMock()
        q.options.return_value = q
        q.join.return_value = q
        q.filter.return_value = q
        q.count.return_value = 1
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = [skill]
        db.query.return_value = q

        with patch("skillhub.services.users._batch_resolve_authors", return_value={}):
            items, total = get_user_forks(db, user_id)

        assert total == 1


class TestGetUserSubmissions:
    def test_returns_user_submissions(self) -> None:
        user_id = uuid.uuid4()
        sub = _mock_submission()

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 1
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = [sub]
        db.query.return_value = q

        items, total = get_user_submissions(db, user_id)

        assert total == 1
        assert items[0]["display_id"] == "SKL-TEST01"
