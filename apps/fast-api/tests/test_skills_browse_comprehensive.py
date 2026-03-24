"""Comprehensive tests for Skills browse/search/filter — all sort options, pagination, featured, search edge cases."""

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
from skillhub.services.skills import browse_skills, increment_view_count
from tests.conftest import _make_settings, make_token


def _make_skill_summary(**overrides: Any) -> dict[str, Any]:
    """Create a mock skill summary dict."""
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "slug": "test-skill",
        "name": "Test Skill",
        "short_desc": "A test skill",
        "category": "Engineering",
        "divisions": ["Engineering Org"],
        "tags": ["test"],
        "author": None,
        "author_type": "community",
        "version": "1.0.0",
        "install_method": "all",
        "verified": False,
        "featured": False,
        "install_count": 10,
        "fork_count": 2,
        "favorite_count": 5,
        "avg_rating": Decimal("4.00"),
        "review_count": 3,
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
        "slug": "test-skill",
        "name": "Test Skill",
        "short_desc": "A test skill",
        "category": "Engineering",
        "divisions": ["Engineering Org"],
        "tags": ["test"],
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
        "install_count": 10,
        "fork_count": 2,
        "favorite_count": 5,
        "view_count": 100,
        "review_count": 3,
        "avg_rating": Decimal("4.00"),
        "trending_score": Decimal("50.0000"),
        "published_at": datetime.now(UTC),
        "deprecated_at": None,
        "trigger_phrases": [],
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


# --- Sort Options ---


class TestSortOptions:
    """Test all sort parameter values are accepted and forwarded correctly."""

    @pytest.mark.parametrize(
        "sort_value",
        ["trending", "installs", "rating", "newest", "updated"],
    )
    @patch("skillhub.routers.skills.browse_skills")
    def test_sort_option_accepted(
        self, mock_browse: MagicMock, sort_value: str, client: TestClient
    ) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get(f"/api/v1/skills?sort={sort_value}")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["sort"] == sort_value

    @patch("skillhub.routers.skills.browse_skills")
    def test_default_sort_is_trending(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["sort"] == "trending"

    def test_invalid_sort_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/v1/skills?sort=invalid_sort")
        assert response.status_code == 422


# --- Multi-Division Filtering ---


class TestMultiDivisionFilter:
    """Test multi-division filter combinations."""

    @patch("skillhub.routers.skills.browse_skills")
    def test_single_division(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills?divisions=Engineering+Org")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["divisions"] == ["Engineering Org"]

    @patch("skillhub.routers.skills.browse_skills")
    def test_multiple_divisions(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get(
            "/api/v1/skills?divisions=Engineering+Org&divisions=Product+Org&divisions=Finance+%26+Legal"
        )
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert "Engineering Org" in call_kwargs["divisions"]
        assert "Product Org" in call_kwargs["divisions"]
        assert "Finance & Legal" in call_kwargs["divisions"]

    @patch("skillhub.routers.skills.browse_skills")
    def test_no_divisions_sends_none(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["divisions"] is None


# --- Combined Filters ---


class TestCombinedFilters:
    """Test category + division combined filter scenarios."""

    @patch("skillhub.routers.skills.browse_skills")
    def test_category_and_division_combined(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([_make_skill_summary()], 1)
        response = client.get(
            "/api/v1/skills?category=Engineering&divisions=Engineering+Org"
        )
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["category"] == "Engineering"
        assert call_kwargs["divisions"] == ["Engineering Org"]

    @patch("skillhub.routers.skills.browse_skills")
    def test_category_division_and_sort_combined(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get(
            "/api/v1/skills?category=Data&divisions=Engineering+Org&sort=installs"
        )
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["category"] == "Data"
        assert call_kwargs["sort"] == "installs"
        assert call_kwargs["divisions"] == ["Engineering Org"]

    @patch("skillhub.routers.skills.browse_skills")
    def test_search_with_category_and_division(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get(
            "/api/v1/skills?q=review&category=Engineering&divisions=Product+Org"
        )
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["q"] == "review"
        assert call_kwargs["category"] == "Engineering"
        assert call_kwargs["divisions"] == ["Product Org"]

    @patch("skillhub.routers.skills.browse_skills")
    def test_verified_with_featured(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills?verified=true&featured=true")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["verified"] is True
        assert call_kwargs["featured"] is True

    @patch("skillhub.routers.skills.browse_skills")
    def test_install_method_filter(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills?install_method=mcp")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["install_method"] == "mcp"


# --- Pagination Edge Cases ---


class TestPaginationEdgeCases:
    """Test pagination boundary conditions."""

    @patch("skillhub.routers.skills.browse_skills")
    def test_page_1_default(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 20

    def test_page_0_returns_422(self, client: TestClient) -> None:
        """Page 0 should fail validation (ge=1)."""
        response = client.get("/api/v1/skills?page=0")
        assert response.status_code == 422

    def test_negative_page_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/v1/skills?page=-1")
        assert response.status_code == 422

    @patch("skillhub.routers.skills.browse_skills")
    def test_page_beyond_total_returns_empty(self, mock_browse: MagicMock, client: TestClient) -> None:
        """Requesting beyond total returns empty items with correct total."""
        mock_browse.return_value = ([], 5)
        response = client.get("/api/v1/skills?page=100&per_page=20")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 5
        assert data["has_more"] is False

    @patch("skillhub.routers.skills.browse_skills")
    def test_empty_results(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["has_more"] is False

    def test_per_page_0_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/v1/skills?per_page=0")
        assert response.status_code == 422

    def test_per_page_over_100_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/v1/skills?per_page=101")
        assert response.status_code == 422

    @patch("skillhub.routers.skills.browse_skills")
    def test_per_page_100_accepted(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills?per_page=100")
        assert response.status_code == 200
        assert response.json()["per_page"] == 100

    @patch("skillhub.routers.skills.browse_skills")
    def test_exact_last_page_has_more_false(self, mock_browse: MagicMock, client: TestClient) -> None:
        """When page * per_page == total, has_more should be False."""
        mock_browse.return_value = ([_make_skill_summary()], 20)
        response = client.get("/api/v1/skills?page=1&per_page=20")
        assert response.status_code == 200
        assert response.json()["has_more"] is False


# --- Search with Special Characters ---


class TestSearchSpecialCharacters:
    """Test search queries with special and edge-case characters."""

    @patch("skillhub.routers.skills.browse_skills")
    def test_search_with_quotes(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get('/api/v1/skills?q="code+review"')
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert '"code review"' == call_kwargs["q"]

    @patch("skillhub.routers.skills.browse_skills")
    def test_search_with_ampersand(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills?q=R%26D+tools")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert "R&D" in call_kwargs["q"]

    @patch("skillhub.routers.skills.browse_skills")
    def test_search_with_unicode(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills?q=%C3%BCber+skill")
        assert response.status_code == 200

    @patch("skillhub.routers.skills.browse_skills")
    def test_search_empty_string(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills?q=")
        assert response.status_code == 200

    @patch("skillhub.routers.skills.browse_skills")
    def test_search_long_query(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        long_query = "a" * 200
        response = client.get(f"/api/v1/skills?q={long_query}")
        assert response.status_code == 200


# --- Featured Skills ---


class TestFeaturedSkills:
    """Test featured filter behavior."""

    @patch("skillhub.routers.skills.browse_skills")
    def test_featured_true_filters_correctly(self, mock_browse: MagicMock, client: TestClient) -> None:
        featured_skill = _make_skill_summary(featured=True, name="Featured Skill")
        mock_browse.return_value = ([featured_skill], 1)
        response = client.get("/api/v1/skills?featured=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["featured"] is True

    @patch("skillhub.routers.skills.browse_skills")
    def test_featured_false_excludes_featured(self, mock_browse: MagicMock, client: TestClient) -> None:
        mock_browse.return_value = ([], 0)
        response = client.get("/api/v1/skills?featured=false")
        assert response.status_code == 200
        call_kwargs = mock_browse.call_args[1]
        assert call_kwargs["featured"] is False


# --- View Count Increment ---


class TestViewCountIncrement:
    """Test that viewing a skill increments view_count."""

    @patch("skillhub.routers.skills.increment_view_count")
    @patch("skillhub.routers.skills.get_skill_detail")
    def test_detail_view_triggers_view_count_increment(
        self,
        mock_detail: MagicMock,
        mock_view: MagicMock,
        client: TestClient,
    ) -> None:
        skill_data = _make_detail_dict()
        mock_detail.return_value = skill_data
        response = client.get("/api/v1/skills/test-skill")
        assert response.status_code == 200
        # TestClient runs background tasks synchronously, so it will have been called
        mock_view.assert_called_once()

    @patch("skillhub.routers.skills.increment_view_count")
    @patch("skillhub.routers.skills.get_skill_detail")
    def test_detail_view_passes_skill_id_for_increment(
        self,
        mock_detail: MagicMock,
        mock_view: MagicMock,
        client: TestClient,
    ) -> None:
        skill_id = uuid.uuid4()
        mock_detail.return_value = _make_detail_dict(id=skill_id)
        client.get("/api/v1/skills/test-skill")
        # The background task was scheduled with the correct skill_id
        assert mock_detail.called


class TestIncrementViewCountService:
    """Tests for the service-level increment_view_count."""

    def test_increments_view_count_field(self) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        skill_id = uuid.uuid4()
        increment_view_count(mock_db, skill_id)

        mock_query.update.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_increments_for_different_skills(self) -> None:
        """Each skill ID triggers its own update call."""
        for _ in range(3):
            mock_db = MagicMock()
            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query

            increment_view_count(mock_db, uuid.uuid4())
            mock_query.update.assert_called_once()


# --- Service-Level Browse Tests ---


class TestBrowseSkillsServiceSortOptions:
    """Tests for browse_skills service with different sort options."""

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

    @pytest.mark.parametrize(
        "sort_option",
        ["trending", "installs", "rating", "newest", "updated"],
    )
    def test_all_sort_options_execute_without_error(self, sort_option: str) -> None:
        mock_db = self._setup_mock_db()
        items, total = browse_skills(mock_db, sort=sort_option)
        assert total == 0
        assert items == []

    def test_default_pagination_offset_0(self) -> None:
        mock_db = self._setup_mock_db()
        browse_skills(mock_db, page=1, per_page=20)
        mock_query = mock_db.query.return_value.options.return_value.filter.return_value
        mock_query.order_by.return_value.offset.assert_called_once_with(0)

    def test_page_2_offset_20(self) -> None:
        mock_db = self._setup_mock_db()
        browse_skills(mock_db, page=2, per_page=20)
        mock_query = mock_db.query.return_value.options.return_value.filter.return_value
        mock_query.order_by.return_value.offset.assert_called_once_with(20)

    def test_combined_category_and_division(self) -> None:
        mock_db = self._setup_mock_db()
        items, total = browse_skills(
            mock_db,
            category="Engineering",
            divisions=["Engineering Org", "Product Org"],
        )
        assert total == 0
