"""Tests for Users service — profile stats and collection queries."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from sqlalchemy.orm import Session

from skillhub.services.users import (
    get_user_favorites,
    get_user_forks,
    get_user_installs,
    get_user_profile,
    get_user_submissions,
)

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _mock_skill(**overrides: Any) -> MagicMock:
    """Create a mock Skill ORM object."""
    skill = MagicMock()
    skill.id = overrides.get("id", uuid.uuid4())
    skill.slug = overrides.get("slug", "test-skill")
    skill.name = overrides.get("name", "Test Skill")
    skill.short_desc = overrides.get("short_desc", "A test skill")
    skill.category = overrides.get("category", "engineering")
    skill.author_type = MagicMock()
    skill.author_type.value = overrides.get("author_type", "community")
    skill.current_version = overrides.get("current_version", "1.0.0")
    skill.install_method = MagicMock()
    skill.install_method.value = overrides.get("install_method", "all")
    skill.verified = overrides.get("verified", False)
    skill.featured = overrides.get("featured", False)
    skill.install_count = overrides.get("install_count", 0)
    skill.fork_count = overrides.get("fork_count", 0)
    skill.favorite_count = overrides.get("favorite_count", 0)
    skill.avg_rating = overrides.get("avg_rating", Decimal("0.00"))
    skill.review_count = overrides.get("review_count", 0)
    skill.published_at = overrides.get("published_at", datetime.now(UTC))
    skill.divisions = []
    skill.tags = []
    return skill


class TestGetUserProfile:
    """Tests for get_user_profile."""

    def test_returns_stats_from_db(self) -> None:
        db = MagicMock(spec=Session)
        user_claims: dict[str, Any] = {
            "user_id": str(USER_ID),
            "sub": "test-user",
            "name": "Test User",
            "division": "engineering",
            "role": "engineer",
            "is_platform_team": False,
            "is_security_team": False,
        }

        # Mock the scalar returns for count queries
        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.select_from.return_value = mock_query
        mock_query.filter.return_value = mock_query
        # Return counts: installs=2, submissions=3, reviews=5, forks=1
        mock_query.scalar.side_effect = [2, 3, 5, 1]

        result = get_user_profile(db, user_claims)

        assert result["name"] == "Test User"
        assert result["division"] == "engineering"
        assert result["skills_installed"] == 2
        assert result["skills_submitted"] == 3
        assert result["reviews_written"] == 5
        assert result["forks_made"] == 1

    def test_zero_stats_when_no_activity(self) -> None:
        db = MagicMock(spec=Session)
        user_claims: dict[str, Any] = {
            "user_id": str(USER_ID),
            "sub": "new-user",
            "name": "New User",
            "division": "product",
            "role": "pm",
            "is_platform_team": False,
            "is_security_team": False,
        }

        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.select_from.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [0, 0, 0, 0]

        result = get_user_profile(db, user_claims)

        assert result["skills_installed"] == 0
        assert result["skills_submitted"] == 0
        assert result["reviews_written"] == 0
        assert result["forks_made"] == 0


class TestGetUserInstalls:
    """Tests for get_user_installs."""

    def test_returns_installed_skills(self) -> None:
        db = MagicMock(spec=Session)
        skill = _mock_skill(slug="my-installed-skill")

        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.unique.return_value = mock_query
        mock_query.all.return_value = [skill]

        items, total = get_user_installs(db, USER_ID, page=1, per_page=20, include_uninstalled=False)

        assert total == 1
        assert len(items) == 1
        assert items[0]["slug"] == "my-installed-skill"

    def test_excludes_uninstalled_by_default(self) -> None:
        db = MagicMock(spec=Session)

        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.unique.return_value = mock_query
        mock_query.all.return_value = []

        items, total = get_user_installs(db, USER_ID, page=1, per_page=20, include_uninstalled=False)

        assert total == 0
        assert len(items) == 0
        # filter was called (to exclude uninstalled)
        assert mock_query.filter.called


class TestGetUserFavorites:
    """Tests for get_user_favorites."""

    def test_returns_favorited_skills(self) -> None:
        db = MagicMock(spec=Session)
        skill = _mock_skill(slug="fav-skill")

        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.unique.return_value = mock_query
        mock_query.all.return_value = [skill]

        items, total = get_user_favorites(db, USER_ID, page=1, per_page=20)

        assert total == 1
        assert len(items) == 1
        assert items[0]["slug"] == "fav-skill"


class TestGetUserForks:
    """Tests for get_user_forks."""

    def test_returns_forked_skills(self) -> None:
        db = MagicMock(spec=Session)
        skill = _mock_skill(slug="forked-skill")

        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.unique.return_value = mock_query
        mock_query.all.return_value = [skill]

        items, total = get_user_forks(db, USER_ID, page=1, per_page=20)

        assert total == 1
        assert len(items) == 1
        assert items[0]["slug"] == "forked-skill"


class TestGetUserSubmissions:
    """Tests for get_user_submissions."""

    def test_returns_submissions_with_status(self) -> None:
        db = MagicMock(spec=Session)

        mock_submission = MagicMock()
        mock_submission.id = uuid.uuid4()
        mock_submission.display_id = "SKL-ABC123"
        mock_submission.name = "My Skill"
        mock_submission.short_desc = "Description"
        mock_submission.category = "engineering"
        mock_submission.status = MagicMock()
        mock_submission.status.value = "gate1_passed"
        mock_submission.created_at = datetime.now(UTC)

        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_submission]

        items, total = get_user_submissions(db, USER_ID, page=1, per_page=20)

        assert total == 1
        assert len(items) == 1
        assert items[0]["display_id"] == "SKL-ABC123"
        assert items[0]["status"] == "gate1_passed"
