"""Comprehensive tests for the social blueprint (16 routes)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest

from tests.conftest import _make_settings, make_token

SLUG = "my-awesome-skill"
USER_ID = str(uuid4())
SKILL_ID = str(uuid4())
REVIEW_ID = str(uuid4())
COMMENT_ID = str(uuid4())
REPLY_ID = str(uuid4())
NOW = datetime.now(timezone.utc).isoformat()


def _auth_headers(
    user_id: str = USER_ID,
    division: str = "engineering",
    is_platform_team: bool = False,
) -> dict[str, str]:
    token = make_token(
        payload={
            "sub": "test-user",
            "user_id": user_id,
            "division": division,
            "is_platform_team": is_platform_team,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def _install_result() -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "skill_id": SKILL_ID,
        "user_id": USER_ID,
        "version": "1.0.0",
        "method": "claude-code",
        "installed_at": NOW,
    }


def _favorite_result() -> dict[str, Any]:
    return {
        "user_id": USER_ID,
        "skill_id": SKILL_ID,
        "created_at": NOW,
    }


def _fork_result() -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "original_skill_id": SKILL_ID,
        "forked_skill_id": str(uuid4()),
        "forked_skill_slug": "my-awesome-skill-fork",
        "forked_by": USER_ID,
    }


def _follow_result() -> dict[str, Any]:
    return {
        "follower_id": USER_ID,
        "followed_user_id": str(uuid4()),
        "created_at": NOW,
    }


def _review_result(**overrides: Any) -> dict[str, Any]:
    result = {
        "id": REVIEW_ID,
        "skill_id": SKILL_ID,
        "user_id": USER_ID,
        "rating": 5,
        "body": "Great skill!",
        "helpful_count": 0,
        "unhelpful_count": 0,
        "created_at": NOW,
        "updated_at": NOW,
    }
    result.update(overrides)
    return result


def _comment_result(**overrides: Any) -> dict[str, Any]:
    result = {
        "id": COMMENT_ID,
        "skill_id": SKILL_ID,
        "user_id": USER_ID,
        "body": "Nice work!",
        "upvote_count": 0,
        "deleted_at": None,
        "created_at": NOW,
        "replies": [],
    }
    result.update(overrides)
    return result


def _reply_result() -> dict[str, Any]:
    return {
        "id": REPLY_ID,
        "comment_id": COMMENT_ID,
        "user_id": USER_ID,
        "body": "Thanks!",
        "deleted_at": None,
        "created_at": NOW,
    }


# ── 1. Install: POST /{slug}/install ─────────────────────────────────────


class TestPostInstall:
    """POST /api/v1/skills/{slug}/install"""

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_install_success(self, mock_install: Any, client: Any) -> None:
        mock_install.return_value = _install_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["skill_id"] == SKILL_ID
        assert data["method"] == "claude-code"
        mock_install.assert_called_once()

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_install_division_restricted(self, mock_install: Any, client: Any) -> None:
        mock_install.side_effect = PermissionError("Division restricted")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["detail"]["error"] == "division_restricted"

    def test_install_no_auth(self, client: Any) -> None:
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
        )
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_install_skill_not_found(self, mock_install: Any, client: Any) -> None:
        mock_install.side_effect = ValueError("Skill not found")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 404
        assert "Skill not found" in resp.get_json()["detail"]


# ── 2. Uninstall: DELETE /{slug}/install ──────────────────────────────────


class TestDeleteInstall:
    """DELETE /api/v1/skills/{slug}/install"""

    @patch("skillhub_flask.blueprints.social.uninstall_skill")
    def test_uninstall_success(self, mock_uninstall: Any, client: Any) -> None:
        mock_uninstall.return_value = None
        resp = client.delete(
            f"/api/v1/skills/{SLUG}/install",
            headers=_auth_headers(),
        )
        assert resp.status_code == 204
        mock_uninstall.assert_called_once()

    def test_uninstall_no_auth(self, client: Any) -> None:
        resp = client.delete(f"/api/v1/skills/{SLUG}/install")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.uninstall_skill")
    def test_uninstall_not_found(self, mock_uninstall: Any, client: Any) -> None:
        mock_uninstall.side_effect = ValueError("Not found")
        resp = client.delete(
            f"/api/v1/skills/{SLUG}/install",
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


# ── 3. Favorite: POST /{slug}/favorite ───────────────────────────────────


class TestPostFavorite:
    """POST /api/v1/skills/{slug}/favorite"""

    @patch("skillhub_flask.blueprints.social.favorite_skill")
    def test_favorite_success_idempotent(self, mock_fav: Any, client: Any) -> None:
        mock_fav.return_value = _favorite_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/favorite",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user_id"] == USER_ID
        assert data["skill_id"] == SKILL_ID

    @patch("skillhub_flask.blueprints.social.favorite_skill")
    def test_favorite_called_twice_idempotent(self, mock_fav: Any, client: Any) -> None:
        mock_fav.return_value = _favorite_result()
        headers = _auth_headers()
        resp1 = client.post(f"/api/v1/skills/{SLUG}/favorite", headers=headers)
        resp2 = client.post(f"/api/v1/skills/{SLUG}/favorite", headers=headers)
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert mock_fav.call_count == 2

    def test_favorite_no_auth(self, client: Any) -> None:
        resp = client.post(f"/api/v1/skills/{SLUG}/favorite")
        assert resp.status_code == 401


# ── 4. Unfavorite: DELETE /{slug}/favorite ────────────────────────────────


class TestDeleteFavorite:
    """DELETE /api/v1/skills/{slug}/favorite"""

    @patch("skillhub_flask.blueprints.social.unfavorite_skill")
    def test_unfavorite_success(self, mock_unfav: Any, client: Any) -> None:
        mock_unfav.return_value = None
        resp = client.delete(
            f"/api/v1/skills/{SLUG}/favorite",
            headers=_auth_headers(),
        )
        assert resp.status_code == 204

    def test_unfavorite_no_auth(self, client: Any) -> None:
        resp = client.delete(f"/api/v1/skills/{SLUG}/favorite")
        assert resp.status_code == 401


# ── 5. Fork: POST /{slug}/fork ───────────────────────────────────────────


class TestPostFork:
    """POST /api/v1/skills/{slug}/fork"""

    @patch("skillhub_flask.blueprints.social.fork_skill")
    def test_fork_success(self, mock_fork: Any, client: Any) -> None:
        result = _fork_result()
        mock_fork.return_value = result
        resp = client.post(
            f"/api/v1/skills/{SLUG}/fork",
            headers=_auth_headers(),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["forked_skill_slug"] == "my-awesome-skill-fork"
        assert data["forked_by"] == USER_ID

    def test_fork_no_auth(self, client: Any) -> None:
        resp = client.post(f"/api/v1/skills/{SLUG}/fork")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.fork_skill")
    def test_fork_not_found(self, mock_fork: Any, client: Any) -> None:
        mock_fork.side_effect = ValueError("Skill not found")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/fork",
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


# ── 6. Follow: POST /{slug}/follow ───────────────────────────────────────


class TestPostFollow:
    """POST /api/v1/skills/{slug}/follow"""

    @patch("skillhub_flask.blueprints.social.follow_user")
    def test_follow_success(self, mock_follow: Any, client: Any) -> None:
        mock_follow.return_value = _follow_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/follow",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["follower_id"] == USER_ID

    def test_follow_no_auth(self, client: Any) -> None:
        resp = client.post(f"/api/v1/skills/{SLUG}/follow")
        assert resp.status_code == 401


# ── 7. Unfollow: DELETE /{slug}/follow ────────────────────────────────────


class TestDeleteFollow:
    """DELETE /api/v1/skills/{slug}/follow"""

    @patch("skillhub_flask.blueprints.social.unfollow_user")
    def test_unfollow_success(self, mock_unfollow: Any, client: Any) -> None:
        mock_unfollow.return_value = None
        resp = client.delete(
            f"/api/v1/skills/{SLUG}/follow",
            headers=_auth_headers(),
        )
        assert resp.status_code == 204

    def test_unfollow_no_auth(self, client: Any) -> None:
        resp = client.delete(f"/api/v1/skills/{SLUG}/follow")
        assert resp.status_code == 401


# ── 8. List reviews: GET /{slug}/reviews ──────────────────────────────────


class TestGetReviews:
    """GET /api/v1/skills/{slug}/reviews"""

    @patch("skillhub_flask.blueprints.social.list_reviews")
    def test_list_reviews_with_pagination(self, mock_list: Any, client: Any) -> None:
        items = [_review_result(id=str(uuid4())) for _ in range(2)]
        mock_list.return_value = (items, 5)
        resp = client.get(
            f"/api/v1/skills/{SLUG}/reviews?page=1&per_page=2",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["has_more"] is True
        assert len(data["items"]) == 2

    @patch("skillhub_flask.blueprints.social.list_reviews")
    def test_list_reviews_defaults(self, mock_list: Any, client: Any) -> None:
        mock_list.return_value = ([], 0)
        resp = client.get(
            f"/api/v1/skills/{SLUG}/reviews",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert data["has_more"] is False

    def test_list_reviews_no_auth(self, client: Any) -> None:
        resp = client.get(f"/api/v1/skills/{SLUG}/reviews")
        assert resp.status_code == 401


# ── 9. Create review: POST /{slug}/reviews ────────────────────────────────


class TestPostReview:
    """POST /api/v1/skills/{slug}/reviews"""

    @patch("skillhub_flask.blueprints.social.create_review")
    def test_create_review_success(self, mock_create: Any, client: Any) -> None:
        mock_create.return_value = _review_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/reviews",
            json={"rating": 5, "body": "Great skill!"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["rating"] == 5
        assert data["body"] == "Great skill!"

    @patch("skillhub_flask.blueprints.social.create_review")
    def test_create_review_duplicate_409(self, mock_create: Any, client: Any) -> None:
        from skillhub.services.reviews import DuplicateReviewError

        mock_create.side_effect = DuplicateReviewError("Already reviewed")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/reviews",
            json={"rating": 4, "body": "Another review"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 409
        assert "Already reviewed" in resp.get_json()["detail"]

    def test_create_review_no_auth(self, client: Any) -> None:
        resp = client.post(
            f"/api/v1/skills/{SLUG}/reviews",
            json={"rating": 5, "body": "Great!"},
        )
        assert resp.status_code == 401


# ── 10. Update review: PATCH /{slug}/reviews/{id} ─────────────────────────


class TestPatchReview:
    """PATCH /api/v1/skills/{slug}/reviews/{review_id}"""

    @patch("skillhub_flask.blueprints.social.update_review")
    def test_update_review_success(self, mock_update: Any, client: Any) -> None:
        mock_update.return_value = _review_result(rating=4, body="Updated!")
        resp = client.patch(
            f"/api/v1/skills/{SLUG}/reviews/{REVIEW_ID}",
            json={"rating": 4, "body": "Updated!"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["rating"] == 4
        assert data["body"] == "Updated!"

    @patch("skillhub_flask.blueprints.social.update_review")
    def test_update_review_not_owner_403(self, mock_update: Any, client: Any) -> None:
        mock_update.side_effect = PermissionError("Not the review owner")
        resp = client.patch(
            f"/api/v1/skills/{SLUG}/reviews/{REVIEW_ID}",
            json={"rating": 1},
            headers=_auth_headers(),
        )
        assert resp.status_code == 403
        assert "Not the review owner" in resp.get_json()["detail"]

    def test_update_review_no_auth(self, client: Any) -> None:
        resp = client.patch(
            f"/api/v1/skills/{SLUG}/reviews/{REVIEW_ID}",
            json={"rating": 3},
        )
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.update_review")
    def test_update_review_not_found(self, mock_update: Any, client: Any) -> None:
        mock_update.side_effect = ValueError("Review not found")
        resp = client.patch(
            f"/api/v1/skills/{SLUG}/reviews/{REVIEW_ID}",
            json={"body": "new text"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


# ── 11. Vote review: POST /{slug}/reviews/{id}/vote ───────────────────────


class TestPostReviewVote:
    """POST /api/v1/skills/{slug}/reviews/{review_id}/vote"""

    @patch("skillhub_flask.blueprints.social.vote_on_review")
    def test_vote_review_success(self, mock_vote: Any, client: Any) -> None:
        mock_vote.return_value = None
        resp = client.post(
            f"/api/v1/skills/{SLUG}/reviews/{REVIEW_ID}/vote",
            json={"vote": "helpful"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 204

    @patch("skillhub_flask.blueprints.social.vote_on_review")
    def test_vote_review_unhelpful(self, mock_vote: Any, client: Any) -> None:
        mock_vote.return_value = None
        resp = client.post(
            f"/api/v1/skills/{SLUG}/reviews/{REVIEW_ID}/vote",
            json={"vote": "unhelpful"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 204

    def test_vote_review_no_auth(self, client: Any) -> None:
        resp = client.post(
            f"/api/v1/skills/{SLUG}/reviews/{REVIEW_ID}/vote",
            json={"vote": "helpful"},
        )
        assert resp.status_code == 401


# ── 12. List comments: GET /{slug}/comments ───────────────────────────────


class TestGetComments:
    """GET /api/v1/skills/{slug}/comments"""

    @patch("skillhub_flask.blueprints.social.list_comments")
    def test_list_comments_with_pagination(self, mock_list: Any, client: Any) -> None:
        items = [_comment_result(id=str(uuid4())) for _ in range(3)]
        mock_list.return_value = (items, 10)
        resp = client.get(
            f"/api/v1/skills/{SLUG}/comments?page=1&per_page=3",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 10
        assert data["page"] == 1
        assert data["per_page"] == 3
        assert data["has_more"] is True
        assert len(data["items"]) == 3

    @patch("skillhub_flask.blueprints.social.list_comments")
    def test_list_comments_empty(self, mock_list: Any, client: Any) -> None:
        mock_list.return_value = ([], 0)
        resp = client.get(
            f"/api/v1/skills/{SLUG}/comments",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["has_more"] is False

    def test_list_comments_no_auth(self, client: Any) -> None:
        resp = client.get(f"/api/v1/skills/{SLUG}/comments")
        assert resp.status_code == 401


# ── 13. Create comment: POST /{slug}/comments ────────────────────────────


class TestPostComment:
    """POST /api/v1/skills/{slug}/comments"""

    @patch("skillhub_flask.blueprints.social.create_comment")
    def test_create_comment_success(self, mock_create: Any, client: Any) -> None:
        mock_create.return_value = _comment_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/comments",
            json={"body": "Nice work!"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["body"] == "Nice work!"
        assert data["user_id"] == USER_ID

    def test_create_comment_no_auth(self, client: Any) -> None:
        resp = client.post(
            f"/api/v1/skills/{SLUG}/comments",
            json={"body": "Nice work!"},
        )
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.create_comment")
    def test_create_comment_skill_not_found(self, mock_create: Any, client: Any) -> None:
        mock_create.side_effect = ValueError("Skill not found")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/comments",
            json={"body": "Hello"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


# ── 14. Delete comment: DELETE /{slug}/comments/{id} ──────────────────────


class TestDeleteComment:
    """DELETE /api/v1/skills/{slug}/comments/{comment_id}"""

    @patch("skillhub_flask.blueprints.social.delete_comment")
    def test_delete_comment_soft_delete(self, mock_delete: Any, client: Any) -> None:
        mock_delete.return_value = _comment_result(deleted_at=NOW)
        resp = client.delete(
            f"/api/v1/skills/{SLUG}/comments/{COMMENT_ID}",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["deleted_at"] is not None

    @patch("skillhub_flask.blueprints.social.delete_comment")
    def test_delete_comment_platform_team(self, mock_delete: Any, client: Any) -> None:
        mock_delete.return_value = _comment_result(deleted_at=NOW)
        resp = client.delete(
            f"/api/v1/skills/{SLUG}/comments/{COMMENT_ID}",
            headers=_auth_headers(is_platform_team=True),
        )
        assert resp.status_code == 200
        # Verify is_platform was passed through
        call_kwargs = mock_delete.call_args
        assert call_kwargs.kwargs.get("is_platform_team") is True

    def test_delete_comment_no_auth(self, client: Any) -> None:
        resp = client.delete(f"/api/v1/skills/{SLUG}/comments/{COMMENT_ID}")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.delete_comment")
    def test_delete_comment_not_owner_403(self, mock_delete: Any, client: Any) -> None:
        mock_delete.side_effect = PermissionError("Not the comment owner")
        resp = client.delete(
            f"/api/v1/skills/{SLUG}/comments/{COMMENT_ID}",
            headers=_auth_headers(),
        )
        assert resp.status_code == 403


# ── 15. Reply: POST /{slug}/comments/{id}/replies ────────────────────────


class TestPostReply:
    """POST /api/v1/skills/{slug}/comments/{comment_id}/replies"""

    @patch("skillhub_flask.blueprints.social.create_reply")
    def test_reply_success(self, mock_reply: Any, client: Any) -> None:
        mock_reply.return_value = _reply_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/comments/{COMMENT_ID}/replies",
            json={"body": "Thanks!"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["body"] == "Thanks!"
        assert data["comment_id"] == COMMENT_ID

    def test_reply_no_auth(self, client: Any) -> None:
        resp = client.post(
            f"/api/v1/skills/{SLUG}/comments/{COMMENT_ID}/replies",
            json={"body": "Thanks!"},
        )
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.create_reply")
    def test_reply_comment_not_found(self, mock_reply: Any, client: Any) -> None:
        mock_reply.side_effect = ValueError("Comment not found")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/comments/{COMMENT_ID}/replies",
            json={"body": "Hi"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


# ── 16. Vote comment: POST /{slug}/comments/{id}/vote ────────────────────


class TestPostCommentVote:
    """POST /api/v1/skills/{slug}/comments/{comment_id}/vote"""

    @patch("skillhub_flask.blueprints.social.vote_on_comment")
    def test_vote_comment_success(self, mock_vote: Any, client: Any) -> None:
        mock_vote.return_value = None
        resp = client.post(
            f"/api/v1/skills/{SLUG}/comments/{COMMENT_ID}/vote",
            headers=_auth_headers(),
        )
        assert resp.status_code == 204

    def test_vote_comment_no_auth(self, client: Any) -> None:
        resp = client.post(f"/api/v1/skills/{SLUG}/comments/{COMMENT_ID}/vote")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.vote_on_comment")
    def test_vote_comment_not_found(self, mock_vote: Any, client: Any) -> None:
        mock_vote.side_effect = ValueError("Comment not found")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/comments/{COMMENT_ID}/vote",
            headers=_auth_headers(),
        )
        assert resp.status_code == 404
