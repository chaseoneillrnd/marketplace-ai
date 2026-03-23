"""Tests for Users router — profile, installs, favorites, forks, submissions."""

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

USER_ID = "00000000-0000-0000-0000-000000000001"


def _auth_headers(**extra_claims: Any) -> dict[str, str]:
    """Create auth headers with a valid JWT."""
    claims: dict[str, Any] = {
        "user_id": USER_ID,
        "sub": "test-user",
        "name": "Test User",
        "division": "engineering",
        "role": "engineer",
        "is_platform_team": False,
        "is_security_team": False,
    }
    claims.update(extra_claims)
    token = make_token(claims)
    return {"Authorization": f"Bearer {token}"}


def _make_skill_summary(**overrides: Any) -> dict[str, Any]:
    """Create a mock skill summary dict for collection responses."""
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "slug": "test-skill",
        "name": "Test Skill",
        "short_desc": "A test skill",
        "category": "engineering",
        "divisions": ["engineering"],
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


def _make_submission_summary(**overrides: Any) -> dict[str, Any]:
    """Create a mock submission summary dict."""
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "display_id": "SKL-ABC123",
        "name": "My Submission",
        "short_desc": "A submitted skill",
        "category": "engineering",
        "status": "submitted",
        "created_at": datetime.now(UTC).isoformat(),
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
    return _auth_headers()


class TestGetProfile:
    """Tests for GET /api/v1/users/me."""

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    @patch("skillhub.routers.users.get_user_profile")
    def test_returns_profile_with_jwt_claims(
        self,
        mock_profile: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_profile.return_value = {
            "user_id": USER_ID,
            "sub": "test-user",
            "name": "Test User",
            "division": "engineering",
            "role": "engineer",
            "is_platform_team": False,
            "is_security_team": False,
            "skills_installed": 0,
            "skills_submitted": 0,
            "reviews_written": 0,
            "forks_made": 0,
        }
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test User"
        assert data["division"] == "engineering"
        assert data["role"] == "engineer"

    @patch("skillhub.routers.users.get_user_profile")
    def test_profile_stats_accurate_after_installs(
        self,
        mock_profile: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_profile.return_value = {
            "user_id": USER_ID,
            "sub": "test-user",
            "name": "Test User",
            "division": "engineering",
            "role": "engineer",
            "is_platform_team": False,
            "is_security_team": False,
            "skills_installed": 2,
            "skills_submitted": 3,
            "reviews_written": 5,
            "forks_made": 1,
        }
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["skills_installed"] == 2
        assert data["skills_submitted"] == 3
        assert data["reviews_written"] == 5
        assert data["forks_made"] == 1


class TestGetInstalls:
    """Tests for GET /api/v1/users/me/installs."""

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/v1/users/me/installs")
        assert response.status_code == 401

    @patch("skillhub.routers.users.get_user_installs")
    def test_returns_installed_skills(
        self,
        mock_installs: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        skill = _make_skill_summary(slug="installed-skill")
        mock_installs.return_value = ([skill], 1)
        response = client.get("/api/v1/users/me/installs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["slug"] == "installed-skill"

    @patch("skillhub.routers.users.get_user_installs")
    def test_uninstalled_excluded_by_default(
        self,
        mock_installs: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_installs.return_value = ([], 0)
        response = client.get("/api/v1/users/me/installs", headers=auth_headers)
        assert response.status_code == 200
        # Verify the service was called with include_uninstalled=False
        mock_installs.assert_called_once()
        call_kwargs = mock_installs.call_args[1]
        assert call_kwargs["include_uninstalled"] is False

    @patch("skillhub.routers.users.get_user_installs")
    def test_include_uninstalled_when_requested(
        self,
        mock_installs: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_installs.return_value = ([], 0)
        response = client.get("/api/v1/users/me/installs?include_uninstalled=true", headers=auth_headers)
        assert response.status_code == 200
        call_kwargs = mock_installs.call_args[1]
        assert call_kwargs["include_uninstalled"] is True

    @patch("skillhub.routers.users.get_user_installs")
    def test_pagination(
        self,
        mock_installs: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_installs.return_value = ([_make_skill_summary()], 50)
        response = client.get("/api/v1/users/me/installs?page=1&per_page=20", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is True
        assert data["page"] == 1
        assert data["per_page"] == 20


class TestGetFavorites:
    """Tests for GET /api/v1/users/me/favorites."""

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/v1/users/me/favorites")
        assert response.status_code == 401

    @patch("skillhub.routers.users.get_user_favorites")
    def test_returns_favorited_skills(
        self,
        mock_favorites: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        skill = _make_skill_summary(slug="fav-skill")
        mock_favorites.return_value = ([skill], 1)
        response = client.get("/api/v1/users/me/favorites", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["slug"] == "fav-skill"

    @patch("skillhub.routers.users.get_user_favorites")
    def test_pagination(
        self,
        mock_favorites: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_favorites.return_value = ([_make_skill_summary()], 30)
        response = client.get("/api/v1/users/me/favorites?page=2&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 10
        assert data["has_more"] is True


class TestGetForks:
    """Tests for GET /api/v1/users/me/forks."""

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/v1/users/me/forks")
        assert response.status_code == 401

    @patch("skillhub.routers.users.get_user_forks")
    def test_returns_forked_skills(
        self,
        mock_forks: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        skill = _make_skill_summary(slug="forked-skill")
        mock_forks.return_value = ([skill], 1)
        response = client.get("/api/v1/users/me/forks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["slug"] == "forked-skill"


class TestGetSubmissions:
    """Tests for GET /api/v1/users/me/submissions."""

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/v1/users/me/submissions")
        assert response.status_code == 401

    @patch("skillhub.routers.users.get_user_submissions")
    def test_returns_own_submissions_with_status(
        self,
        mock_submissions: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        submission = _make_submission_summary(status="gate1_passed")
        mock_submissions.return_value = ([submission], 1)
        response = client.get("/api/v1/users/me/submissions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "gate1_passed"
        assert data["items"][0]["display_id"] == "SKL-ABC123"

    @patch("skillhub.routers.users.get_user_submissions")
    def test_pagination(
        self,
        mock_submissions: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_submissions.return_value = ([_make_submission_summary()], 25)
        response = client.get("/api/v1/users/me/submissions?page=1&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is True
