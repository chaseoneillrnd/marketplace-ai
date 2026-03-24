"""Tests for the users blueprint (profile and personal collections)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tests.conftest import make_token

USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
SKILL_ID = uuid4()


def _auth_headers(token: str | None = None) -> dict[str, str]:
    if token is None:
        token = make_token(payload={
            "sub": "test-user",
            "user_id": USER_ID,
            "division": "engineering",
        })
    return {"Authorization": f"Bearer {token}"}


def _make_user_profile(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "user_id": USER_ID,
        "sub": "test-user",
        "name": "Test User",
        "division": "engineering",
        "role": "engineer",
        "is_platform_team": False,
        "is_security_team": False,
        "skills_installed": 5,
        "skills_submitted": 2,
        "reviews_written": 10,
        "forks_made": 1,
    }
    defaults.update(overrides)
    return defaults


def _make_user_skill_summary(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "id": SKILL_ID,
        "slug": "cool-skill",
        "name": "Cool Skill",
        "short_desc": "Does cool things",
        "category": "productivity",
        "divisions": ["engineering"],
        "tags": ["ai"],
        "author": "alice",
        "author_type": "individual",
        "version": "1.0.0",
        "install_method": "mcp",
        "verified": True,
        "featured": False,
        "install_count": 10,
        "fork_count": 2,
        "favorite_count": 5,
        "avg_rating": "4.0",
        "review_count": 3,
        "days_ago": 1,
        "user_has_installed": True,
        "user_has_favorited": False,
    }
    defaults.update(overrides)
    return defaults


def _make_submission_summary(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "id": uuid4(),
        "display_id": "SUB-001",
        "name": "New Skill",
        "short_desc": "A submission",
        "category": "productivity",
        "status": "pending_review",
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# GET /api/v1/users/me
# ---------------------------------------------------------------------------
class TestGetMe:
    """GET /api/v1/users/me — current user profile."""

    @patch("skillhub_flask.blueprints.users.get_user_profile")
    def test_returns_200_with_profile(self, mock_profile: MagicMock, client: Any) -> None:
        mock_profile.return_value = _make_user_profile()

        resp = client.get("/api/v1/users/me", headers=_auth_headers())
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["user_id"] == USER_ID
        assert data["name"] == "Test User"
        assert data["skills_installed"] == 5

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.users.get_user_profile")
    def test_passes_current_user_to_service(self, mock_profile: MagicMock, client: Any) -> None:
        mock_profile.return_value = _make_user_profile()

        client.get("/api/v1/users/me", headers=_auth_headers())

        _, call_args = mock_profile.call_args
        # Second positional arg is the current_user dict
        current_user = mock_profile.call_args[0][1]
        assert current_user["sub"] == "test-user"


# ---------------------------------------------------------------------------
# GET /api/v1/users/me/installs
# ---------------------------------------------------------------------------
class TestListInstalls:
    """GET /api/v1/users/me/installs — user's installed skills."""

    @patch("skillhub_flask.blueprints.users.get_user_installs")
    def test_returns_200_with_installs(self, mock_installs: MagicMock, client: Any) -> None:
        mock_installs.return_value = ([_make_user_skill_summary()], 1)

        resp = client.get("/api/v1/users/me/installs", headers=_auth_headers())
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert data["has_more"] is False
        assert len(data["items"]) == 1
        assert data["items"][0]["slug"] == "cool-skill"

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.get("/api/v1/users/me/installs")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.users.get_user_installs")
    def test_pagination_params(self, mock_installs: MagicMock, client: Any) -> None:
        mock_installs.return_value = ([], 0)

        client.get("/api/v1/users/me/installs?page=3&per_page=5", headers=_auth_headers())
        call_kwargs = mock_installs.call_args[1]
        assert call_kwargs["page"] == 3
        assert call_kwargs["per_page"] == 5

    @patch("skillhub_flask.blueprints.users.get_user_installs")
    def test_include_uninstalled_param(self, mock_installs: MagicMock, client: Any) -> None:
        mock_installs.return_value = ([], 0)

        client.get("/api/v1/users/me/installs?include_uninstalled=true", headers=_auth_headers())
        call_kwargs = mock_installs.call_args[1]
        assert call_kwargs["include_uninstalled"] is True

    @patch("skillhub_flask.blueprints.users.get_user_installs")
    def test_has_more_when_paginated(self, mock_installs: MagicMock, client: Any) -> None:
        mock_installs.return_value = ([_make_user_skill_summary()], 50)

        resp = client.get("/api/v1/users/me/installs?page=1&per_page=5", headers=_auth_headers())
        data = resp.get_json()
        assert data["has_more"] is True


# ---------------------------------------------------------------------------
# GET /api/v1/users/me/favorites
# ---------------------------------------------------------------------------
class TestListFavorites:
    """GET /api/v1/users/me/favorites — user's favorited skills."""

    @patch("skillhub_flask.blueprints.users.get_user_favorites")
    def test_returns_200_with_favorites(self, mock_favs: MagicMock, client: Any) -> None:
        mock_favs.return_value = ([_make_user_skill_summary()], 1)

        resp = client.get("/api/v1/users/me/favorites", headers=_auth_headers())
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.get("/api/v1/users/me/favorites")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.users.get_user_favorites")
    def test_empty_favorites(self, mock_favs: MagicMock, client: Any) -> None:
        mock_favs.return_value = ([], 0)

        resp = client.get("/api/v1/users/me/favorites", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# GET /api/v1/users/me/forks
# ---------------------------------------------------------------------------
class TestListForks:
    """GET /api/v1/users/me/forks — user's forked skills."""

    @patch("skillhub_flask.blueprints.users.get_user_forks")
    def test_returns_200_with_forks(self, mock_forks: MagicMock, client: Any) -> None:
        mock_forks.return_value = ([_make_user_skill_summary()], 1)

        resp = client.get("/api/v1/users/me/forks", headers=_auth_headers())
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.get("/api/v1/users/me/forks")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.users.get_user_forks")
    def test_pagination_fields_present(self, mock_forks: MagicMock, client: Any) -> None:
        mock_forks.return_value = ([], 0)

        resp = client.get("/api/v1/users/me/forks", headers=_auth_headers())
        data = resp.get_json()
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "has_more" in data
        assert "items" in data


# ---------------------------------------------------------------------------
# GET /api/v1/users/me/submissions
# ---------------------------------------------------------------------------
class TestListSubmissions:
    """GET /api/v1/users/me/submissions — user's skill submissions."""

    @patch("skillhub_flask.blueprints.users.get_user_submissions")
    def test_returns_200_with_submissions(self, mock_subs: MagicMock, client: Any) -> None:
        mock_subs.return_value = ([_make_submission_summary()], 1)

        resp = client.get("/api/v1/users/me/submissions", headers=_auth_headers())
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["display_id"] == "SUB-001"
        assert data["items"][0]["status"] == "pending_review"

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.get("/api/v1/users/me/submissions")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.users.get_user_submissions")
    def test_empty_submissions(self, mock_subs: MagicMock, client: Any) -> None:
        mock_subs.return_value = ([], 0)

        resp = client.get("/api/v1/users/me/submissions", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["has_more"] is False
