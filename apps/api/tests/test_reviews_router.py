"""Tests for reviews and comments router endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from skillhub.services.reviews import DuplicateReviewError
from tests.conftest import _make_settings, make_token

USER_ID = "00000000-0000-0000-0000-000000000001"
OTHER_USER_ID = "00000000-0000-0000-0000-000000000002"
SKILL_ID = uuid.uuid4()
REVIEW_ID = uuid.uuid4()
COMMENT_ID = uuid.uuid4()
NOW = datetime.now(UTC)


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


# --- Reviews ---


class TestGetReviews:
    """Tests for GET /api/v1/skills/{slug}/reviews."""

    @patch("skillhub.routers.social.list_reviews")
    def test_returns_paginated_reviews(
        self,
        mock_list: MagicMock,
        client: TestClient,
    ) -> None:
        mock_list.return_value = (
            [
                {
                    "id": REVIEW_ID,
                    "skill_id": SKILL_ID,
                    "user_id": uuid.UUID(USER_ID),
                    "rating": 5,
                    "body": "Great!",
                    "helpful_count": 3,
                    "unhelpful_count": 0,
                    "created_at": NOW,
                    "updated_at": NOW,
                }
            ],
            1,
        )
        response = client.get("/api/v1/skills/test-skill/reviews")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["rating"] == 5


class TestCreateReview:
    """Tests for POST /api/v1/skills/{slug}/reviews."""

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": 5, "body": "Great!"},
        )
        assert response.status_code == 401

    @patch("skillhub.routers.social.create_review")
    def test_creates_review_returns_201(
        self,
        mock_create: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_create.return_value = {
            "id": REVIEW_ID,
            "skill_id": SKILL_ID,
            "user_id": uuid.UUID(USER_ID),
            "rating": 5,
            "body": "Great!",
            "helpful_count": 0,
            "unhelpful_count": 0,
            "created_at": NOW,
            "updated_at": NOW,
        }
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": 5, "body": "Great!"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5

    @patch("skillhub.routers.social.create_review")
    def test_duplicate_review_returns_409(
        self,
        mock_create: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_create.side_effect = DuplicateReviewError("Already reviewed")
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": 5, "body": "Again!"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_invalid_rating_returns_422(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": 6, "body": "Too high"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_rating_zero_returns_422(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": 0, "body": "Too low"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestPatchReview:
    """Tests for PATCH /api/v1/skills/{slug}/reviews/{id}."""

    @patch("skillhub.routers.social.update_review")
    def test_owner_can_patch(
        self,
        mock_update: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_update.return_value = {
            "id": REVIEW_ID,
            "skill_id": SKILL_ID,
            "user_id": uuid.UUID(USER_ID),
            "rating": 3,
            "body": "Updated",
            "helpful_count": 0,
            "unhelpful_count": 0,
            "created_at": NOW,
            "updated_at": NOW,
        }
        response = client.patch(
            f"/api/v1/skills/test-skill/reviews/{REVIEW_ID}",
            json={"rating": 3, "body": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["rating"] == 3

    @patch("skillhub.routers.social.update_review")
    def test_non_owner_patch_returns_403(
        self,
        mock_update: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_update.side_effect = PermissionError("Only the review owner can update")
        response = client.patch(
            f"/api/v1/skills/test-skill/reviews/{REVIEW_ID}",
            json={"rating": 1},
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestReviewVote:
    """Tests for POST /api/v1/skills/{slug}/reviews/{id}/vote."""

    @patch("skillhub.routers.social.vote_on_review")
    def test_vote_returns_204(
        self,
        mock_vote: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_vote.return_value = None
        response = client.post(
            f"/api/v1/skills/test-skill/reviews/{REVIEW_ID}/vote",
            json={"vote": "helpful"},
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_invalid_vote_returns_422(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.post(
            f"/api/v1/skills/test-skill/reviews/{REVIEW_ID}/vote",
            json={"vote": "invalid"},
            headers=auth_headers,
        )
        assert response.status_code == 422


# --- Comments ---


class TestGetComments:
    """Tests for GET /api/v1/skills/{slug}/comments."""

    @patch("skillhub.routers.social.list_comments")
    def test_returns_paginated_comments(
        self,
        mock_list: MagicMock,
        client: TestClient,
    ) -> None:
        mock_list.return_value = (
            [
                {
                    "id": COMMENT_ID,
                    "skill_id": SKILL_ID,
                    "user_id": uuid.UUID(USER_ID),
                    "body": "Nice!",
                    "upvote_count": 0,
                    "deleted_at": None,
                    "created_at": NOW,
                    "replies": [],
                }
            ],
            1,
        )
        response = client.get("/api/v1/skills/test-skill/comments")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["body"] == "Nice!"


class TestCreateComment:
    """Tests for POST /api/v1/skills/{slug}/comments."""

    @patch("skillhub.routers.social.create_comment")
    def test_creates_comment_returns_201(
        self,
        mock_create: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_create.return_value = {
            "id": COMMENT_ID,
            "skill_id": SKILL_ID,
            "user_id": uuid.UUID(USER_ID),
            "body": "Hello!",
            "upvote_count": 0,
            "deleted_at": None,
            "created_at": NOW,
            "replies": [],
        }
        response = client.post(
            "/api/v1/skills/test-skill/comments",
            json={"body": "Hello!"},
            headers=auth_headers,
        )
        assert response.status_code == 201


class TestDeleteComment:
    """Tests for DELETE /api/v1/skills/{slug}/comments/{id}."""

    @patch("skillhub.routers.social.delete_comment")
    def test_soft_delete_returns_200(
        self,
        mock_delete: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_delete.return_value = {
            "id": COMMENT_ID,
            "skill_id": SKILL_ID,
            "user_id": uuid.UUID(USER_ID),
            "body": "[deleted]",
            "upvote_count": 0,
            "deleted_at": NOW,
            "created_at": NOW,
            "replies": [],
        }
        response = client.delete(
            f"/api/v1/skills/test-skill/comments/{COMMENT_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["body"] == "[deleted]"

    @patch("skillhub.routers.social.delete_comment")
    def test_non_owner_delete_returns_403(
        self,
        mock_delete: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_delete.side_effect = PermissionError("Not authorized")
        response = client.delete(
            f"/api/v1/skills/test-skill/comments/{COMMENT_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestReply:
    """Tests for POST /api/v1/skills/{slug}/comments/{id}/replies."""

    @patch("skillhub.routers.social.create_reply")
    def test_creates_reply_returns_201(
        self,
        mock_reply: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_reply.return_value = {
            "id": uuid.uuid4(),
            "comment_id": COMMENT_ID,
            "user_id": uuid.UUID(USER_ID),
            "body": "A reply",
            "deleted_at": None,
            "created_at": NOW,
        }
        response = client.post(
            f"/api/v1/skills/test-skill/comments/{COMMENT_ID}/replies",
            json={"body": "A reply"},
            headers=auth_headers,
        )
        assert response.status_code == 201


class TestCommentVote:
    """Tests for POST /api/v1/skills/{slug}/comments/{id}/vote."""

    @patch("skillhub.routers.social.vote_on_comment")
    def test_vote_returns_204(
        self,
        mock_vote: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_vote.return_value = None
        response = client.post(
            f"/api/v1/skills/test-skill/comments/{COMMENT_ID}/vote",
            headers=auth_headers,
        )
        assert response.status_code == 204
