"""Tests for feedback service — create, list, upvote, status updates."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from skillhub.services.feedback import (
    VALID_CATEGORIES,
    VALID_STATUSES,
    create_feedback,
    infer_sentiment,
    list_feedback,
    update_feedback_status,
    upvote_feedback,
)

USER_ID = str(uuid.uuid4())
FEEDBACK_ID = uuid.uuid4()


def _mock_feedback(**overrides: Any) -> MagicMock:
    """Create a mock SkillFeedback ORM object."""
    fb = MagicMock()
    fb.id = overrides.get("id", FEEDBACK_ID)
    fb.user_id = overrides.get("user_id", uuid.UUID(USER_ID))
    fb.skill_id = overrides.get("skill_id", None)
    fb.category = overrides.get("category", "feature_request")
    fb.body = overrides.get("body", "This is a great feature request for the platform")
    fb.sentiment = overrides.get("sentiment", "neutral")
    fb.upvotes = overrides.get("upvotes", 0)
    fb.status = overrides.get("status", "open")
    fb.allow_contact = overrides.get("allow_contact", False)
    fb.created_at = overrides.get("created_at", datetime.now(UTC))
    return fb


def _mock_db_session() -> MagicMock:
    """Create a mock DB session."""
    db = MagicMock()
    return db


class TestInferSentiment:
    """Tests for keyword-based sentiment inference."""

    def test_infer_sentiment_positive(self) -> None:
        assert infer_sentiment("I love this amazing tool!") == "positive"

    def test_infer_sentiment_negative(self) -> None:
        assert infer_sentiment("This is terrible and broken") == "negative"

    def test_infer_sentiment_neutral(self) -> None:
        assert infer_sentiment("I submitted a request for a new feature") == "neutral"

    def test_infer_sentiment_mixed_positive_wins(self) -> None:
        assert infer_sentiment("It's great and amazing despite a bad UI") == "positive"

    def test_infer_sentiment_mixed_negative_wins(self) -> None:
        assert infer_sentiment("Great but terrible, awful, and broken") == "negative"

    def test_infer_sentiment_empty_string(self) -> None:
        assert infer_sentiment("") == "neutral"


class TestCreateFeedback:
    """Tests for create_feedback."""

    def test_create_feedback(self) -> None:
        db = _mock_db_session()
        fb = _mock_feedback(sentiment="neutral")

        def _refresh(obj: Any) -> None:
            pass

        db.refresh = _refresh

        with patch("skillhub.services.feedback.SkillFeedback") as MockModel:
            mock_instance = fb
            MockModel.return_value = mock_instance

            result = create_feedback(
                db,
                user_id=USER_ID,
                category="feature_request",
                body="This is a great feature request for the platform",
            )

        assert result["category"] == "feature_request"
        assert result["id"] == FEEDBACK_ID
        assert result["status"] == "open"
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_create_feedback_invalid_category(self) -> None:
        db = _mock_db_session()
        with pytest.raises(ValueError, match="Invalid category"):
            create_feedback(
                db,
                user_id=USER_ID,
                category="invalid_category",
                body="Some feedback body text here",
            )


class TestListFeedback:
    """Tests for list_feedback."""

    def test_list_feedback_empty(self) -> None:
        db = _mock_db_session()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.all.return_value = []

        items, total = list_feedback(db)
        assert items == []
        assert total == 0

    def test_list_feedback_with_category_filter(self) -> None:
        db = _mock_db_session()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.all.return_value = []

        items, total = list_feedback(db, category="bug_report")
        assert total == 0
        # Verify filter was called (category filter applied)
        query_mock.filter.assert_called()


class TestUpvoteFeedback:
    """Tests for upvote_feedback."""

    def test_upvote_feedback(self) -> None:
        db = _mock_db_session()
        fb = _mock_feedback(upvotes=5)
        db.query.return_value.filter.return_value.first.return_value = fb

        def _refresh(obj: Any) -> None:
            pass

        db.refresh = _refresh

        result = upvote_feedback(db, feedback_id=str(FEEDBACK_ID), user_id=USER_ID)
        assert result["id"] == FEEDBACK_ID
        db.commit.assert_called_once()

    def test_upvote_feedback_not_found(self) -> None:
        db = _mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Feedback not found"):
            upvote_feedback(db, feedback_id=str(uuid.uuid4()), user_id=USER_ID)


class TestUpdateFeedbackStatus:
    """Tests for update_feedback_status."""

    def test_update_status_writes_audit(self) -> None:
        db = _mock_db_session()
        fb = _mock_feedback(status="open")
        db.query.return_value.filter.return_value.first.return_value = fb

        def _refresh(obj: Any) -> None:
            pass

        db.refresh = _refresh

        actor_id = str(uuid.uuid4())
        result = update_feedback_status(
            db, feedback_id=str(FEEDBACK_ID), status="triaged", actor_id=actor_id
        )
        assert result["id"] == FEEDBACK_ID
        # Should have added the feedback + audit log entry
        assert db.add.call_count >= 1
        db.commit.assert_called_once()

    def test_update_status_invalid(self) -> None:
        db = _mock_db_session()
        with pytest.raises(ValueError, match="Invalid status"):
            update_feedback_status(
                db,
                feedback_id=str(FEEDBACK_ID),
                status="nonexistent",
                actor_id=str(uuid.uuid4()),
            )

    def test_update_status_not_found(self) -> None:
        db = _mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Feedback not found"):
            update_feedback_status(
                db,
                feedback_id=str(uuid.uuid4()),
                status="triaged",
                actor_id=str(uuid.uuid4()),
            )
