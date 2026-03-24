"""Tests for HITL revision tracking Flask endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import make_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_token(user_id: str | None = None, **extra: Any) -> str:
    payload: dict[str, Any] = {
        "sub": "test-user",
        "user_id": user_id or str(uuid.uuid4()),
        "division": "engineering",
    }
    payload.update(extra)
    return make_token(payload=payload)


def _platform_token(**extra: Any) -> str:
    payload: dict[str, Any] = {
        "sub": "admin-user",
        "user_id": str(uuid.uuid4()),
        "division": "platform",
        "is_platform_team": True,
    }
    payload.update(extra)
    return make_token(payload=payload)


_DISPLAY_ID = "SKL-ABC123"
_USER_ID = str(uuid.uuid4())
_NOW = datetime.now(timezone.utc).isoformat()

_RESUBMIT_RESULT = {
    "id": uuid.uuid4(),
    "display_id": _DISPLAY_ID,
    "name": "Updated Skill",
    "short_desc": "Updated desc",
    "status": "submitted",
    "revision_number": 2,
    "content_hash": "abcdef1234567890",
}

_AUDIT_ENTRIES = [
    {
        "id": uuid.uuid4(),
        "from_status": "submitted",
        "to_status": "changes_requested",
        "actor_id": uuid.uuid4(),
        "notes": "Please fix formatting",
        "created_at": _NOW,
    },
    {
        "id": uuid.uuid4(),
        "from_status": "changes_requested",
        "to_status": "submitted",
        "actor_id": uuid.uuid4(),
        "notes": "Resubmitted",
        "created_at": _NOW,
    },
]


# ---------------------------------------------------------------------------
# POST /api/v1/submissions/<display_id>/resubmit
# ---------------------------------------------------------------------------


class TestResubmitEndpoint:
    """POST /api/v1/submissions/<display_id>/resubmit."""

    @patch("skillhub_flask.blueprints.submissions.resubmit_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_resubmit_200(self, mock_get_db: MagicMock, mock_resubmit: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_resubmit.return_value = _RESUBMIT_RESULT

        token = _user_token()
        resp = client.post(
            f"/api/v1/submissions/{_DISPLAY_ID}/resubmit",
            json={"content": "updated SKILL.md content"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "submitted"
        assert data["revision_number"] == 2
        mock_resubmit.assert_called_once()

    def test_resubmit_401(self, client: Any) -> None:
        resp = client.post(
            f"/api/v1/submissions/{_DISPLAY_ID}/resubmit",
            json={"content": "new content"},
        )
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.submissions.resubmit_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_resubmit_403(self, mock_get_db: MagicMock, mock_resubmit: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_resubmit.side_effect = PermissionError("Only the original submitter can resubmit")

        token = _user_token()
        resp = client.post(
            f"/api/v1/submissions/{_DISPLAY_ID}/resubmit",
            json={"content": "new content"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert "original submitter" in data["detail"]

    @patch("skillhub_flask.blueprints.submissions.resubmit_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_resubmit_400_wrong_status(self, mock_get_db: MagicMock, mock_resubmit: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_resubmit.side_effect = ValueError("Submission is not in a resubmittable state: approved")

        token = _user_token()
        resp = client.post(
            f"/api/v1/submissions/{_DISPLAY_ID}/resubmit",
            json={"content": "new content"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 400

    @patch("skillhub_flask.blueprints.submissions.resubmit_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_resubmit_404_not_found(self, mock_get_db: MagicMock, mock_resubmit: MagicMock, client: Any) -> None:
        mock_get_db.return_value = MagicMock()
        mock_resubmit.side_effect = ValueError("Submission 'SKL-NOPE' not found")

        token = _user_token()
        resp = client.post(
            "/api/v1/submissions/SKL-NOPE/resubmit",
            json={"content": "new content"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/submissions/<display_id>/audit-log
# ---------------------------------------------------------------------------


class TestAuditLogEndpoint:
    """GET /api/v1/submissions/<display_id>/audit-log."""

    @patch("skillhub_flask.blueprints.submissions.get_audit_trail")
    @patch("skillhub_flask.blueprints.submissions.get_submission_by_display_id")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_audit_log_200(
        self,
        mock_get_db: MagicMock,
        mock_lookup: MagicMock,
        mock_trail: MagicMock,
        client: Any,
    ) -> None:
        mock_get_db.return_value = MagicMock()

        user_id = str(uuid.uuid4())
        sub = MagicMock()
        sub.submitted_by = uuid.UUID(user_id)
        mock_lookup.return_value = sub
        mock_trail.return_value = _AUDIT_ENTRIES

        token = _user_token(user_id=user_id)
        resp = client.get(
            f"/api/v1/submissions/{_DISPLAY_ID}/audit-log",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["entries"]) == 2

    @patch("skillhub_flask.blueprints.submissions.get_audit_trail")
    @patch("skillhub_flask.blueprints.submissions.get_submission_by_display_id")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_audit_log_200_admin(
        self,
        mock_get_db: MagicMock,
        mock_lookup: MagicMock,
        mock_trail: MagicMock,
        client: Any,
    ) -> None:
        """Platform team can see any submission's audit log."""
        mock_get_db.return_value = MagicMock()

        sub = MagicMock()
        sub.submitted_by = uuid.uuid4()  # Different user
        mock_lookup.return_value = sub
        mock_trail.return_value = _AUDIT_ENTRIES

        token = _platform_token()
        resp = client.get(
            f"/api/v1/submissions/{_DISPLAY_ID}/audit-log",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["entries"]) == 2

    def test_audit_log_401(self, client: Any) -> None:
        resp = client.get(f"/api/v1/submissions/{_DISPLAY_ID}/audit-log")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.submissions.get_submission_by_display_id")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_audit_log_403_not_owner(
        self,
        mock_get_db: MagicMock,
        mock_lookup: MagicMock,
        client: Any,
    ) -> None:
        """Non-owner, non-admin cannot view audit log."""
        mock_get_db.return_value = MagicMock()

        sub = MagicMock()
        sub.submitted_by = uuid.uuid4()  # Different user
        mock_lookup.return_value = sub

        token = _user_token()  # Regular user, not the owner
        resp = client.get(
            f"/api/v1/submissions/{_DISPLAY_ID}/audit-log",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403
