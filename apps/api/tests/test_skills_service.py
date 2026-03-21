"""Tests for Skills service — query logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

from skillhub.services.skills import (
    _skill_to_detail_dict,
    _skill_to_summary_dict,
    _user_has_favorited,
    _user_has_installed,
    browse_skills,
    get_skill_detail,
    increment_view_count,
)


def _make_mock_skill(**overrides: Any) -> MagicMock:
    """Create a mock Skill ORM object."""
    skill = MagicMock()
    skill.id = overrides.get("id", uuid.uuid4())
    skill.slug = overrides.get("slug", "test-skill")
    skill.name = overrides.get("name", "Test Skill")
    skill.short_desc = overrides.get("short_desc", "A test skill")
    skill.category = overrides.get("category", "Engineering")
    skill.author_id = overrides.get("author_id", uuid.uuid4())
    skill.author_type = MagicMock()
    skill.author_type.value = overrides.get("author_type", "community")
    skill.current_version = overrides.get("current_version", "1.0.0")
    skill.install_method = MagicMock()
    skill.install_method.value = overrides.get("install_method", "all")
    skill.data_sensitivity = MagicMock()
    skill.data_sensitivity.value = overrides.get("data_sensitivity", "low")
    skill.external_calls = overrides.get("external_calls", False)
    skill.verified = overrides.get("verified", False)
    skill.featured = overrides.get("featured", False)
    skill.status = MagicMock()
    skill.status.value = overrides.get("status", "published")
    skill.install_count = overrides.get("install_count", 10)
    skill.fork_count = overrides.get("fork_count", 2)
    skill.favorite_count = overrides.get("favorite_count", 5)
    skill.view_count = overrides.get("view_count", 100)
    skill.review_count = overrides.get("review_count", 3)
    skill.avg_rating = overrides.get("avg_rating", Decimal("4.00"))
    skill.trending_score = overrides.get("trending_score", Decimal("50.0000"))
    skill.published_at = overrides.get("published_at", datetime.now(UTC))
    skill.deprecated_at = overrides.get("deprecated_at")

    # Relationships
    div = MagicMock()
    div.division_slug = "Engineering Org"
    skill.divisions = overrides.get("divisions", [div])

    tag = MagicMock()
    tag.tag = "testing"
    skill.tags = overrides.get("tags", [tag])

    tp = MagicMock()
    tp.id = uuid.uuid4()
    tp.phrase = "test this"
    skill.trigger_phrases = overrides.get("trigger_phrases", [tp])

    skill.versions = overrides.get("versions", [])

    return skill


class TestSkillToSummaryDict:
    """Tests for _skill_to_summary_dict."""

    def test_extracts_divisions(self) -> None:
        skill = _make_mock_skill()
        result = _skill_to_summary_dict(skill)
        assert result["divisions"] == ["Engineering Org"]

    def test_extracts_tags(self) -> None:
        skill = _make_mock_skill()
        result = _skill_to_summary_dict(skill)
        assert result["tags"] == ["testing"]

    def test_counters_present(self) -> None:
        skill = _make_mock_skill(install_count=42)
        result = _skill_to_summary_dict(skill)
        assert result["install_count"] == 42
        assert result["rating_count"] == skill.review_count


class TestSkillToDetailDict:
    """Tests for _skill_to_detail_dict."""

    def test_includes_trigger_phrases(self) -> None:
        skill = _make_mock_skill()
        result = _skill_to_detail_dict(skill)
        assert len(result["trigger_phrases"]) == 1
        assert result["trigger_phrases"][0]["phrase"] == "test this"

    def test_finds_current_version_content(self) -> None:
        version = MagicMock()
        version.id = uuid.uuid4()
        version.version = "1.0.0"
        version.content = "# My Skill"
        version.frontmatter = {"name": "My Skill"}
        version.changelog = "Initial release"
        version.published_at = datetime.now(UTC)

        skill = _make_mock_skill(current_version="1.0.0", versions=[version])
        result = _skill_to_detail_dict(skill)
        assert result["current_version_content"] is not None
        assert result["current_version_content"]["content"] == "# My Skill"

    def test_no_matching_version_returns_none(self) -> None:
        skill = _make_mock_skill(current_version="2.0.0", versions=[])
        result = _skill_to_detail_dict(skill)
        assert result["current_version_content"] is None


class TestBrowseSkills:
    """Tests for browse_skills function."""

    def test_calls_query_with_published_filter(self) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.unique.return_value = mock_query
        mock_query.all.return_value = []

        items, total = browse_skills(mock_db)
        assert items == []
        assert total == 0


class TestGetSkillDetail:
    """Tests for get_skill_detail function."""

    def test_returns_none_for_not_found(self) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = get_skill_detail(mock_db, "nonexistent")
        assert result is None

    def test_returns_detail_dict_for_found(self) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query

        skill = _make_mock_skill()
        mock_query.first.return_value = skill

        # Mock user annotation queries
        count_query = MagicMock()
        count_query.select_from.return_value = count_query
        count_query.filter.return_value = count_query
        count_query.scalar.return_value = 0

        result = get_skill_detail(mock_db, "test-skill")
        assert result is not None
        assert result["slug"] == "test-skill"


class TestUserAnnotations:
    """Tests for _user_has_installed and _user_has_favorited."""

    def test_user_has_installed_true(self) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.select_from.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 1

        assert _user_has_installed(mock_db, uuid.uuid4(), uuid.uuid4()) is True

    def test_user_has_installed_false(self) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.select_from.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0

        assert _user_has_installed(mock_db, uuid.uuid4(), uuid.uuid4()) is False

    def test_user_has_favorited_true(self) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.select_from.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 1

        assert _user_has_favorited(mock_db, uuid.uuid4(), uuid.uuid4()) is True


class TestBrowseSkillsFilters:
    """Tests for browse_skills with various filters."""

    def _setup_mock_db(self) -> MagicMock:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.unique.return_value = mock_query
        mock_query.all.return_value = []
        return mock_db

    def test_with_search_query(self) -> None:
        mock_db = self._setup_mock_db()
        items, total = browse_skills(mock_db, q="review")
        assert total == 0

    def test_with_category_filter(self) -> None:
        mock_db = self._setup_mock_db()
        items, total = browse_skills(mock_db, category="Engineering")
        assert total == 0

    def test_with_divisions_filter(self) -> None:
        mock_db = self._setup_mock_db()
        items, total = browse_skills(mock_db, divisions=["Engineering Org"])
        assert total == 0

    def test_with_install_method_filter(self) -> None:
        mock_db = self._setup_mock_db()
        items, total = browse_skills(mock_db, install_method="mcp")
        assert total == 0

    def test_with_verified_filter(self) -> None:
        mock_db = self._setup_mock_db()
        items, total = browse_skills(mock_db, verified=True)
        assert total == 0

    def test_with_featured_filter(self) -> None:
        mock_db = self._setup_mock_db()
        items, total = browse_skills(mock_db, featured=True)
        assert total == 0

    @patch("skillhub.services.skills._user_has_installed", return_value=True)
    @patch("skillhub.services.skills._user_has_favorited", return_value=False)
    def test_with_user_annotations(self, mock_fav: MagicMock, mock_inst: MagicMock) -> None:
        mock_db = self._setup_mock_db()
        skill = _make_mock_skill()
        mock_query = mock_db.query.return_value
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.unique.return_value = mock_query
        mock_query.all.return_value = [skill]

        user_id = uuid.uuid4()
        items, total = browse_skills(mock_db, current_user_id=user_id)
        assert total == 1
        assert len(items) == 1
        assert items[0]["user_has_installed"] is True
        assert items[0]["user_has_favorited"] is False

    def test_sort_options(self) -> None:
        for sort in ["trending", "installs", "rating", "newest", "updated"]:
            mock_db = self._setup_mock_db()
            items, total = browse_skills(mock_db, sort=sort)
            assert total == 0


class TestIncrementViewCount:
    """Tests for increment_view_count."""

    def test_increments_and_commits(self) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        skill_id = uuid.uuid4()
        increment_view_count(mock_db, skill_id)

        mock_query.update.assert_called_once()
        mock_db.commit.assert_called_once()
