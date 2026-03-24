"""Tests for the skills blueprint (browse, detail, versions)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tests.conftest import make_token

SKILL_ID = uuid4()
AUTHOR_ID = uuid4()
VERSION_ID = uuid4()


def _auth_headers(token: str | None = None) -> dict[str, str]:
    if token is None:
        token = make_token()
    return {"Authorization": f"Bearer {token}"}


def _make_skill_summary(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "id": SKILL_ID,
        "slug": "my-skill",
        "name": "My Skill",
        "short_desc": "A useful skill",
        "category": "productivity",
        "divisions": ["engineering"],
        "tags": ["ai"],
        "author": "alice",
        "author_type": "individual",
        "version": "1.0.0",
        "install_method": "mcp",
        "verified": True,
        "featured": False,
        "install_count": 42,
        "fork_count": 3,
        "favorite_count": 10,
        "avg_rating": "4.5",
        "review_count": 5,
        "days_ago": 2,
        "user_has_installed": None,
        "user_has_favorited": None,
    }
    defaults.update(overrides)
    return defaults


def _make_skill_detail(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "id": SKILL_ID,
        "slug": "my-skill",
        "name": "My Skill",
        "short_desc": "A useful skill",
        "category": "productivity",
        "divisions": ["engineering"],
        "tags": ["ai"],
        "author": "alice",
        "author_id": AUTHOR_ID,
        "author_type": "individual",
        "current_version": "1.0.0",
        "install_method": "mcp",
        "data_sensitivity": "none",
        "external_calls": False,
        "verified": True,
        "featured": False,
        "status": "published",
        "install_count": 42,
        "fork_count": 3,
        "favorite_count": 10,
        "view_count": 100,
        "review_count": 5,
        "avg_rating": "4.5",
        "trending_score": "0.85",
        "published_at": datetime.now(tz=timezone.utc).isoformat(),
        "deprecated_at": None,
        "trigger_phrases": [],
        "current_version_content": None,
        "user_has_installed": None,
        "user_has_favorited": None,
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# GET /api/v1/skills — browse (public)
# ---------------------------------------------------------------------------
class TestListSkills:
    """GET /api/v1/skills — public browse endpoint."""

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    def test_returns_200_with_items(self, mock_browse: MagicMock, client: Any) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 1)

        resp = client.get("/api/v1/skills")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert data["has_more"] is False
        assert len(data["items"]) == 1
        assert data["items"][0]["slug"] == "my-skill"

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    def test_returns_empty_list(self, mock_browse: MagicMock, client: Any) -> None:
        mock_browse.return_value = ([], 0)

        resp = client.get("/api/v1/skills")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    def test_works_without_auth(self, mock_browse: MagicMock, client: Any) -> None:
        """Public endpoint — no Authorization header needed."""
        mock_browse.return_value = ([], 0)

        resp = client.get("/api/v1/skills")
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    def test_pagination_params_forwarded(self, mock_browse: MagicMock, client: Any) -> None:
        mock_browse.return_value = ([], 0)

        client.get("/api/v1/skills?page=2&per_page=10&q=test&category=productivity&sort=newest")
        call_kwargs = mock_browse.call_args[1]

        assert call_kwargs["page"] == 2
        assert call_kwargs["per_page"] == 10
        assert call_kwargs["q"] == "test"
        assert call_kwargs["category"] == "productivity"
        assert call_kwargs["sort"] == "newest"

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    def test_has_more_true_when_more_pages(self, mock_browse: MagicMock, client: Any) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 50)

        resp = client.get("/api/v1/skills?page=1&per_page=5")
        data = resp.get_json()
        assert data["has_more"] is True

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    def test_per_page_clamped_to_max_100(self, mock_browse: MagicMock, client: Any) -> None:
        mock_browse.return_value = ([], 0)

        client.get("/api/v1/skills?per_page=999")
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["per_page"] == 100


# ---------------------------------------------------------------------------
# GET /api/v1/skills/categories (public)
# ---------------------------------------------------------------------------
class TestListCategories:
    """GET /api/v1/skills/categories — public categories list."""

    def test_returns_200_with_categories(self, client: Any, mock_db: MagicMock) -> None:
        cat1 = MagicMock()
        cat1.slug = "productivity"
        cat1.name = "Productivity"
        cat1.sort_order = 1

        cat2 = MagicMock()
        cat2.slug = "security"
        cat2.name = "Security"
        cat2.sort_order = 2

        mock_db.query.return_value.order_by.return_value.all.return_value = [cat1, cat2]

        resp = client.get("/api/v1/skills/categories")
        assert resp.status_code == 200

        data = resp.get_json()
        assert len(data) == 2
        assert data[0]["slug"] == "productivity"
        assert data[1]["slug"] == "security"

    def test_works_without_auth(self, client: Any, mock_db: MagicMock) -> None:
        mock_db.query.return_value.order_by.return_value.all.return_value = []

        resp = client.get("/api/v1/skills/categories")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/skills/<slug> (public)
# ---------------------------------------------------------------------------
class TestGetSkillDetail:
    """GET /api/v1/skills/<slug> — public skill detail."""

    @patch("skillhub_flask.blueprints.skills.increment_view_count")
    @patch("skillhub_flask.blueprints.skills.SessionLocal")
    @patch("skillhub_flask.blueprints.skills.get_skill_detail")
    def test_returns_200_on_found(
        self,
        mock_detail: MagicMock,
        mock_session_local: MagicMock,
        mock_increment: MagicMock,
        client: Any,
    ) -> None:
        mock_detail.return_value = _make_skill_detail()
        mock_session_local.return_value = MagicMock()

        resp = client.get("/api/v1/skills/my-skill")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["slug"] == "my-skill"
        assert data["name"] == "My Skill"

    @patch("skillhub_flask.blueprints.skills.get_skill_detail")
    def test_returns_404_when_not_found(self, mock_detail: MagicMock, client: Any) -> None:
        mock_detail.return_value = None

        resp = client.get("/api/v1/skills/nonexistent")
        assert resp.status_code == 404
        assert "not found" in resp.get_json()["detail"].lower()

    @patch("skillhub_flask.blueprints.skills.increment_view_count")
    @patch("skillhub_flask.blueprints.skills.SessionLocal")
    @patch("skillhub_flask.blueprints.skills.get_skill_detail")
    def test_works_without_auth(
        self,
        mock_detail: MagicMock,
        mock_session_local: MagicMock,
        mock_increment: MagicMock,
        client: Any,
    ) -> None:
        mock_detail.return_value = _make_skill_detail()
        mock_session_local.return_value = MagicMock()

        resp = client.get("/api/v1/skills/my-skill")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/skills/<slug>/versions (auth required)
# ---------------------------------------------------------------------------
class TestListVersions:
    """GET /api/v1/skills/<slug>/versions — requires auth."""

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.get("/api/v1/skills/my-skill/versions")
        assert resp.status_code == 401

    def test_returns_200_with_versions(self, client: Any, mock_db: MagicMock) -> None:
        skill_mock = MagicMock(id=SKILL_ID)
        mock_db.query.return_value.filter.return_value.first.return_value = skill_mock

        now = datetime.now(tz=timezone.utc)
        ver_mock = MagicMock(id=VERSION_ID, version="1.0.0", changelog="Initial", published_at=now)
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [ver_mock]

        resp = client.get("/api/v1/skills/my-skill/versions", headers=_auth_headers())
        assert resp.status_code == 200

        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["version"] == "1.0.0"

    def test_returns_404_when_skill_not_found(self, client: Any, mock_db: MagicMock) -> None:
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = client.get("/api/v1/skills/nonexistent/versions", headers=_auth_headers())
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/skills/<slug>/versions/latest (auth required)
# ---------------------------------------------------------------------------
class TestGetLatestVersion:
    """GET /api/v1/skills/<slug>/versions/latest — requires auth."""

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.get("/api/v1/skills/my-skill/versions/latest")
        assert resp.status_code == 401

    def test_returns_200_with_latest_version(self, client: Any, mock_db: MagicMock) -> None:
        skill_mock = MagicMock(id=SKILL_ID, current_version="1.0.0")
        now = datetime.now(tz=timezone.utc)
        version_mock = MagicMock(
            id=VERSION_ID,
            version="1.0.0",
            content="# My Skill\nDoes things.",
            frontmatter={"title": "My Skill"},
            changelog="Initial release",
            published_at=now,
        )

        # First query returns skill, second returns version
        mock_db.query.return_value.filter.return_value.first.side_effect = [skill_mock, version_mock]

        resp = client.get("/api/v1/skills/my-skill/versions/latest", headers=_auth_headers())
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["version"] == "1.0.0"
        assert data["content"] == "# My Skill\nDoes things."

    def test_returns_404_when_skill_not_found(self, client: Any, mock_db: MagicMock) -> None:
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = client.get("/api/v1/skills/nonexistent/versions/latest", headers=_auth_headers())
        assert resp.status_code == 404

    def test_returns_404_when_version_missing(self, client: Any, mock_db: MagicMock) -> None:
        skill_mock = MagicMock(id=SKILL_ID, current_version="1.0.0")
        # Skill found, but version query returns None
        mock_db.query.return_value.filter.return_value.first.side_effect = [skill_mock, None]

        resp = client.get("/api/v1/skills/my-skill/versions/latest", headers=_auth_headers())
        assert resp.status_code == 404
        assert "not found" in resp.get_json()["detail"].lower()


# ---------------------------------------------------------------------------
# GET /api/v1/skills/<slug>/versions/<version> (auth required)
# ---------------------------------------------------------------------------
class TestGetSpecificVersion:
    """GET /api/v1/skills/<slug>/versions/<version> — requires auth."""

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.get("/api/v1/skills/my-skill/versions/1.0.0")
        assert resp.status_code == 401

    def test_returns_200_with_specific_version(self, client: Any, mock_db: MagicMock) -> None:
        skill_mock = MagicMock(id=SKILL_ID, current_version="1.0.0")
        now = datetime.now(tz=timezone.utc)
        version_mock = MagicMock(
            id=VERSION_ID,
            version="1.0.0",
            content="# Content",
            frontmatter=None,
            changelog="Bug fix",
            published_at=now,
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [skill_mock, version_mock]

        resp = client.get("/api/v1/skills/my-skill/versions/1.0.0", headers=_auth_headers())
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["version"] == "1.0.0"
        assert data["changelog"] == "Bug fix"

    def test_returns_404_when_skill_not_found(self, client: Any, mock_db: MagicMock) -> None:
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = client.get("/api/v1/skills/nonexistent/versions/1.0.0", headers=_auth_headers())
        assert resp.status_code == 404

    def test_returns_404_when_version_not_found(self, client: Any, mock_db: MagicMock) -> None:
        skill_mock = MagicMock(id=SKILL_ID, current_version="1.0.0")
        mock_db.query.return_value.filter.return_value.first.side_effect = [skill_mock, None]

        resp = client.get("/api/v1/skills/my-skill/versions/2.0.0", headers=_auth_headers())
        assert resp.status_code == 404
        assert "2.0.0" in resp.get_json()["detail"]
