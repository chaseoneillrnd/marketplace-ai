"""Tests for Social router — install, favorite, fork, follow endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from tests.conftest import _make_settings, make_token

USER_ID = "00000000-0000-0000-0000-000000000001"
SKILL_ID = uuid.uuid4()


def _auth_headers(**extra_claims: Any) -> dict[str, str]:
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


class TestInstallEndpoint:
    """Tests for POST/DELETE /api/v1/skills/{slug}/install."""

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/install",
            json={"method": "claude-code", "version": "1.0.0"},
        )
        assert response.status_code == 401

    @patch("skillhub.routers.social.install_skill")
    def test_install_authorized_returns_201(
        self,
        mock_install: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_install.return_value = {
            "id": uuid.uuid4(),
            "skill_id": SKILL_ID,
            "user_id": uuid.UUID(USER_ID),
            "version": "1.0.0",
            "method": "claude-code",
            "installed_at": datetime.now(UTC),
        }
        response = client.post(
            "/api/v1/skills/test-skill/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["method"] == "claude-code"
        assert data["version"] == "1.0.0"

    @patch("skillhub.routers.social.install_skill")
    def test_install_unauthorized_division_returns_403(
        self,
        mock_install: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_install.side_effect = PermissionError("division_restricted")
        response = client.post(
            "/api/v1/skills/test-skill/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=auth_headers,
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "division_restricted"

    @patch("skillhub.routers.social.install_skill")
    def test_install_not_found_returns_404(
        self,
        mock_install: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_install.side_effect = ValueError("Skill 'x' not found")
        response = client.post(
            "/api/v1/skills/x/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_install_invalid_method_returns_422(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/install",
            json={"method": "invalid-method", "version": "1.0.0"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @patch("skillhub.routers.social.uninstall_skill")
    def test_uninstall_returns_204(
        self,
        mock_uninstall: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_uninstall.return_value = None
        response = client.delete(
            "/api/v1/skills/test-skill/install",
            headers=auth_headers,
        )
        assert response.status_code == 204


class TestFavoriteEndpoint:
    """Tests for POST/DELETE /api/v1/skills/{slug}/favorite."""

    @patch("skillhub.routers.social.favorite_skill")
    def test_favorite_returns_200(
        self,
        mock_fav: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_fav.return_value = {
            "user_id": uuid.UUID(USER_ID),
            "skill_id": SKILL_ID,
            "created_at": datetime.now(UTC),
        }
        response = client.post(
            "/api/v1/skills/test-skill/favorite",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @patch("skillhub.routers.social.favorite_skill")
    def test_duplicate_favorite_returns_200(
        self,
        mock_fav: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Duplicate favorite is idempotent — returns 200."""
        mock_fav.return_value = {
            "user_id": uuid.UUID(USER_ID),
            "skill_id": SKILL_ID,
            "created_at": datetime.now(UTC),
        }
        # Call twice
        response1 = client.post("/api/v1/skills/test-skill/favorite", headers=auth_headers)
        response2 = client.post("/api/v1/skills/test-skill/favorite", headers=auth_headers)
        assert response1.status_code == 200
        assert response2.status_code == 200

    @patch("skillhub.routers.social.unfavorite_skill")
    def test_unfavorite_returns_204(
        self,
        mock_unfav: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_unfav.return_value = None
        response = client.delete(
            "/api/v1/skills/test-skill/favorite",
            headers=auth_headers,
        )
        assert response.status_code == 204


class TestForkEndpoint:
    """Tests for POST /api/v1/skills/{slug}/fork."""

    @patch("skillhub.routers.social.fork_skill")
    def test_fork_returns_201_with_new_slug(
        self,
        mock_fork: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_fork.return_value = {
            "id": uuid.uuid4(),
            "original_skill_id": SKILL_ID,
            "forked_skill_id": uuid.uuid4(),
            "forked_skill_slug": "test-skill-fork-abc12345",
            "forked_by": uuid.UUID(USER_ID),
        }
        response = client.post(
            "/api/v1/skills/test-skill/fork",
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "fork" in data["forked_skill_slug"]

    def test_fork_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.post("/api/v1/skills/test-skill/fork")
        assert response.status_code == 401


class TestFollowEndpoint:
    """Tests for POST /api/v1/skills/{slug}/follow."""

    @patch("skillhub.routers.social.follow_user")
    def test_follow_returns_200(
        self,
        mock_follow: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_follow.return_value = {
            "follower_id": uuid.UUID(USER_ID),
            "followed_user_id": uuid.uuid4(),
            "created_at": datetime.now(UTC),
        }
        response = client.post(
            "/api/v1/skills/test-skill/follow",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @patch("skillhub.routers.social.follow_user")
    def test_follow_upsert_no_error(
        self,
        mock_follow: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Second follow = no error (idempotent)."""
        mock_follow.return_value = {
            "follower_id": uuid.UUID(USER_ID),
            "followed_user_id": uuid.uuid4(),
            "created_at": datetime.now(UTC),
        }
        response1 = client.post("/api/v1/skills/test-skill/follow", headers=auth_headers)
        response2 = client.post("/api/v1/skills/test-skill/follow", headers=auth_headers)
        assert response1.status_code == 200
        assert response2.status_code == 200
