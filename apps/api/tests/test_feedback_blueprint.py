"""Tests for the feedback blueprint endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import make_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_token(**extra: Any) -> str:
    payload = {"sub": "test-user", "user_id": str(uuid.uuid4()), "division": "engineering"}
    payload.update(extra)
    return make_token(payload=payload)


def _platform_token(**extra: Any) -> str:
    payload = {
        "sub": "admin-user",
        "user_id": str(uuid.uuid4()),
        "division": "platform",
        "is_platform_team": True,
    }
    payload.update(extra)
    return make_token(payload=payload)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FEEDBACK_ID = str(uuid.uuid4())
_USER_ID = str(uuid.uuid4())
_SKILL_ID = str(uuid.uuid4())
_NOW = datetime.now(timezone.utc).isoformat()

_FEEDBACK_RESULT = {
    "id": _FEEDBACK_ID,
    "user_id": _USER_ID,
    "skill_id": _SKILL_ID,
    "category": "feature_request",
    "body": "This is a feature request body that is long enough",
    "sentiment": "positive",
    "upvotes": 0,
    "status": "new",
    "allow_contact": True,
    "created_at": _NOW,
    "skill_name": None,
    "user_display_name": None,
}

_FEEDBACK_WITH_NAMES = {
    **_FEEDBACK_RESULT,
    "skill_name": "Cool Skill",
    "user_display_name": "Alice Smith",
}


# ---------------------------------------------------------------------------
# POST /api/v1/feedback
# ---------------------------------------------------------------------------


class TestSubmitFeedback:
    """POST /api/v1/feedback — any authenticated user."""

    @patch("skillhub_flask.blueprints.feedback.create_feedback")
    @patch("skillhub_flask.blueprints.feedback.get_db")
    def test_success_returns_201(self, mock_get_db: MagicMock, mock_create: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_create.return_value = _FEEDBACK_RESULT

        token = _user_token()
        resp = client.post(
            "/api/v1/feedback",
            json={
                "category": "feature_request",
                "body": "I would really like this feature to be added to the platform please",
                "allow_contact": True,
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["category"] == "feature_request"
        mock_create.assert_called_once()

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/feedback",
            json={"category": "feature_request", "body": "Some feedback text here"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/admin/feedback
# ---------------------------------------------------------------------------


class TestListFeedbackAdmin:
    """GET /api/v1/admin/feedback — platform team only.

    BUG #5: Verify skill_name and user_display_name are present in response.
    """

    @patch("skillhub_flask.blueprints.feedback.list_feedback")
    @patch("skillhub_flask.blueprints.feedback.get_db")
    def test_success_returns_200_with_display_names(
        self, mock_get_db: MagicMock, mock_list: MagicMock, client: Any
    ) -> None:
        mock_get_db.return_value = MagicMock()
        mock_list.return_value = ([_FEEDBACK_WITH_NAMES], 1)

        token = _platform_token()
        resp = client.get("/api/v1/admin/feedback", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        item = data["items"][0]
        # BUG #5 fix verification: display names are passed through
        assert item["skill_name"] == "Cool Skill"
        assert item["user_display_name"] == "Alice Smith"

    @patch("skillhub_flask.blueprints.feedback.list_feedback")
    @patch("skillhub_flask.blueprints.feedback.get_db")
    def test_pagination_params_forwarded(
        self, mock_get_db: MagicMock, mock_list: MagicMock, client: Any
    ) -> None:
        mock_get_db.return_value = MagicMock()
        mock_list.return_value = ([], 0)

        token = _platform_token()
        resp = client.get(
            "/api/v1/admin/feedback?page=2&per_page=10&category=bug_report&sentiment=negative&status=triaged&sort=newest",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        mock_list.assert_called_once_with(
            mock_get_db.return_value,
            category="bug_report",
            sentiment="negative",
            status="triaged",
            sort="newest",
            page=2,
            per_page=10,
        )

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/feedback")
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.get("/api/v1/admin/feedback", headers=_auth_headers(token))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/feedback/<id>/upvote
# ---------------------------------------------------------------------------


class TestUpvoteFeedback:
    """POST /api/v1/feedback/<id>/upvote — any authenticated user."""

    @patch("skillhub_flask.blueprints.feedback.upvote_feedback")
    @patch("skillhub_flask.blueprints.feedback.get_db")
    def test_success_returns_200(self, mock_get_db: MagicMock, mock_upvote: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_upvote.return_value = {"upvotes": 1}

        token = _user_token()
        resp = client.post(f"/api/v1/feedback/{_FEEDBACK_ID}/upvote", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["upvotes"] == 1

    @patch("skillhub_flask.blueprints.feedback.upvote_feedback")
    @patch("skillhub_flask.blueprints.feedback.get_db")
    def test_not_found_returns_404(self, mock_get_db: MagicMock, mock_upvote: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_upvote.side_effect = ValueError("Feedback not found")

        token = _user_token()
        resp = client.post(f"/api/v1/feedback/{_FEEDBACK_ID}/upvote", headers=_auth_headers(token))
        assert resp.status_code == 404

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.post(f"/api/v1/feedback/{_FEEDBACK_ID}/upvote")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /api/v1/admin/feedback/<id>/status
# ---------------------------------------------------------------------------


class TestUpdateFeedbackStatus:
    """PATCH /api/v1/admin/feedback/<id>/status — platform team only."""

    @patch("skillhub_flask.blueprints.feedback.update_feedback_status")
    @patch("skillhub_flask.blueprints.feedback.get_db")
    def test_success_returns_200(self, mock_get_db: MagicMock, mock_update: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_update.return_value = {**_FEEDBACK_RESULT, "status": "triaged"}

        token = _platform_token()
        resp = client.patch(
            f"/api/v1/admin/feedback/{_FEEDBACK_ID}/status",
            json={"status": "triaged"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "triaged"

    @patch("skillhub_flask.blueprints.feedback.get_db")
    def test_missing_status_returns_422(self, mock_get_db: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()

        token = _platform_token()
        resp = client.patch(
            f"/api/v1/admin/feedback/{_FEEDBACK_ID}/status",
            json={},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 422

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.patch(f"/api/v1/admin/feedback/{_FEEDBACK_ID}/status", json={"status": "triaged"})
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.patch(
            f"/api/v1/admin/feedback/{_FEEDBACK_ID}/status",
            json={"status": "triaged"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403
