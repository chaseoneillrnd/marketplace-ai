"""Tests for the submissions blueprint endpoints."""

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

_SUBMISSION_ID = str(uuid.uuid4())
_USER_ID = str(uuid.uuid4())
_SKILL_ID = str(uuid.uuid4())
_NOW = datetime.now(timezone.utc).isoformat()

_GATE1_RESULT = {"gate": 1, "result": "pass", "findings": [], "score": 100}

_CREATE_RESULT = {
    "id": _SUBMISSION_ID,
    "display_id": "SUB-0001",
    "status": "gate1_passed",
    "gate1_result": _GATE1_RESULT,
}

_DETAIL_RESULT = {
    "id": _SUBMISSION_ID,
    "display_id": "SUB-0001",
    "name": "My Skill",
    "short_desc": "A skill",
    "category": "code-review",
    "content": "# SKILL.md",
    "declared_divisions": ["engineering"],
    "division_justification": "Useful for engineering",
    "status": "gate1_passed",
    "submitted_by": _USER_ID,
    "gate_results": [_GATE1_RESULT],
    "created_at": _NOW,
    "updated_at": _NOW,
}

_ADMIN_SUMMARY = {
    "id": _SUBMISSION_ID,
    "display_id": "SUB-0001",
    "name": "My Skill",
    "short_desc": "A skill",
    "category": "code-review",
    "status": "gate1_passed",
    "submitted_by": _USER_ID,
    "declared_divisions": ["engineering"],
    "created_at": _NOW,
}

_ACCESS_REQUEST_RESULT = {
    "id": str(uuid.uuid4()),
    "skill_id": _SKILL_ID,
    "requested_by": _USER_ID,
    "user_division": "engineering",
    "reason": "I need access",
    "status": "pending",
    "created_at": _NOW,
}


# ---------------------------------------------------------------------------
# POST /api/v1/submissions
# ---------------------------------------------------------------------------


class TestCreateSubmission:
    """POST /api/v1/submissions."""

    @patch("skillhub_flask.blueprints.submissions.create_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_success_returns_201(self, mock_get_db: MagicMock, mock_create: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        # Return gate1_failed so the background Gate 2 thread does NOT start
        result = {**_CREATE_RESULT, "status": "gate1_failed"}
        mock_create.return_value = result

        token = _user_token()
        resp = client.post(
            "/api/v1/submissions",
            json={
                "name": "My Skill",
                "short_desc": "A skill",
                "category": "code-review",
                "content": "# SKILL.md content here",
                "declared_divisions": ["engineering"],
                "division_justification": "Engineering uses this",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["display_id"] == "SUB-0001"
        mock_create.assert_called_once()

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.post("/api/v1/submissions", json={"name": "x"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/submissions/<id>
# ---------------------------------------------------------------------------


class TestGetSubmissionDetail:
    """GET /api/v1/submissions/<id>."""

    @patch("skillhub_flask.blueprints.submissions.get_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_success_as_owner(self, mock_get_db: MagicMock, mock_get: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_get.return_value = _DETAIL_RESULT

        token = _user_token(user_id=_USER_ID)
        resp = client.get(f"/api/v1/submissions/{_SUBMISSION_ID}", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["display_id"] == "SUB-0001"

    @patch("skillhub_flask.blueprints.submissions.get_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_permission_error_returns_403(self, mock_get_db: MagicMock, mock_get: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_get.side_effect = PermissionError("Not the owner")

        token = _user_token()
        resp = client.get(f"/api/v1/submissions/{_SUBMISSION_ID}", headers=_auth_headers(token))
        assert resp.status_code == 403

    @patch("skillhub_flask.blueprints.submissions.get_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_not_found_returns_404(self, mock_get_db: MagicMock, mock_get: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_get.return_value = None

        token = _user_token()
        resp = client.get(f"/api/v1/submissions/{_SUBMISSION_ID}", headers=_auth_headers(token))
        assert resp.status_code == 404

    def test_invalid_uuid_returns_400(self, client: Any) -> None:
        token = _user_token()
        resp = client.get("/api/v1/submissions/not-a-uuid", headers=_auth_headers(token))
        assert resp.status_code == 400

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.get(f"/api/v1/submissions/{_SUBMISSION_ID}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/admin/submissions/<id>/scan
# ---------------------------------------------------------------------------


class TestScanSubmission:
    """POST /api/v1/admin/submissions/<id>/scan — platform team only."""

    @patch("skillhub.services.submissions.run_gate2_scan")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_success_returns_200(self, mock_get_db: MagicMock, mock_scan: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_scan.return_value = {"gate": 2, "result": "pass"}

        token = _platform_token()
        resp = client.post(f"/api/v1/admin/submissions/{_SUBMISSION_ID}/scan", headers=_auth_headers(token))
        assert resp.status_code == 200

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.post(f"/api/v1/admin/submissions/{_SUBMISSION_ID}/scan")
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.post(f"/api/v1/admin/submissions/{_SUBMISSION_ID}/scan", headers=_auth_headers(token))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/admin/submissions
# ---------------------------------------------------------------------------


class TestListSubmissionsAdmin:
    """GET /api/v1/admin/submissions — platform team only."""

    @patch("skillhub_flask.blueprints.submissions.list_admin_submissions")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_success_returns_200(self, mock_get_db: MagicMock, mock_list: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_list.return_value = ([_ADMIN_SUMMARY], 1)

        token = _platform_token()
        resp = client.get("/api/v1/admin/submissions", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/submissions")
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.get("/api/v1/admin/submissions", headers=_auth_headers(token))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/admin/submissions/<id>/review
# ---------------------------------------------------------------------------


class TestReviewSubmission:
    """POST /api/v1/admin/submissions/<id>/review — platform team only."""

    @patch("skillhub_flask.blueprints.submissions.review_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_success_returns_200(self, mock_get_db: MagicMock, mock_review: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_review.return_value = {"status": "approved"}

        token = _platform_token()
        resp = client.post(
            f"/api/v1/admin/submissions/{_SUBMISSION_ID}/review",
            json={"decision": "approved", "notes": "Looks good"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.post(f"/api/v1/admin/submissions/{_SUBMISSION_ID}/review", json={"decision": "approved", "notes": "ok"})
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.post(
            f"/api/v1/admin/submissions/{_SUBMISSION_ID}/review",
            json={"decision": "approved", "notes": "ok"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/skills/<slug>/access-request
# ---------------------------------------------------------------------------


class TestCreateAccessRequest:
    """POST /api/v1/skills/<slug>/access-request — any authed user."""

    @patch("skillhub_flask.blueprints.submissions.create_access_request")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_success_returns_201(self, mock_get_db: MagicMock, mock_create: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_create.return_value = _ACCESS_REQUEST_RESULT

        token = _user_token()
        resp = client.post(
            "/api/v1/skills/my-skill/access-request",
            json={"reason": "I need access"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "pending"

    @patch("skillhub_flask.blueprints.submissions.create_access_request")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_not_found_returns_404(self, mock_get_db: MagicMock, mock_create: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_create.side_effect = ValueError("Skill not found")

        token = _user_token()
        resp = client.post(
            "/api/v1/skills/no-such-skill/access-request",
            json={"reason": "I need access"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.post("/api/v1/skills/my-skill/access-request", json={"reason": "x"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/admin/access-requests
# ---------------------------------------------------------------------------


class TestListAccessRequests:
    """GET /api/v1/admin/access-requests — platform team only."""

    @patch("skillhub_flask.blueprints.submissions.list_access_requests")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_success_returns_200(self, mock_get_db: MagicMock, mock_list: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_list.return_value = ([_ACCESS_REQUEST_RESULT], 1)

        token = _platform_token()
        resp = client.get("/api/v1/admin/access-requests", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/access-requests")
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        token = _user_token()
        resp = client.get("/api/v1/admin/access-requests", headers=_auth_headers(token))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/admin/access-requests/<id>/review
# ---------------------------------------------------------------------------


class TestReviewAccessRequest:
    """POST /api/v1/admin/access-requests/<id>/review — platform team only."""

    @patch("skillhub_flask.blueprints.submissions.review_access_request")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_success_returns_200(self, mock_get_db: MagicMock, mock_review: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_review.return_value = {"status": "approved"}

        req_id = str(uuid.uuid4())
        token = _platform_token()
        resp = client.post(
            f"/api/v1/admin/access-requests/{req_id}/review",
            json={"decision": "approved"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200

    def test_no_auth_returns_401(self, client: Any) -> None:
        req_id = str(uuid.uuid4())
        resp = client.post(f"/api/v1/admin/access-requests/{req_id}/review", json={"decision": "approved"})
        assert resp.status_code == 401

    def test_non_platform_returns_403(self, client: Any) -> None:
        req_id = str(uuid.uuid4())
        token = _user_token()
        resp = client.post(
            f"/api/v1/admin/access-requests/{req_id}/review",
            json={"decision": "approved"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403
