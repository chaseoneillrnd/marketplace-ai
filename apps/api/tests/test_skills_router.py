"""Tests for Skills router — browse, detail, and version endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from tests.conftest import _make_settings, make_token


def _make_skill_summary(**overrides: Any) -> dict[str, Any]:
    """Create a mock skill summary dict."""
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "slug": "pr-review-assistant",
        "name": "PR Review Assistant",
        "short_desc": "Automated PR code reviews",
        "category": "Engineering",
        "divisions": ["Engineering Org"],
        "tags": ["code-review", "pr"],
        "author": None,
        "author_type": "community",
        "version": "1.0.0",
        "install_method": "all",
        "verified": False,
        "featured": False,
        "install_count": 42,
        "fork_count": 5,
        "favorite_count": 10,
        "avg_rating": Decimal("4.20"),
        "rating_count": 8,
        "days_ago": None,
        "user_has_installed": None,
        "user_has_favorited": None,
    }
    defaults.update(overrides)
    return defaults


def _make_detail_dict(**overrides: Any) -> dict[str, Any]:
    """Create a mock skill detail dict."""
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "slug": "pr-review-assistant",
        "name": "PR Review Assistant",
        "short_desc": "Automated PR code reviews",
        "category": "Engineering",
        "divisions": ["Engineering Org"],
        "tags": ["code-review"],
        "author": None,
        "author_id": uuid.uuid4(),
        "author_type": "community",
        "current_version": "1.0.0",
        "install_method": "all",
        "data_sensitivity": "low",
        "external_calls": False,
        "verified": False,
        "featured": False,
        "status": "published",
        "install_count": 42,
        "fork_count": 5,
        "favorite_count": 10,
        "view_count": 100,
        "review_count": 8,
        "avg_rating": Decimal("4.20"),
        "trending_score": Decimal("85.1234"),
        "published_at": datetime.now(UTC),
        "deprecated_at": None,
        "trigger_phrases": [
            {"id": uuid.uuid4(), "phrase": "review this PR"},
        ],
        "current_version_content": None,
        "user_has_installed": None,
        "user_has_favorited": None,
    }
    defaults.update(overrides)
    return defaults


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
def auth_headers() -> dict[str, str]:
    token = make_token(
        {
            "user_id": "00000000-0000-0000-0000-000000000001",
            "sub": "test-user",
            "division": "Engineering Org",
            "is_platform_team": False,
            "is_security_team": False,
        }
    )
    return {"Authorization": f"Bearer {token}"}


class TestListSkills:
    """Tests for GET /api/v1/skills."""

    @patch("skillhub.routers.skills.browse_skills")
    def test_returns_200_with_items_and_pagination(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 1)
        response = client.get("/api/v1/skills")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "has_more" in data
        assert data["total"] == 1

    @patch("skillhub.routers.skills.browse_skills")
    def test_category_filter(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 1)
        response = client.get("/api/v1/skills?category=Engineering")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["category"] == "Engineering"

    @patch("skillhub.routers.skills.browse_skills")
    def test_divisions_filter(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 1)
        response = client.get("/api/v1/skills?divisions=Engineering+Org&divisions=Product+Org")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["divisions"] == ["Engineering Org", "Product Org"]

    @patch("skillhub.routers.skills.browse_skills")
    def test_sort_by_rating(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 1)
        response = client.get("/api/v1/skills?sort=rating")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["sort"] == "rating"

    @patch("skillhub.routers.skills.browse_skills")
    def test_search_query(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 1)
        response = client.get("/api/v1/skills?q=review")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["q"] == "review"

    @patch("skillhub.routers.skills.browse_skills")
    def test_unauthenticated_returns_skills_without_user_annotations(
        self, mock_browse: MagicMock, client: TestClient
    ) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 1)
        response = client.get("/api/v1/skills")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["current_user_id"] is None

    @patch("skillhub.routers.skills.browse_skills")
    def test_authenticated_includes_user_id(
        self,
        mock_browse: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_browse.return_value = (
            [_make_skill_summary(user_has_installed=True, user_has_favorited=False)],
            1,
        )
        response = client.get("/api/v1/skills", headers=auth_headers)
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["current_user_id"] is not None

    @patch("skillhub.routers.skills.browse_skills")
    def test_has_more_true_when_more_pages(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 50)
        response = client.get("/api/v1/skills?page=1&per_page=20")
        assert response.status_code == 200
        assert response.json()["has_more"] is True

    @patch("skillhub.routers.skills.browse_skills")
    def test_has_more_false_when_last_page(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 1)
        response = client.get("/api/v1/skills?page=1&per_page=20")
        assert response.status_code == 200
        assert response.json()["has_more"] is False


class TestGetSkillDetail:
    """Tests for GET /api/v1/skills/{slug}."""

    @patch("skillhub.routers.skills.increment_view_count")
    @patch("skillhub.routers.skills.get_skill_detail")
    def test_returns_full_detail_with_triggers(
        self, mock_detail: MagicMock, mock_view: MagicMock, client: TestClient
    ) -> None:
        skill_data = _make_detail_dict()
        mock_detail.return_value = skill_data
        response = client.get("/api/v1/skills/pr-review-assistant")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "pr-review-assistant"
        assert "trigger_phrases" in data
        assert len(data["trigger_phrases"]) == 1

    @patch("skillhub.routers.skills.get_skill_detail")
    def test_nonexistent_returns_404(self, mock_detail: MagicMock, client: TestClient) -> None:
        mock_detail.return_value = None
        response = client.get("/api/v1/skills/nonexistent")
        assert response.status_code == 404

    @patch("skillhub.routers.skills.increment_view_count")
    @patch("skillhub.routers.skills.get_skill_detail")
    def test_unauthenticated_has_no_user_annotations(
        self, mock_detail: MagicMock, mock_view: MagicMock, client: TestClient
    ) -> None:
        mock_detail.return_value = _make_detail_dict()
        response = client.get("/api/v1/skills/pr-review-assistant")
        assert response.status_code == 200
        data = response.json()
        assert data["user_has_installed"] is None
        assert data["user_has_favorited"] is None

    @patch("skillhub.routers.skills.increment_view_count")
    @patch("skillhub.routers.skills.get_skill_detail")
    def test_authenticated_includes_user_annotations(
        self,
        mock_detail: MagicMock,
        mock_view: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_detail.return_value = _make_detail_dict(user_has_installed=True, user_has_favorited=False)
        response = client.get("/api/v1/skills/pr-review-assistant", headers=auth_headers)
        assert response.status_code == 200
        # The service layer was called with user_id so it can return annotations
        mock_detail.assert_called_once()
        call_kwargs = mock_detail.call_args
        assert call_kwargs[1].get("current_user_id") is not None or call_kwargs[0][2] is not None


class TestListVersions:
    """Tests for GET /api/v1/skills/{slug}/versions."""

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/v1/skills/test-skill/versions")
        assert response.status_code == 401

    @patch("skillhub.routers.skills.Skill", create=True)
    def test_authenticated_returns_versions(
        self,
        _mock_skill: MagicMock,
        client: TestClient,
        mock_db: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        """Authenticated request with mocked DB returns version list."""
        mock_skill = MagicMock()
        mock_skill.id = uuid.uuid4()
        mock_skill.current_version = "2.0.0"

        mock_version = MagicMock()
        mock_version.id = uuid.uuid4()
        mock_version.version = "2.0.0"
        mock_version.changelog = "Added new features"
        mock_version.published_at = datetime.now(UTC)

        # Mock the DB query chain for skill lookup
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_skill
        mock_query.all.return_value = [mock_version]

        response = client.get("/api/v1/skills/test-skill/versions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["version"] == "2.0.0"


class TestGetVersion:
    """Tests for GET /api/v1/skills/{slug}/versions/{version}."""

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/v1/skills/test-skill/versions/1.0.0")
        assert response.status_code == 401

    def test_nonexistent_skill_returns_404(
        self,
        client: TestClient,
        mock_db: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        response = client.get("/api/v1/skills/nonexistent/versions/1.0.0", headers=auth_headers)
        assert response.status_code == 404


class TestGetLatestVersion:
    """Tests for GET /api/v1/skills/{slug}/versions/latest."""

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/v1/skills/test-skill/versions/latest")
        assert response.status_code == 401

    def test_latest_resolves_to_current_version(
        self,
        client: TestClient,
        mock_db: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        mock_skill = MagicMock()
        mock_skill.id = uuid.uuid4()
        mock_skill.current_version = "2.3.0"

        mock_version = MagicMock()
        mock_version.id = uuid.uuid4()
        mock_version.version = "2.3.0"
        mock_version.content = "# Skill Content"
        mock_version.frontmatter = {"name": "Test", "version": "2.3.0"}
        mock_version.changelog = "Bug fixes"
        mock_version.published_at = datetime.now(UTC)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_skill

        # Second call returns the version
        mock_query.first.side_effect = [mock_skill, mock_version]

        response = client.get("/api/v1/skills/test-skill/versions/latest", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.3.0"
        assert data["content"] == "# Skill Content"
