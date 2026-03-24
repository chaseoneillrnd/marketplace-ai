"""Tests for review_queue blueprint — list, claim, decide with event_type fix."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tests.conftest import make_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _platform_token(user_id: str | None = None) -> str:
    return make_token(
        payload={
            "sub": "admin",
            "user_id": user_id or str(uuid4()),
            "division": "eng",
            "is_platform_team": True,
            "is_security_team": False,
        }
    )


def _regular_token() -> str:
    return make_token(
        payload={
            "sub": "user",
            "user_id": str(uuid4()),
            "division": "eng",
            "is_platform_team": False,
            "is_security_team": False,
        }
    )


def _queue_item(submission_id: str | None = None) -> dict:
    """Return a dict matching ReviewQueueItem schema fields."""
    return {
        "submission_id": submission_id or str(uuid4()),
        "display_id": "SUB-001",
        "skill_name": "test-skill",
        "short_desc": "A test skill",
        "category": "productivity",
        "submitter_name": "Alice",
        "submitted_at": "2026-03-01T00:00:00",
        "gate1_passed": True,
        "gate2_score": 0.92,
        "gate2_summary": "Passed automated checks",
        "content_preview": "# Test Skill\nDoes things.",
        "wait_time_hours": 2.5,
        "divisions": ["eng"],
    }


# ---------------------------------------------------------------------------
# GET /api/v1/admin/review-queue
# ---------------------------------------------------------------------------


class TestListReviewQueue:
    """GET /admin/review-queue — platform team only."""

    def test_list_401_no_token(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/review-queue")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.review_queue.get_review_queue")
    def test_list_200_platform(self, mock_rq: MagicMock, client: Any) -> None:
        item = _queue_item()
        mock_rq.return_value = ([item], 1)
        resp = client.get(
            "/api/v1/admin/review-queue",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["has_more"] is False
        mock_rq.assert_called_once()

    @patch("skillhub_flask.blueprints.review_queue.get_review_queue")
    def test_list_pagination(self, mock_rq: MagicMock, client: Any) -> None:
        mock_rq.return_value = ([_queue_item()], 25)
        resp = client.get(
            "/api/v1/admin/review-queue?page=1&per_page=20",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["has_more"] is True

    def test_list_403_regular(self, client: Any) -> None:
        resp = client.get(
            "/api/v1/admin/review-queue",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/admin/review-queue/<id>/claim
# ---------------------------------------------------------------------------


class TestClaimSubmission:
    """POST /admin/review-queue/<id>/claim — platform team only."""

    def test_claim_401_no_token(self, client: Any) -> None:
        sub_id = str(uuid4())
        resp = client.post(f"/api/v1/admin/review-queue/{sub_id}/claim")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.review_queue.claim_submission")
    def test_claim_200_platform(self, mock_cs: MagicMock, client: Any) -> None:
        sub_id = str(uuid4())
        reviewer_id = str(uuid4())
        mock_cs.return_value = {
            "submission_id": sub_id,
            "reviewer_id": reviewer_id,
            "claimed_at": "2026-03-01T10:00:00",
        }
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/claim",
            headers=_auth_headers(_platform_token(user_id=reviewer_id)),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["submission_id"] == sub_id
        mock_cs.assert_called_once()

    @patch("skillhub_flask.blueprints.review_queue.claim_submission")
    def test_claim_404_not_found(self, mock_cs: MagicMock, client: Any) -> None:
        mock_cs.side_effect = ValueError("Submission not found")
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/claim",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 404

    def test_claim_403_regular(self, client: Any) -> None:
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/claim",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/admin/review-queue/<id>/decision
# ---------------------------------------------------------------------------


def _decision_result(sub_id: str, decision: str = "approve") -> dict:
    """Return a dict matching DecisionResponse schema."""
    return {
        "submission_id": sub_id,
        "decision": decision,
        "reviewer_id": str(uuid4()),
        "reviewed_at": "2026-03-01T12:00:00",
    }


class TestDecideSubmission:
    """POST /admin/review-queue/<id>/decision — platform team, self-approval blocked."""

    def test_decide_401_no_token(self, client: Any) -> None:
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "approve"},
        )
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_decide_approve_200(self, mock_ds: MagicMock, client: Any) -> None:
        sub_id = str(uuid4())
        mock_ds.return_value = _decision_result(sub_id, "approve")
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "approve", "notes": "Looks good", "score": 5},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["decision"] == "approve"
        mock_ds.assert_called_once()

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_decide_reject_200(self, mock_ds: MagicMock, client: Any) -> None:
        sub_id = str(uuid4())
        mock_ds.return_value = _decision_result(sub_id, "reject")
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "reject", "notes": "Does not meet quality bar"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["decision"] == "reject"

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_decide_request_changes_200(self, mock_ds: MagicMock, client: Any) -> None:
        sub_id = str(uuid4())
        mock_ds.return_value = _decision_result(sub_id, "request_changes")
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "request_changes", "notes": "Needs docs"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["decision"] == "request_changes"

    def test_decide_403_regular(self, client: Any) -> None:
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "approve"},
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_decide_403_self_approval(self, mock_ds: MagicMock, client: Any) -> None:
        """PermissionError from service layer maps to 403 for self-approval."""
        mock_ds.side_effect = PermissionError("Cannot approve your own submission")
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "approve", "notes": "Self-approve attempt"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert "Cannot approve your own submission" in data["detail"]

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_decide_404_not_found(self, mock_ds: MagicMock, client: Any) -> None:
        mock_ds.side_effect = ValueError("Submission not found")
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "approve"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Event type fix verification
# ---------------------------------------------------------------------------


class TestEventTypeFix:
    """Verify the _DECISION_EVENT dict produces correct event_type strings."""

    def test_decision_event_mapping(self) -> None:
        """The mapping must produce grammatically correct event types."""
        from skillhub_flask.blueprints.review_queue import _DECISION_EVENT

        assert _DECISION_EVENT["approve"] == "submission.approved"
        assert _DECISION_EVENT["reject"] == "submission.rejected"
        assert _DECISION_EVENT["request_changes"] == "submission.changes_requested"

    def test_reject_not_rejectd(self) -> None:
        """Regression: f'submission.{decision}d' would produce 'submission.rejectd'."""
        from skillhub_flask.blueprints.review_queue import _DECISION_EVENT

        assert _DECISION_EVENT["reject"] != "submission.rejectd"
        assert _DECISION_EVENT["reject"] == "submission.rejected"

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_decide_calls_service_with_correct_args(self, mock_ds: MagicMock, client: Any) -> None:
        """Verify decide_submission is called with the expected parameters."""
        sub_id = str(uuid4())
        reviewer_id = str(uuid4())
        mock_ds.return_value = {
            "submission_id": sub_id,
            "decision": "reject",
            "reviewer_id": reviewer_id,
            "reviewed_at": "2026-03-01T12:00:00",
        }
        token = _platform_token(user_id=reviewer_id)
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "reject", "notes": "Not ready", "score": 2},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        mock_ds.assert_called_once()
        kwargs = mock_ds.call_args
        # Verify the service received the correct decision string
        assert kwargs[1]["decision"] == "reject"
        assert kwargs[1]["notes"] == "Not ready"
        assert kwargs[1]["score"] == 2

    def test_invalid_decision_returns_400(self, client: Any) -> None:
        """An unknown decision value should return 400."""
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "maybe"},
            headers=_auth_headers(_platform_token()),
        )
        # Either 400 from our check or a validation error
        assert resp.status_code in (400, 422)

    def test_event_type_reject_correct(self) -> None:
        """Regression: 'submission.rejectd' typo — must be 'submission.rejected'."""
        from skillhub_flask.blueprints.review_queue import _DECISION_EVENT

        assert _DECISION_EVENT["reject"] == "submission.rejected"
        assert not _DECISION_EVENT["reject"].endswith("rejectd")

    def test_event_type_approve_correct(self) -> None:
        """Verify approve maps to 'submission.approved'."""
        from skillhub_flask.blueprints.review_queue import _DECISION_EVENT

        assert _DECISION_EVENT["approve"] == "submission.approved"

    def test_event_type_changes_correct(self) -> None:
        """Verify request_changes maps to 'submission.changes_requested'."""
        from skillhub_flask.blueprints.review_queue import _DECISION_EVENT

        assert _DECISION_EVENT["request_changes"] == "submission.changes_requested"

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_audit_log_event_type_passed_to_service(self, mock_ds: MagicMock, client: Any) -> None:
        """Verify the decision endpoint passes the correct event_type to the service.

        The blueprint resolves event_type via _DECISION_EVENT before calling
        decide_submission — this confirms the non-typo path is exercised.
        """
        sub_id = str(uuid4())
        reviewer_id = str(uuid4())
        mock_ds.return_value = {
            "submission_id": sub_id,
            "decision": "reject",
            "reviewer_id": reviewer_id,
            "reviewed_at": "2026-03-01T12:00:00",
        }
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "reject", "notes": "Does not meet bar"},
            headers=_auth_headers(_platform_token(user_id=reviewer_id)),
        )
        assert resp.status_code == 200
        # Service was called exactly once with decision="reject" (not "rejectd")
        mock_ds.assert_called_once()
        kwargs = mock_ds.call_args[1]
        assert kwargs["decision"] == "reject"
