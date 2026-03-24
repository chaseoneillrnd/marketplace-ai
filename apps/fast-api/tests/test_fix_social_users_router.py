"""Tests for fixes #2, #8, and #20 — fork double-insert, user summary fields, view count session."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

SKILL_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
AUTHOR_ID = uuid.uuid4()
AUTHOR_NAME = "Jane Developer"


def _mock_skill(**overrides: Any) -> MagicMock:
    """Create a mock Skill with sensible defaults."""
    skill = MagicMock()
    skill.id = overrides.get("id", SKILL_ID)
    skill.slug = overrides.get("slug", "test-skill")
    skill.name = overrides.get("name", "Test Skill")
    skill.short_desc = overrides.get("short_desc", "A test skill")
    skill.category = overrides.get("category", "engineering")
    skill.author_id = overrides.get("author_id", AUTHOR_ID)
    skill.current_version = overrides.get("current_version", "1.0.0")
    skill.install_method = overrides.get("install_method", "all")
    skill.data_sensitivity = overrides.get("data_sensitivity", "low")
    skill.external_calls = overrides.get("external_calls", False)
    skill.install_count = overrides.get("install_count", 5)
    skill.fork_count = overrides.get("fork_count", 0)
    skill.favorite_count = overrides.get("favorite_count", 2)
    skill.avg_rating = overrides.get("avg_rating", 4.0)
    skill.review_count = overrides.get("review_count", 3)
    skill.view_count = overrides.get("view_count", 100)
    skill.verified = overrides.get("verified", False)
    skill.featured = overrides.get("featured", False)
    skill.author_type = overrides.get("author_type", "community")
    skill.published_at = overrides.get("published_at", datetime.now(UTC) - timedelta(days=7))
    skill.divisions = overrides.get("divisions", [])
    skill.tags = overrides.get("tags", [])
    return skill


# ===========================================================================
# FIX #2 — fork_skill must create exactly 1 SkillVersion
# ===========================================================================


class TestForkSkillSingleVersion:
    """Verify that forking a single-version skill produces exactly 1 SkillVersion row."""

    def test_fork_creates_exactly_one_version(self) -> None:
        """Fork a skill that has one version and verify only 1 SkillVersion is added."""
        from skillhub.services.social import fork_skill
        from skillhub_db.models.skill import SkillVersion

        db = MagicMock()
        original = _mock_skill()

        # Mock for get_skill_or_404
        upstream_version = MagicMock()
        upstream_version.version = "1.0.0"
        upstream_version.content = "skill content"
        upstream_version.frontmatter = {"title": "Test"}
        upstream_version.changelog = "Initial"
        upstream_version.content_hash = "abc123"

        # db.query(Skill).filter(...).first() returns original skill
        # db.query(SkillVersion).filter(...).first() returns upstream_version
        def _query_side_effect(model: Any) -> MagicMock:
            mock_q = MagicMock()
            if model is SkillVersion:
                mock_q.filter.return_value.first.return_value = upstream_version
            else:
                # Skill model queries
                mock_q.filter.return_value.first.return_value = original
                mock_q.filter.return_value.update.return_value = 1
            return mock_q

        db.query.side_effect = _query_side_effect

        result = fork_skill(db, "test-skill", USER_ID)

        # Count how many SkillVersion objects were added
        version_adds = 0
        for add_call in db.add.call_args_list:
            obj = add_call[0][0]
            if isinstance(obj, SkillVersion):
                version_adds += 1

        assert version_adds == 1, (
            f"Expected exactly 1 SkillVersion to be added, got {version_adds}"
        )

    def test_fork_creates_no_version_when_original_has_none(self) -> None:
        """Fork a skill with no matching version: 0 SkillVersion rows added."""
        from skillhub.services.social import fork_skill
        from skillhub_db.models.skill import SkillVersion

        db = MagicMock()
        original = _mock_skill()

        def _query_side_effect(model: Any) -> MagicMock:
            mock_q = MagicMock()
            if model is SkillVersion:
                mock_q.filter.return_value.first.return_value = None
            else:
                mock_q.filter.return_value.first.return_value = original
                mock_q.filter.return_value.update.return_value = 1
            return mock_q

        db.query.side_effect = _query_side_effect

        result = fork_skill(db, "test-skill", USER_ID)

        version_adds = 0
        for add_call in db.add.call_args_list:
            obj = add_call[0][0]
            if isinstance(obj, SkillVersion):
                version_adds += 1

        assert version_adds == 0


# ===========================================================================
# FIX #8 — UserSkillSummary must return non-null author and days_ago
# ===========================================================================


class TestUserCollectionAuthorAndDaysAgo:
    """Verify that get_user_installs/favorites/forks return author and days_ago."""

    def _make_mock_db_with_skills(self, skills: list[MagicMock]) -> MagicMock:
        """Build a mock db that returns skills from the joined query."""
        db = MagicMock()
        query = db.query.return_value
        query.options.return_value = query
        query.join.return_value = query
        query.filter.return_value = query
        query.count.return_value = len(skills)
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.unique.return_value = query
        query.all.return_value = skills
        return db

    def test_get_user_installs_returns_author_and_days_ago(self) -> None:
        """Installs endpoint returns resolved author name and computed days_ago."""
        from skillhub.services.users import get_user_installs

        published_7_days_ago = datetime.now(UTC) - timedelta(days=7)
        skill = _mock_skill(published_at=published_7_days_ago)
        db = self._make_mock_db_with_skills([skill])

        # Patch _batch_resolve_authors to return a known name
        with patch(
            "skillhub.services.users._batch_resolve_authors",
            return_value={AUTHOR_ID: AUTHOR_NAME},
        ):
            items, total = get_user_installs(db, USER_ID)

        assert len(items) == 1
        assert items[0]["author"] == AUTHOR_NAME
        assert items[0]["days_ago"] is not None
        assert items[0]["days_ago"] == 7

    def test_get_user_favorites_returns_author_and_days_ago(self) -> None:
        """Favorites endpoint returns resolved author name and computed days_ago."""
        from skillhub.services.users import get_user_favorites

        published_3_days_ago = datetime.now(UTC) - timedelta(days=3)
        skill = _mock_skill(published_at=published_3_days_ago)
        db = self._make_mock_db_with_skills([skill])

        with patch(
            "skillhub.services.users._batch_resolve_authors",
            return_value={AUTHOR_ID: AUTHOR_NAME},
        ):
            items, total = get_user_favorites(db, USER_ID)

        assert len(items) == 1
        assert items[0]["author"] == AUTHOR_NAME
        assert items[0]["days_ago"] == 3

    def test_get_user_forks_returns_author_and_days_ago(self) -> None:
        """Forks endpoint returns resolved author name and computed days_ago."""
        from skillhub.services.users import get_user_forks

        published_0_days_ago = datetime.now(UTC)
        skill = _mock_skill(published_at=published_0_days_ago)
        db = self._make_mock_db_with_skills([skill])

        with patch(
            "skillhub.services.users._batch_resolve_authors",
            return_value={AUTHOR_ID: AUTHOR_NAME},
        ):
            items, total = get_user_forks(db, USER_ID)

        assert len(items) == 1
        assert items[0]["author"] == AUTHOR_NAME
        assert items[0]["days_ago"] == 0

    def test_days_ago_none_when_published_at_none(self) -> None:
        """days_ago is None when skill has no published_at."""
        from skillhub.services.users import get_user_installs

        skill = _mock_skill(published_at=None)
        db = self._make_mock_db_with_skills([skill])

        with patch(
            "skillhub.services.users._batch_resolve_authors",
            return_value={AUTHOR_ID: AUTHOR_NAME},
        ):
            items, _ = get_user_installs(db, USER_ID)

        assert items[0]["days_ago"] is None

    def test_author_none_when_not_resolved(self) -> None:
        """author is None when the author_id has no matching User row."""
        from skillhub.services.users import get_user_installs

        skill = _mock_skill()
        db = self._make_mock_db_with_skills([skill])

        with patch(
            "skillhub.services.users._batch_resolve_authors",
            return_value={},  # No match for AUTHOR_ID
        ):
            items, _ = get_user_installs(db, USER_ID)

        assert items[0]["author"] is None


# ===========================================================================
# FIX #20 — increment_view_count uses fresh DB session in background task
# ===========================================================================


class TestViewCountBackgroundTask:
    """Verify that the background task for view counts creates a fresh session."""

    @patch("skillhub.routers.skills.increment_view_count")
    @patch("skillhub.routers.skills.get_skill_detail")
    @patch("skillhub.routers.skills.SessionLocal")
    def test_background_task_uses_fresh_session(
        self,
        mock_session_local: MagicMock,
        mock_get_detail: MagicMock,
        mock_increment: MagicMock,
    ) -> None:
        """The view count background task should create and close its own session."""
        from tests.conftest import _make_settings, make_token
        from skillhub.dependencies import get_db
        from skillhub.main import create_app
        from fastapi.testclient import TestClient

        skill_id = uuid.uuid4()
        mock_get_detail.return_value = {
            "id": skill_id,
            "slug": "test-skill",
            "name": "Test Skill",
            "short_desc": "Desc",
            "category": "engineering",
            "divisions": [],
            "tags": [],
            "author": None,
            "author_id": AUTHOR_ID,
            "author_type": "community",
            "current_version": "1.0.0",
            "install_method": "all",
            "data_sensitivity": "low",
            "external_calls": False,
            "verified": False,
            "featured": False,
            "status": "published",
            "install_count": 5,
            "fork_count": 0,
            "favorite_count": 2,
            "view_count": 100,
            "review_count": 3,
            "avg_rating": 4.0,
            "trending_score": 50.0,
            "published_at": datetime.now(UTC),
            "deprecated_at": None,
            "trigger_phrases": [],
            "current_version_content": None,
            "user_has_installed": None,
            "user_has_favorited": None,
        }

        fresh_db = MagicMock()
        mock_session_local.return_value = fresh_db

        settings = _make_settings()
        app = create_app(settings=settings)

        mock_db = MagicMock()

        def override_get_db():  # type: ignore[no-untyped-def]
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        resp = client.get("/api/v1/skills/test-skill")
        assert resp.status_code == 200

        # The background task should have been called with the fresh session
        mock_session_local.assert_called_once()
        mock_increment.assert_called_once_with(fresh_db, skill_id)
        fresh_db.close.assert_called_once()

    @patch("skillhub.routers.skills.increment_view_count")
    @patch("skillhub.routers.skills.get_skill_detail")
    @patch("skillhub.routers.skills.SessionLocal")
    def test_fresh_session_closed_on_error(
        self,
        mock_session_local: MagicMock,
        mock_get_detail: MagicMock,
        mock_increment: MagicMock,
    ) -> None:
        """Fresh session is closed even if increment_view_count raises."""
        from tests.conftest import _make_settings
        from skillhub.dependencies import get_db
        from skillhub.main import create_app
        from fastapi.testclient import TestClient

        skill_id = uuid.uuid4()
        mock_get_detail.return_value = {
            "id": skill_id,
            "slug": "err-skill",
            "name": "Error Skill",
            "short_desc": "Desc",
            "category": "engineering",
            "divisions": [],
            "tags": [],
            "author": None,
            "author_id": AUTHOR_ID,
            "author_type": "community",
            "current_version": "1.0.0",
            "install_method": "all",
            "data_sensitivity": "low",
            "external_calls": False,
            "verified": False,
            "featured": False,
            "status": "published",
            "install_count": 0,
            "fork_count": 0,
            "favorite_count": 0,
            "view_count": 0,
            "review_count": 0,
            "avg_rating": 0.0,
            "trending_score": 0.0,
            "published_at": datetime.now(UTC),
            "deprecated_at": None,
            "trigger_phrases": [],
            "current_version_content": None,
            "user_has_installed": None,
            "user_has_favorited": None,
        }

        fresh_db = MagicMock()
        mock_session_local.return_value = fresh_db
        mock_increment.side_effect = RuntimeError("DB gone")

        settings = _make_settings()
        app = create_app(settings=settings)
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: (yield mock_db).__next__  # type: ignore[misc]

        def override_get_db():  # type: ignore[no-untyped-def]
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app, raise_server_exceptions=False)
        # The request itself should succeed (background task runs after response)
        client.get("/api/v1/skills/err-skill")

        # Even on error, the fresh session must be closed
        fresh_db.close.assert_called_once()
