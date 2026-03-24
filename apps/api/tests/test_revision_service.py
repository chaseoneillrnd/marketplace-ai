"""Tests for HITL revision tracking service functions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from skillhub_db.models.submission import Submission, SubmissionStateTransition, SubmissionStatus
from skillhub.services.submissions import (
    compute_content_hash,
    get_audit_trail,
    get_submission_by_display_id,
    record_state_transition,
    resubmit_submission,
)


def _make_submission(
    *,
    display_id: str = "SKL-ABC123",
    status: SubmissionStatus = SubmissionStatus.CHANGES_REQUESTED,
    submitted_by: uuid.UUID | None = None,
    content: str = "original content",
    revision_number: int = 1,
    content_hash: str | None = None,
) -> MagicMock:
    """Create a mock Submission object."""
    sub = MagicMock(spec=Submission)
    sub.id = uuid.uuid4()
    sub.display_id = display_id
    sub.status = status
    sub.submitted_by = submitted_by or uuid.uuid4()
    sub.content = content
    sub.name = "Test Skill"
    sub.short_desc = "A test skill"
    sub.revision_number = revision_number
    sub.content_hash = content_hash
    return sub


class TestComputeContentHash:
    """Tests for compute_content_hash."""

    def test_content_hash_computed(self) -> None:
        """Hash changes when content changes."""
        hash1 = compute_content_hash("content A")
        hash2 = compute_content_hash("content B")
        assert hash1 != hash2
        assert len(hash1) == 16
        assert len(hash2) == 16

    def test_same_content_same_hash(self) -> None:
        """Same content produces the same hash."""
        h1 = compute_content_hash("hello world")
        h2 = compute_content_hash("hello world")
        assert h1 == h2


class TestRecordStateTransition:
    """Tests for record_state_transition."""

    def test_creates_transition_row(self) -> None:
        db = MagicMock()
        submission_id = uuid.uuid4()
        actor_id = uuid.uuid4()

        result = record_state_transition(
            db,
            submission_id=submission_id,
            from_status="changes_requested",
            to_status="submitted",
            actor_id=actor_id,
            notes="resubmitted",
        )

        db.add.assert_called_once()
        assert isinstance(result, SubmissionStateTransition)
        assert result.from_status == "changes_requested"
        assert result.to_status == "submitted"


class TestResubmitSubmission:
    """Tests for resubmit_submission."""

    @patch("skillhub.services.submissions.get_submission_by_display_id")
    def test_resubmit_success(self, mock_lookup: MagicMock) -> None:
        """Resubmit in CHANGES_REQUESTED updates status to SUBMITTED and bumps revision_number."""
        user_id = uuid.uuid4()
        sub = _make_submission(
            status=SubmissionStatus.CHANGES_REQUESTED,
            submitted_by=user_id,
            revision_number=1,
        )
        mock_lookup.return_value = sub

        db = MagicMock()
        result = resubmit_submission(
            db,
            display_id="SKL-ABC123",
            user_id=user_id,
            new_content="updated content",
            new_name="New Name",
        )

        assert sub.status == SubmissionStatus.SUBMITTED
        assert sub.revision_number == 2
        assert sub.content == "updated content"
        assert sub.name == "New Name"
        db.commit.assert_called_once()

    @patch("skillhub.services.submissions.get_submission_by_display_id")
    def test_resubmit_gate3_changes_requested(self, mock_lookup: MagicMock) -> None:
        """Resubmit also works for GATE3_CHANGES_REQUESTED status."""
        user_id = uuid.uuid4()
        sub = _make_submission(
            status=SubmissionStatus.GATE3_CHANGES_REQUESTED,
            submitted_by=user_id,
        )
        mock_lookup.return_value = sub

        db = MagicMock()
        result = resubmit_submission(
            db,
            display_id="SKL-ABC123",
            user_id=user_id,
            new_content="new content",
        )

        assert sub.status == SubmissionStatus.SUBMITTED

    @patch("skillhub.services.submissions.get_submission_by_display_id")
    def test_resubmit_wrong_status(self, mock_lookup: MagicMock) -> None:
        """Resubmit on APPROVED submission raises ValueError."""
        user_id = uuid.uuid4()
        sub = _make_submission(
            status=SubmissionStatus.APPROVED,
            submitted_by=user_id,
        )
        mock_lookup.return_value = sub

        db = MagicMock()
        with pytest.raises(ValueError, match="not in a resubmittable state"):
            resubmit_submission(db, "SKL-ABC123", user_id, "new content")

    @patch("skillhub.services.submissions.get_submission_by_display_id")
    def test_resubmit_not_owner(self, mock_lookup: MagicMock) -> None:
        """Resubmit by a different user raises PermissionError."""
        owner_id = uuid.uuid4()
        other_id = uuid.uuid4()
        sub = _make_submission(
            status=SubmissionStatus.CHANGES_REQUESTED,
            submitted_by=owner_id,
        )
        mock_lookup.return_value = sub

        db = MagicMock()
        with pytest.raises(PermissionError, match="Only the original submitter"):
            resubmit_submission(db, "SKL-ABC123", other_id, "new content")

    @patch("skillhub.services.submissions.get_submission_by_display_id")
    def test_resubmit_not_found(self, mock_lookup: MagicMock) -> None:
        """Resubmit with invalid display_id raises ValueError."""
        mock_lookup.return_value = None

        db = MagicMock()
        with pytest.raises(ValueError, match="not found"):
            resubmit_submission(db, "SKL-NOPE00", uuid.uuid4(), "content")


class TestGetAuditTrail:
    """Tests for get_audit_trail."""

    @patch("skillhub.services.submissions.get_submission_by_display_id")
    def test_audit_trail_returns_entries(self, mock_lookup: MagicMock) -> None:
        """Audit trail returns ordered transition entries."""
        sub = _make_submission()
        mock_lookup.return_value = sub

        t1_id = uuid.uuid4()
        t2_id = uuid.uuid4()
        actor = uuid.uuid4()
        ts1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        ts2 = datetime(2026, 1, 2, tzinfo=timezone.utc)

        transition1 = MagicMock()
        transition1.id = t1_id
        transition1.from_status = "submitted"
        transition1.to_status = "changes_requested"
        transition1.actor_id = actor
        transition1.notes = "Please fix"
        transition1.created_at = ts1

        transition2 = MagicMock()
        transition2.id = t2_id
        transition2.from_status = "changes_requested"
        transition2.to_status = "submitted"
        transition2.actor_id = actor
        transition2.notes = "Resubmitted"
        transition2.created_at = ts2

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            transition1,
            transition2,
        ]

        entries = get_audit_trail(db, "SKL-ABC123")

        assert len(entries) == 2
        assert entries[0]["from_status"] == "submitted"
        assert entries[1]["from_status"] == "changes_requested"
        assert entries[0]["created_at"] == ts1
        assert entries[1]["created_at"] == ts2
