"""Coverage tests for skillhub.services.review_queue — HITL approval workflow."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest

from skillhub_db.models.submission import SubmissionStatus
from skillhub.services.review_queue import (
    claim_submission,
    decide_submission,
    get_review_queue,
)


def _mock_submission(
    status: Any = SubmissionStatus.GATE2_PASSED,
    submitted_by: uuid.UUID | None = None,
) -> MagicMock:
    sub = MagicMock()
    sub.id = uuid.uuid4()
    sub.display_id = "SKL-TEST01"
    sub.name = "Test Skill"
    sub.short_desc = "A test"
    sub.category = "productivity"
    sub.status = status
    sub.submitted_by = submitted_by or uuid.uuid4()
    sub.content = "skill content here for preview"
    sub.declared_divisions = ["engineering"]
    sub.gate3_reviewer_id = None
    sub.gate3_reviewed_at = None
    sub.gate3_notes = None
    sub.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return sub


class TestGetReviewQueue:
    def test_returns_paginated_items(self) -> None:
        sub = _mock_submission()
        sub.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

        gate1 = MagicMock()
        gate1.gate = 1
        gate1.result = "passed"

        gate2 = MagicMock()
        gate2.gate = 2
        gate2.result = "passed"
        gate2.findings = {"score": 0.85, "summary": "Looks good"}

        user_row = MagicMock()
        user_row.id = sub.submitted_by
        user_row.name = "Alice"

        db = MagicMock()

        q_submissions = MagicMock()
        q_submissions.filter.return_value = q_submissions
        q_submissions.count.return_value = 1
        q_submissions.order_by.return_value = q_submissions
        q_submissions.offset.return_value = q_submissions
        q_submissions.limit.return_value = q_submissions
        q_submissions.all.return_value = [sub]

        q_users = MagicMock()
        q_users.filter.return_value = q_users
        q_users.all.return_value = [user_row]

        q_gates = MagicMock()
        q_gates.filter.return_value = q_gates
        q_gates.all.return_value = [gate1, gate2]

        db.query.side_effect = [q_submissions, q_users, q_gates]

        items, total = get_review_queue(db, page=1, per_page=20)

        assert total == 1
        assert len(items) == 1
        item = items[0]
        assert item["submission_id"] == str(sub.id)
        assert item["skill_name"] == "Test Skill"
        assert item["gate1_passed"] is True
        assert item["gate2_score"] == 0.85

    def test_empty_queue(self) -> None:
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 0
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        items, total = get_review_queue(db)
        assert total == 0
        assert items == []

    def test_no_gate_results(self) -> None:
        sub = _mock_submission()
        sub.created_at = datetime(2026, 3, 1, tzinfo=timezone.utc)

        db = MagicMock()

        q_submissions = MagicMock()
        q_submissions.filter.return_value = q_submissions
        q_submissions.count.return_value = 1
        q_submissions.order_by.return_value = q_submissions
        q_submissions.offset.return_value = q_submissions
        q_submissions.limit.return_value = q_submissions
        q_submissions.all.return_value = [sub]

        q_users = MagicMock()
        q_users.filter.return_value = q_users
        q_users.all.return_value = []

        q_gates = MagicMock()
        q_gates.filter.return_value = q_gates
        q_gates.all.return_value = []

        db.query.side_effect = [q_submissions, q_users, q_gates]

        items, total = get_review_queue(db)
        assert items[0]["gate1_passed"] is False
        assert items[0]["gate2_score"] is None


class TestClaimSubmission:
    def test_successful_claim(self) -> None:
        sub = _mock_submission(status=SubmissionStatus.GATE2_PASSED)
        reviewer_id = uuid.uuid4()

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = sub

        result = claim_submission(db, submission_id=sub.id, reviewer_id=reviewer_id)

        assert result["submission_id"] == str(sub.id)
        assert result["reviewer_id"] == str(reviewer_id)
        assert sub.gate3_reviewer_id == reviewer_id
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_claim_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Submission not found"):
            claim_submission(db, submission_id=uuid.uuid4(), reviewer_id=uuid.uuid4())

    def test_claim_wrong_status_raises(self) -> None:
        sub = _mock_submission(status=SubmissionStatus.APPROVED)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = sub

        with pytest.raises(ValueError, match="not reviewable"):
            claim_submission(db, submission_id=sub.id, reviewer_id=uuid.uuid4())


class TestDecideSubmission:
    def test_approve_submission(self) -> None:
        submitter_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()
        sub = _mock_submission(status=SubmissionStatus.GATE2_PASSED, submitted_by=submitter_id)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = sub

        result = decide_submission(
            db,
            submission_id=sub.id,
            reviewer_id=reviewer_id,
            decision="approve",
            notes="Looks great",
        )

        assert result["decision"] == "approve"
        assert sub.status == "approved"
        db.add.assert_called()
        db.commit.assert_called_once()

    def test_reject_submission(self) -> None:
        submitter_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()
        sub = _mock_submission(status=SubmissionStatus.GATE2_FLAGGED, submitted_by=submitter_id)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = sub

        result = decide_submission(
            db,
            submission_id=sub.id,
            reviewer_id=reviewer_id,
            decision="reject",
        )

        assert result["decision"] == "reject"
        assert sub.status == "rejected"

    def test_request_changes(self) -> None:
        submitter_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()
        sub = _mock_submission(status=SubmissionStatus.GATE2_PASSED, submitted_by=submitter_id)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = sub

        result = decide_submission(
            db,
            submission_id=sub.id,
            reviewer_id=reviewer_id,
            decision="request_changes",
            notes="Please fix section 2",
        )

        assert sub.status == "gate3_changes_requested"

    def test_self_review_raises(self) -> None:
        user_id = uuid.uuid4()
        sub = _mock_submission(status=SubmissionStatus.GATE2_PASSED, submitted_by=user_id)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = sub

        with pytest.raises(PermissionError, match="Cannot review your own"):
            decide_submission(db, submission_id=sub.id, reviewer_id=user_id, decision="approve")

    def test_invalid_decision_raises(self) -> None:
        submitter_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()
        sub = _mock_submission(status=SubmissionStatus.GATE2_PASSED, submitted_by=submitter_id)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = sub

        with pytest.raises(ValueError, match="Invalid decision"):
            decide_submission(db, submission_id=sub.id, reviewer_id=reviewer_id, decision="maybe")

    def test_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Submission not found"):
            decide_submission(
                db,
                submission_id=uuid.uuid4(),
                reviewer_id=uuid.uuid4(),
                decision="approve",
            )

    def test_wrong_status_raises(self) -> None:
        submitter_id = uuid.uuid4()
        sub = _mock_submission(status=SubmissionStatus.APPROVED, submitted_by=submitter_id)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = sub

        with pytest.raises(ValueError, match="not reviewable"):
            decide_submission(
                db,
                submission_id=sub.id,
                reviewer_id=uuid.uuid4(),
                decision="approve",
            )
