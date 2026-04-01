"""Coverage tests for skillhub.services.feedback — create, list, upvote, triage."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

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


class TestInferSentiment:
    def test_positive_words(self) -> None:
        assert infer_sentiment("This is amazing and great!") == "positive"

    def test_negative_words(self) -> None:
        assert infer_sentiment("This is terrible and broken") == "negative"

    def test_neutral_when_balanced(self) -> None:
        assert infer_sentiment("Somewhat helpful but also bad") == "neutral"

    def test_neutral_empty(self) -> None:
        assert infer_sentiment("No keywords here") == "neutral"

    def test_bug_keyword_is_negative(self) -> None:
        assert infer_sentiment("There is a bug in this skill") == "negative"

    def test_love_is_positive(self) -> None:
        assert infer_sentiment("I love this skill") == "positive"


class TestCreateFeedback:
    def _make_feedback_obj(self, user_id: uuid.UUID) -> MagicMock:
        fb = MagicMock()
        fb.id = uuid.uuid4()
        fb.user_id = user_id
        fb.skill_id = None
        fb.category = "bug_report"
        fb.body = "This is broken"
        fb.sentiment = "negative"
        fb.upvotes = 0
        fb.status = "open"
        fb.allow_contact = False
        fb.created_at = None
        return fb

    def test_create_feedback_success(self) -> None:
        user_id = uuid.uuid4()
        fb = self._make_feedback_obj(user_id)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = fb

        with __import__("unittest.mock", fromlist=["patch"]).patch(
            "skillhub.services.feedback.SkillFeedback"
        ) as MockFB:
            MockFB.return_value = fb
            result = create_feedback(
                db,
                user_id=str(user_id),
                category="bug_report",
                body="This is broken",
            )

        db.add.assert_called_once_with(fb)
        db.commit.assert_called_once()
        assert result["category"] == "bug_report"
        assert result["sentiment"] == "negative"

    def test_invalid_category_raises(self) -> None:
        db = MagicMock()
        with pytest.raises(ValueError, match="Invalid category"):
            create_feedback(db, user_id=str(uuid.uuid4()), category="invalid", body="test")

    def test_create_with_skill_id(self) -> None:
        user_id = uuid.uuid4()
        skill_id = uuid.uuid4()
        fb = MagicMock()
        fb.id = uuid.uuid4()
        fb.user_id = user_id
        fb.skill_id = skill_id
        fb.category = "feature_request"
        fb.body = "Add dark mode"
        fb.sentiment = "neutral"
        fb.upvotes = 0
        fb.status = "open"
        fb.allow_contact = True
        fb.created_at = None

        db = MagicMock()

        with __import__("unittest.mock", fromlist=["patch"]).patch(
            "skillhub.services.feedback.SkillFeedback"
        ) as MockFB:
            MockFB.return_value = fb
            result = create_feedback(
                db,
                user_id=str(user_id),
                category="feature_request",
                body="Add dark mode",
                skill_id=str(skill_id),
                allow_contact=True,
            )

        assert result["allow_contact"] is True


class TestListFeedback:
    def _make_feedback_item(self, category: str = "bug_report") -> MagicMock:
        fb = MagicMock()
        fb.id = uuid.uuid4()
        fb.user_id = uuid.uuid4()
        fb.skill_id = uuid.uuid4()
        fb.category = category
        fb.body = "Some feedback"
        fb.sentiment = "neutral"
        fb.upvotes = 3
        fb.status = "open"
        fb.allow_contact = False
        fb.created_at = None
        return fb

    def test_list_returns_items(self) -> None:
        fb = self._make_feedback_item()

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 1
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = [fb]

        # For skill/user name resolution
        skill_row = MagicMock()
        skill_row.id = fb.skill_id
        skill_row.name = "Test Skill"

        user_row = MagicMock()
        user_row.id = fb.user_id
        user_row.name = "Alice"

        q_skill = MagicMock()
        q_skill.filter.return_value = q_skill
        q_skill.all.return_value = [skill_row]

        q_user = MagicMock()
        q_user.filter.return_value = q_user
        q_user.all.return_value = [user_row]

        db.query.side_effect = [q, q_skill, q_user]

        items, total = list_feedback(db)

        assert total == 1
        assert len(items) == 1
        assert items[0]["skill_name"] == "Test Skill"

    def test_list_with_category_filter(self) -> None:
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 0
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        items, total = list_feedback(db, category="bug_report")
        assert total == 0
        assert items == []

    def test_list_sort_newest(self) -> None:
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 0
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        items, total = list_feedback(db, sort="newest")
        assert total == 0

    def test_list_sort_upvotes(self) -> None:
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 0
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        items, total = list_feedback(db, sort="upvotes")
        assert total == 0


class TestUpvoteFeedback:
    def test_new_upvote_increments(self) -> None:
        feedback_id = uuid.uuid4()
        user_id = uuid.uuid4()
        fb = MagicMock()
        fb.id = feedback_id
        fb.upvotes = 2

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.side_effect = [fb, None]  # feedback found, no existing upvote
        db.query.return_value = q

        result = upvote_feedback(db, feedback_id=str(feedback_id), user_id=str(user_id))

        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result["already_upvoted"] is False

    def test_already_upvoted_is_idempotent(self) -> None:
        feedback_id = uuid.uuid4()
        user_id = uuid.uuid4()
        fb = MagicMock()
        fb.id = feedback_id
        fb.upvotes = 5
        existing_upvote = MagicMock()

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.side_effect = [fb, existing_upvote]
        db.query.return_value = q

        result = upvote_feedback(db, feedback_id=str(feedback_id), user_id=str(user_id))

        db.commit.assert_not_called()
        assert result["already_upvoted"] is True

    def test_feedback_not_found_raises(self) -> None:
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        with pytest.raises(ValueError, match="Feedback not found"):
            upvote_feedback(db, feedback_id=str(uuid.uuid4()), user_id=str(uuid.uuid4()))


class TestUpdateFeedbackStatus:
    def test_update_status_success(self) -> None:
        feedback_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        fb = MagicMock()
        fb.id = feedback_id
        fb.status = "open"
        fb.user_id = uuid.uuid4()
        fb.skill_id = None
        fb.category = "bug_report"
        fb.body = "something"
        fb.sentiment = "negative"
        fb.upvotes = 0
        fb.allow_contact = False
        fb.created_at = None

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = fb

        result = update_feedback_status(
            db,
            feedback_id=str(feedback_id),
            status="triaged",
            actor_id=str(actor_id),
        )

        assert fb.status == "triaged"
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_invalid_status_raises(self) -> None:
        db = MagicMock()
        with pytest.raises(ValueError, match="Invalid status"):
            update_feedback_status(
                db,
                feedback_id=str(uuid.uuid4()),
                status="nonsense",
                actor_id=str(uuid.uuid4()),
            )

    def test_feedback_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Feedback not found"):
            update_feedback_status(
                db,
                feedback_id=str(uuid.uuid4()),
                status="triaged",
                actor_id=str(uuid.uuid4()),
            )
