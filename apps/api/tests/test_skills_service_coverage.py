"""Coverage tests for skillhub.services.skills — browse, detail, trending."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from skillhub.services.skills import (
    _batch_resolve_authors,
    _batch_user_favorited,
    _batch_user_installed,
    _compute_days_ago,
    _skill_to_detail_dict,
    _skill_to_summary_dict,
    browse_skills,
    get_skill_detail,
    increment_view_count,
    recalculate_trending_scores,
)


def _mock_skill(
    *,
    slug: str = "test-skill",
    category: str = "productivity",
    status: str = "published",
    install_count: int = 10,
    favorite_count: int = 5,
    view_count: int = 100,
    avg_rating: float = 4.5,
    trending_score: float = 25.0,
    install_method: str = "mcp",
    verified: bool = True,
    featured: bool = False,
    published_at: datetime | None = None,
) -> MagicMock:
    skill = MagicMock()
    skill.id = uuid.uuid4()
    skill.slug = slug
    skill.name = "Test Skill"
    skill.short_desc = "A test skill"
    skill.category = category
    skill.status = status
    skill.author_id = uuid.uuid4()
    skill.author_type = "community"
    skill.current_version = "1.0.0"
    skill.install_method = install_method
    skill.data_sensitivity = "low"
    skill.external_calls = False
    skill.verified = verified
    skill.featured = featured
    skill.install_count = install_count
    skill.fork_count = 2
    skill.favorite_count = favorite_count
    skill.view_count = view_count
    skill.avg_rating = Decimal(str(avg_rating))
    skill.review_count = 3
    skill.trending_score = Decimal(str(trending_score))
    skill.published_at = published_at or datetime.now(UTC) - timedelta(days=5)
    skill.deprecated_at = None
    skill.divisions = []
    skill.tags = []
    skill.trigger_phrases = []
    skill.versions = []
    return skill


class TestComputeDaysAgo:
    def test_recent_skill(self) -> None:
        published = datetime.now(UTC) - timedelta(days=3)
        days = _compute_days_ago(published)
        assert days == 3

    def test_no_published_at_returns_none(self) -> None:
        assert _compute_days_ago(None) is None

    def test_today_is_zero(self) -> None:
        published = datetime.now(UTC)
        days = _compute_days_ago(published)
        assert days == 0


class TestBatchResolveAuthors:
    def test_resolves_author_names(self) -> None:
        author_id = uuid.uuid4()
        user_row = MagicMock()
        user_row.id = author_id
        user_row.name = "Alice"

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [user_row]

        result = _batch_resolve_authors(db, [author_id])
        assert result[author_id] == "Alice"

    def test_empty_ids_returns_empty_dict(self) -> None:
        db = MagicMock()
        result = _batch_resolve_authors(db, [])
        assert result == {}

    def test_none_ids_filtered_out(self) -> None:
        db = MagicMock()
        result = _batch_resolve_authors(db, [None])  # type: ignore[list-item]
        assert result == {}


class TestBatchUserInstalled:
    def test_returns_installed_skill_ids(self) -> None:
        user_id = uuid.uuid4()
        skill_id = uuid.uuid4()

        row = MagicMock()
        row.skill_id = skill_id

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [row]

        result = _batch_user_installed(db, user_id, [skill_id])
        assert skill_id in result

    def test_empty_skill_ids_returns_empty(self) -> None:
        result = _batch_user_installed(MagicMock(), uuid.uuid4(), [])
        assert result == set()


class TestBatchUserFavorited:
    def test_returns_favorited_skill_ids(self) -> None:
        user_id = uuid.uuid4()
        skill_id = uuid.uuid4()

        row = MagicMock()
        row.skill_id = skill_id

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [row]

        result = _batch_user_favorited(db, user_id, [skill_id])
        assert skill_id in result

    def test_empty_skill_ids_returns_empty(self) -> None:
        result = _batch_user_favorited(MagicMock(), uuid.uuid4(), [])
        assert result == set()


class TestSkillToSummaryDict:
    def test_returns_required_fields(self) -> None:
        skill = _mock_skill()
        result = _skill_to_summary_dict(skill, author_name="Alice")
        assert result["slug"] == skill.slug
        assert result["name"] == skill.name
        assert result["author"] == "Alice"
        assert result["install_count"] == skill.install_count
        assert result["user_has_installed"] is None
        assert result["user_has_favorited"] is None

    def test_defaults_for_missing_fields(self) -> None:
        skill = _mock_skill()
        skill.author_type = None
        skill.install_method = None
        result = _skill_to_summary_dict(skill)
        assert result["author_type"] == "community"
        assert result["install_method"] == "all"


class TestSkillToDetailDict:
    def test_returns_full_fields(self) -> None:
        skill = _mock_skill()
        result = _skill_to_detail_dict(skill, author_name="Bob")
        assert result["slug"] == skill.slug
        assert result["author"] == "Bob"
        assert result["author_id"] == skill.author_id
        assert result["current_version"] == "1.0.0"
        assert result["trigger_phrases"] == []
        assert result["current_version_content"] is None

    def test_finds_current_version_content(self) -> None:
        skill = _mock_skill()
        version = MagicMock()
        version.version = "1.0.0"
        version.id = uuid.uuid4()
        version.content = "# skill content"
        version.frontmatter = {}
        version.changelog = "Initial"
        version.published_at = None
        skill.versions = [version]

        result = _skill_to_detail_dict(skill)
        assert result["current_version_content"] is not None
        assert result["current_version_content"]["version"] == "1.0.0"


class TestBrowseSkills:
    def _setup_db(self, skills: list[MagicMock]) -> MagicMock:
        db = MagicMock()
        q = MagicMock()
        q.options.return_value = q
        q.filter.return_value = q
        q.count.return_value = len(skills)
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = skills
        db.query.return_value = q
        return db

    def test_basic_browse(self) -> None:
        skill = _mock_skill()
        db = self._setup_db([skill])

        with patch("skillhub.services.skills._batch_resolve_authors", return_value={skill.author_id: "Alice"}):
            items, total = browse_skills(db)

        assert total == 1
        assert len(items) == 1
        assert items[0]["slug"] == skill.slug

    def test_browse_with_user_annotations(self) -> None:
        skill = _mock_skill()
        user_id = uuid.uuid4()
        db = self._setup_db([skill])

        with (
            patch("skillhub.services.skills._batch_resolve_authors", return_value={}),
            patch("skillhub.services.skills._batch_user_installed", return_value={skill.id}),
            patch("skillhub.services.skills._batch_user_favorited", return_value=set()),
        ):
            items, total = browse_skills(db, current_user_id=user_id)

        assert items[0]["user_has_installed"] is True
        assert items[0]["user_has_favorited"] is False

    def test_browse_empty(self) -> None:
        db = self._setup_db([])
        with patch("skillhub.services.skills._batch_resolve_authors", return_value={}):
            items, total = browse_skills(db)
        assert total == 0
        assert items == []


class TestGetSkillDetail:
    def test_returns_detail_for_known_slug(self) -> None:
        skill = _mock_skill()

        db = MagicMock()
        q = MagicMock()
        q.options.return_value = q
        q.filter.return_value = q
        q.first.return_value = skill
        db.query.return_value = q

        with patch("skillhub.services.skills._batch_resolve_authors", return_value={skill.author_id: "Alice"}):
            result = get_skill_detail(db, "test-skill")

        assert result is not None
        assert result["slug"] == skill.slug

    def test_returns_none_for_missing_slug(self) -> None:
        db = MagicMock()
        q = MagicMock()
        q.options.return_value = q
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        result = get_skill_detail(db, "no-such-skill")
        assert result is None

    def test_includes_user_annotations(self) -> None:
        skill = _mock_skill()
        user_id = uuid.uuid4()

        db = MagicMock()
        q = MagicMock()
        q.options.return_value = q
        q.filter.return_value = q
        q.first.return_value = skill
        db.query.return_value = q

        with (
            patch("skillhub.services.skills._batch_resolve_authors", return_value={}),
            patch("skillhub.services.skills._batch_user_installed", return_value=set()),
            patch("skillhub.services.skills._batch_user_favorited", return_value={skill.id}),
        ):
            result = get_skill_detail(db, "test-skill", current_user_id=user_id)

        assert result is not None
        assert result["user_has_installed"] is False
        assert result["user_has_favorited"] is True


class TestIncrementViewCount:
    def test_increments_and_commits(self) -> None:
        skill_id = uuid.uuid4()

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.update.return_value = 1
        db.query.return_value = q

        increment_view_count(db, skill_id)

        db.commit.assert_called_once()


class TestRecalculateTrendingScores:
    def test_updates_trending_scores(self) -> None:
        skill1 = _mock_skill(
            install_count=50,
            favorite_count=20,
            view_count=500,
            avg_rating=4.8,
            published_at=datetime.now(UTC) - timedelta(days=10),
        )

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [skill1]
        q.update.return_value = 1
        db.query.return_value = q

        count = recalculate_trending_scores(db)

        assert count == 1
        db.commit.assert_called_once()
        # Verify that update was called to set the trending_score
        q.update.assert_called_once()

    def test_handles_no_published_at(self) -> None:
        skill = _mock_skill(published_at=None)
        skill.published_at = None

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [skill]
        q.update.return_value = 1
        db.query.return_value = q

        count = recalculate_trending_scores(db)
        assert count == 1
