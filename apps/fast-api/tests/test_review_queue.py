"""Tests for Review Queue — service and router."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from skillhub.services.review_queue import (
    REVIEWABLE_STATUSES,
    claim_submission,
    decide_submission,
    get_review_queue,
)
from tests.conftest import _make_settings, make_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"
SUBMITTER_USER_ID = "00000000-0000-0000-0000-000000000002"
REGULAR_USER_ID = "00000000-0000-0000-0000-000000000003"


def _admin_token() -> str:
    return make_token(
        {
            "user_id": ADMIN_USER_ID,
            "sub": "admin-user",
            "division": "platform",
            "is_platform_team": True,
        }
    )


def _regular_token() -> str:
    return make_token(
        {
            "user_id": REGULAR_USER_ID,
            "sub": "regular-user",
            "division": "engineering",
            "is_platform_team": False,
        }
    )


def _mock_submission(
    *,
    status: str = "gate2_passed",
    submitted_by: uuid.UUID | None = None,
) -> MagicMock:
    sub = MagicMock()
    sub.id = uuid.uuid4()
    sub.display_id = "SKL-ABC123"
    sub.name = "Test Skill"
    sub.short_desc = "A test skill"
    sub.category = "engineering"
    sub.content = "Some skill content here"
    sub.declared_divisions = ["engineering"]
    sub.division_justification = "needed"
    sub.status = status
    sub.submitted_by = submitted_by or uuid.UUID(SUBMITTER_USER_ID)
    sub.created_at = MagicMock()
    sub.gate3_reviewer_id = None
    sub.gate3_reviewed_at = None
    sub.gate3_notes = None
    return sub


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.all.return_value = []
    return db


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestGetReviewQueue:
    def test_empty_queue(self) -> None:
        db = _mock_db()
        q = db.query.return_value.filter.return_value
        q.count.return_value = 0
        q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )

        items, total = get_review_queue(db, page=1, per_page=20)
        assert items == []
        assert total == 0


class TestClaimSubmission:
    def test_not_found_raises(self) -> None:
        db = _mock_db()
        with pytest.raises(ValueError, match="Submission not found"):
            claim_submission(
                db,
                submission_id=uuid.uuid4(),
                reviewer_id=uuid.UUID(ADMIN_USER_ID),
            )

    def test_non_reviewable_status_raises(self) -> None:
        db = _mock_db()
        sub = _mock_submission(status="submitted")
        db.query.return_value.filter.return_value.first.return_value = sub

        with pytest.raises(ValueError, match="not reviewable"):
            claim_submission(
                db,
                submission_id=sub.id,
                reviewer_id=uuid.UUID(ADMIN_USER_ID),
            )


class TestDecideSubmission:
    def test_self_approval_blocked(self) -> None:
        db = _mock_db()
        submitter_id = uuid.UUID(SUBMITTER_USER_ID)
        sub = _mock_submission(submitted_by=submitter_id)
        db.query.return_value.filter.return_value.first.return_value = sub

        with pytest.raises(PermissionError, match="Cannot review your own"):
            decide_submission(
                db,
                submission_id=sub.id,
                reviewer_id=submitter_id,
                decision="approve",
            )

    def test_approve_changes_status(self) -> None:
        db = _mock_db()
        sub = _mock_submission()
        db.query.return_value.filter.return_value.first.return_value = sub

        result = decide_submission(
            db,
            submission_id=sub.id,
            reviewer_id=uuid.UUID(ADMIN_USER_ID),
            decision="approve",
            notes="Looks good",
        )

        assert sub.status == "approved"
        assert result["decision"] == "approve"
        assert result["reviewer_id"] == ADMIN_USER_ID

    def test_reject_changes_status(self) -> None:
        db = _mock_db()
        sub = _mock_submission()
        db.query.return_value.filter.return_value.first.return_value = sub

        result = decide_submission(
            db,
            submission_id=sub.id,
            reviewer_id=uuid.UUID(ADMIN_USER_ID),
            decision="reject",
            notes="Does not meet standards",
        )

        assert sub.status == "rejected"
        assert result["decision"] == "reject"

    def test_request_changes_status(self) -> None:
        db = _mock_db()
        sub = _mock_submission()
        db.query.return_value.filter.return_value.first.return_value = sub

        decide_submission(
            db,
            submission_id=sub.id,
            reviewer_id=uuid.UUID(ADMIN_USER_ID),
            decision="request_changes",
            notes="Needs more docs",
        )

        assert sub.status == "gate3_changes_requested"

    def test_creates_gate_result(self) -> None:
        db = _mock_db()
        sub = _mock_submission()
        db.query.return_value.filter.return_value.first.return_value = sub

        decide_submission(
            db,
            submission_id=sub.id,
            reviewer_id=uuid.UUID(ADMIN_USER_ID),
            decision="approve",
        )

        # db.add is called twice: once for gate result, once for audit log
        add_calls = db.add.call_args_list
        assert len(add_calls) >= 2
        gate_result_obj = add_calls[0][0][0]
        assert gate_result_obj.gate == 3
        assert gate_result_obj.result == "passed"

    def test_creates_audit_log(self) -> None:
        db = _mock_db()
        sub = _mock_submission()
        db.query.return_value.filter.return_value.first.return_value = sub

        decide_submission(
            db,
            submission_id=sub.id,
            reviewer_id=uuid.UUID(ADMIN_USER_ID),
            decision="approve",
            notes="LGTM",
        )

        add_calls = db.add.call_args_list
        assert len(add_calls) >= 2
        audit_obj = add_calls[1][0][0]
        assert audit_obj.event_type == "submission.approved"
        assert audit_obj.target_type == "submission"

    def test_invalid_decision_raises(self) -> None:
        db = _mock_db()
        sub = _mock_submission()
        db.query.return_value.filter.return_value.first.return_value = sub

        with pytest.raises(ValueError, match="Invalid decision"):
            decide_submission(
                db,
                submission_id=sub.id,
                reviewer_id=uuid.UUID(ADMIN_USER_ID),
                decision="maybe",
            )


# ---------------------------------------------------------------------------
# Router tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_db_session() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def app_with_db(mock_db_session: MagicMock) -> Any:
    settings = _make_settings()
    application = create_app(settings=settings)
    application.dependency_overrides[get_db] = lambda: mock_db_session
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def api_client(app_with_db: Any) -> TestClient:
    return TestClient(app_with_db)


class TestQueueRouter:
    def test_requires_auth(self, api_client: TestClient) -> None:
        response = api_client.get("/api/v1/admin/review-queue")
        assert response.status_code == 401

    def test_requires_platform_team(self, api_client: TestClient) -> None:
        headers = {"Authorization": f"Bearer {_regular_token()}"}
        response = api_client.get("/api/v1/admin/review-queue", headers=headers)
        assert response.status_code == 403

    @patch("skillhub.routers.review_queue.get_review_queue")
    def test_returns_200(
        self,
        mock_get: MagicMock,
        api_client: TestClient,
    ) -> None:
        mock_get.return_value = ([], 0)
        headers = {"Authorization": f"Bearer {_admin_token()}"}
        response = api_client.get("/api/v1/admin/review-queue", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["has_more"] is False

    @patch("skillhub.routers.review_queue.claim_submission")
    def test_claim_not_found(
        self,
        mock_claim: MagicMock,
        api_client: TestClient,
    ) -> None:
        mock_claim.side_effect = ValueError("Submission not found")
        headers = {"Authorization": f"Bearer {_admin_token()}"}
        fake_id = str(uuid.uuid4())
        response = api_client.post(
            f"/api/v1/admin/review-queue/{fake_id}/claim",
            headers=headers,
        )
        assert response.status_code == 404

    @patch("skillhub.routers.review_queue.decide_submission")
    def test_decision_self_approval_403(
        self,
        mock_decide: MagicMock,
        api_client: TestClient,
    ) -> None:
        mock_decide.side_effect = PermissionError("Cannot review your own submission")
        headers = {"Authorization": f"Bearer {_admin_token()}"}
        fake_id = str(uuid.uuid4())
        response = api_client.post(
            f"/api/v1/admin/review-queue/{fake_id}/decision",
            headers=headers,
            json={"decision": "approve"},
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Regression tests — enum usage and queue filtering
# ---------------------------------------------------------------------------


class TestReviewableStatusesRegression:
    """Regression: REVIEWABLE_STATUSES must use SubmissionStatus enum members,
    not raw strings.  The original bug used string literals like
    ``{"gate2_passed", "gate2_flagged"}`` which broke SQLAlchemy enum filtering.
    """

    def test_reviewable_statuses_use_enum_members(self) -> None:
        """REVIEWABLE_STATUSES must contain SubmissionStatus enum values."""
        from skillhub_db.models.submission import SubmissionStatus

        for status in REVIEWABLE_STATUSES:
            assert isinstance(status, SubmissionStatus), (
                f"REVIEWABLE_STATUSES contains {type(status).__name__} '{status}' "
                f"instead of SubmissionStatus enum member"
            )

    def test_reviewable_statuses_contains_gate2_passed(self) -> None:
        from skillhub_db.models.submission import SubmissionStatus

        assert SubmissionStatus.GATE2_PASSED in REVIEWABLE_STATUSES

    def test_reviewable_statuses_contains_gate2_flagged(self) -> None:
        from skillhub_db.models.submission import SubmissionStatus

        assert SubmissionStatus.GATE2_FLAGGED in REVIEWABLE_STATUSES

    def test_reviewable_statuses_excludes_non_review_statuses(self) -> None:
        from skillhub_db.models.submission import SubmissionStatus

        non_reviewable = {
            SubmissionStatus.SUBMITTED,
            SubmissionStatus.GATE1_PASSED,
            SubmissionStatus.GATE1_FAILED,
            SubmissionStatus.GATE2_FAILED,
            SubmissionStatus.GATE3_CHANGES_REQUESTED,
            SubmissionStatus.APPROVED,
            SubmissionStatus.REJECTED,
            SubmissionStatus.PUBLISHED,
        }
        for status in non_reviewable:
            assert status not in REVIEWABLE_STATUSES, (
                f"Non-reviewable status {status} should not be in REVIEWABLE_STATUSES"
            )


class TestGetReviewQueueFiltering:
    """Regression: get_review_queue must find gate2_passed / gate2_flagged
    submissions and exclude all other statuses."""

    def test_queue_returns_gate2_passed_submission(self) -> None:
        """Submissions with gate2_passed status must appear in the queue."""
        from skillhub_db.models.submission import SubmissionStatus

        db = _mock_db()
        sub = _mock_submission(status=SubmissionStatus.GATE2_PASSED)
        q = db.query.return_value.filter.return_value
        q.count.return_value = 1
        q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sub]

        # Mock user lookup
        db.query.return_value.filter.return_value.all.return_value = []

        items, total = get_review_queue(db, page=1, per_page=20)
        assert total == 1
        assert len(items) == 1
        assert items[0]["skill_name"] == "Test Skill"

    def test_queue_returns_gate2_flagged_submission(self) -> None:
        """Submissions with gate2_flagged status must appear in the queue."""
        from skillhub_db.models.submission import SubmissionStatus

        db = _mock_db()
        sub = _mock_submission(status=SubmissionStatus.GATE2_FLAGGED)
        q = db.query.return_value.filter.return_value
        q.count.return_value = 1
        q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sub]

        db.query.return_value.filter.return_value.all.return_value = []

        items, total = get_review_queue(db, page=1, per_page=20)
        assert total == 1
        assert items[0]["skill_name"] == "Test Skill"

    def test_claim_rejects_non_reviewable_status(self) -> None:
        """claim_submission must reject submissions not in REVIEWABLE_STATUSES."""
        from skillhub_db.models.submission import SubmissionStatus

        for status in [SubmissionStatus.SUBMITTED, SubmissionStatus.APPROVED, SubmissionStatus.REJECTED]:
            db = _mock_db()
            sub = _mock_submission(status=status)
            db.query.return_value.filter.return_value.first.return_value = sub

            with pytest.raises(ValueError, match="not reviewable"):
                claim_submission(
                    db,
                    submission_id=sub.id,
                    reviewer_id=uuid.UUID(ADMIN_USER_ID),
                )
