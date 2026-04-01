"""Coverage tests for skillhub.services.reviews — reviews, comments, replies."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from skillhub.services.reviews import (
    DuplicateReviewError,
    _comment_to_dict,
    _get_skill_by_slug,
    _recalculate_avg_rating,
    _reply_to_dict,
    _review_to_dict,
    _write_audit,
    create_comment,
    create_reply,
    create_review,
    delete_comment,
    list_comments,
    list_reviews,
    update_review,
    vote_on_comment,
    vote_on_review,
)


def _mock_skill() -> MagicMock:
    skill = MagicMock()
    skill.id = uuid.uuid4()
    skill.slug = "test-skill"
    skill.avg_rating = Decimal("3.5")
    skill.review_count = 2
    return skill


def _mock_review(skill_id: uuid.UUID | None = None) -> MagicMock:
    r = MagicMock()
    r.id = uuid.uuid4()
    r.skill_id = skill_id or uuid.uuid4()
    r.user_id = uuid.uuid4()
    r.rating = 4
    r.body = "Great skill"
    r.helpful_count = 3
    r.unhelpful_count = 1
    r.created_at = None
    r.updated_at = None
    return r


def _mock_comment(skill_id: uuid.UUID | None = None) -> MagicMock:
    c = MagicMock()
    c.id = uuid.uuid4()
    c.skill_id = skill_id or uuid.uuid4()
    c.user_id = uuid.uuid4()
    c.body = "Nice work!"
    c.upvote_count = 5
    c.deleted_at = None
    c.created_at = None
    c.replies = []
    return c


def _mock_reply(comment_id: uuid.UUID | None = None) -> MagicMock:
    r = MagicMock()
    r.id = uuid.uuid4()
    r.comment_id = comment_id or uuid.uuid4()
    r.user_id = uuid.uuid4()
    r.body = "Thanks!"
    r.deleted_at = None
    r.created_at = None
    return r


class TestGetSkillBySlug:
    def test_found_returns_skill(self) -> None:
        skill = _mock_skill()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = skill
        result = _get_skill_by_slug(db, "test-skill")
        assert result is skill

    def test_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="not found"):
            _get_skill_by_slug(db, "missing")


class TestWriteAudit:
    def test_adds_audit_log_entry(self) -> None:
        db = MagicMock()
        actor_id = uuid.uuid4()
        _write_audit(
            db,
            event_type="test.event",
            actor_id=actor_id,
            target_type="skill",
            target_id="some-id",
            metadata={"key": "val"},
        )
        db.add.assert_called_once()


class TestRecalculateAvgRating:
    def test_updates_avg_rating(self) -> None:
        skill_id = uuid.uuid4()

        db = MagicMock()
        q_stats = MagicMock()
        q_stats.filter.return_value = q_stats
        q_stats.first.return_value = (3, 12)  # 3 reviews, sum=12

        q_update = MagicMock()
        q_update.filter.return_value = q_update
        q_update.update.return_value = 1

        db.query.side_effect = [q_stats, q_update]

        _recalculate_avg_rating(db, skill_id)

        q_update.update.assert_called_once()


class TestReviewToDict:
    def test_returns_correct_fields(self) -> None:
        r = _mock_review()
        d = _review_to_dict(r)
        assert d["id"] == r.id
        assert d["rating"] == r.rating
        assert d["helpful_count"] == r.helpful_count


class TestCommentToDict:
    def test_returns_correct_fields_with_replies(self) -> None:
        c = _mock_comment()
        reply = _mock_reply(comment_id=c.id)
        c.replies = [reply]
        d = _comment_to_dict(c)
        assert d["id"] == c.id
        assert len(d["replies"]) == 1
        assert d["replies"][0]["body"] == "Thanks!"


class TestReplyToDict:
    def test_returns_correct_fields(self) -> None:
        r = _mock_reply()
        d = _reply_to_dict(r)
        assert d["id"] == r.id
        assert d["body"] == r.body


class TestListReviews:
    def test_returns_paginated_reviews(self) -> None:
        skill = _mock_skill()
        review = _mock_review(skill_id=skill.id)

        db = MagicMock()
        q_skill = MagicMock()
        q_skill.filter.return_value = q_skill
        q_skill.first.return_value = skill

        q_reviews = MagicMock()
        q_reviews.filter.return_value = q_reviews
        q_reviews.count.return_value = 1
        q_reviews.order_by.return_value = q_reviews
        q_reviews.offset.return_value = q_reviews
        q_reviews.limit.return_value = q_reviews
        q_reviews.all.return_value = [review]

        db.query.side_effect = [q_skill, q_reviews]

        items, total = list_reviews(db, "test-skill")
        assert total == 1
        assert items[0]["rating"] == 4

    def test_skill_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="not found"):
            list_reviews(db, "missing-skill")


class TestCreateReview:
    def test_successful_review_creation(self) -> None:
        skill = _mock_skill()
        user_id = uuid.uuid4()
        review = _mock_review(skill_id=skill.id)
        review.user_id = user_id

        db = MagicMock()
        q_skill = MagicMock()
        q_skill.filter.return_value = q_skill
        q_skill.first.return_value = skill

        # For _recalculate_avg_rating
        q_stats = MagicMock()
        q_stats.filter.return_value = q_stats
        q_stats.first.return_value = (1, 4)

        q_update = MagicMock()
        q_update.filter.return_value = q_update
        q_update.update.return_value = 1

        db.query.side_effect = [q_skill, q_stats, q_update]

        with patch("skillhub.services.reviews.Review") as MockReview:
            MockReview.return_value = review
            result = create_review(db, "test-skill", user_id, 4, "Great skill")

        db.add.assert_called()
        db.flush.assert_called_once()
        db.commit.assert_called_once()
        assert result["rating"] == 4

    def test_duplicate_review_raises(self) -> None:
        skill = _mock_skill()
        user_id = uuid.uuid4()
        review = _mock_review(skill_id=skill.id)

        db = MagicMock()
        q_skill = MagicMock()
        q_skill.filter.return_value = q_skill
        q_skill.first.return_value = skill
        db.query.return_value = q_skill
        db.flush.side_effect = IntegrityError("dup", None, None)

        with patch("skillhub.services.reviews.Review") as MockReview:
            MockReview.return_value = review
            with pytest.raises(DuplicateReviewError):
                create_review(db, "test-skill", user_id, 4, "Great")


class TestUpdateReview:
    def test_update_by_owner(self) -> None:
        skill = _mock_skill()
        user_id = uuid.uuid4()
        review = _mock_review(skill_id=skill.id)
        review.user_id = user_id
        review_id = review.id

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.filter.return_value = q2
        q2.first.return_value = review

        q_stats = MagicMock()
        q_stats.filter.return_value = q_stats
        q_stats.first.return_value = (2, 8)

        q_upd = MagicMock()
        q_upd.filter.return_value = q_upd
        q_upd.update.return_value = 1

        db.query.side_effect = [q1, q2, q_stats, q_upd]

        result = update_review(db, "test-skill", review_id, user_id, rating=5, body="Updated")

        assert review.rating == 5
        assert review.body == "Updated"
        db.commit.assert_called_once()

    def test_update_by_non_owner_raises(self) -> None:
        skill = _mock_skill()
        owner_id = uuid.uuid4()
        other_id = uuid.uuid4()
        review = _mock_review(skill_id=skill.id)
        review.user_id = owner_id

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.filter.return_value = q2
        q2.first.return_value = review

        db.query.side_effect = [q1, q2]

        with pytest.raises(PermissionError, match="Only the review owner"):
            update_review(db, "test-skill", review.id, other_id, rating=1)

    def test_review_not_found_raises(self) -> None:
        skill = _mock_skill()
        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.filter.return_value = q2
        q2.first.return_value = None

        db.query.side_effect = [q1, q2]

        with pytest.raises(ValueError, match="Review not found"):
            update_review(db, "test-skill", uuid.uuid4(), uuid.uuid4())


class TestVoteOnReview:
    def test_new_vote_helpful(self) -> None:
        skill = _mock_skill()
        review = _mock_review(skill_id=skill.id)
        review.helpful_count = 0
        review.unhelpful_count = 0
        user_id = uuid.uuid4()

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.filter.return_value = q2
        q2.first.return_value = review

        q3 = MagicMock()
        q3.filter.return_value = q3
        q3.first.return_value = None  # no existing vote

        db.query.side_effect = [q1, q2, q3]

        vote_on_review(db, "test-skill", review.id, user_id, "helpful")

        db.add.assert_called()
        db.commit.assert_called_once()
        assert review.helpful_count == 1

    def test_same_vote_is_idempotent(self) -> None:
        from skillhub_db.models.social import VoteType
        skill = _mock_skill()
        review = _mock_review(skill_id=skill.id)
        user_id = uuid.uuid4()

        existing_vote = MagicMock()
        existing_vote.vote = VoteType.HELPFUL

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.filter.return_value = q2
        q2.first.return_value = review

        q3 = MagicMock()
        q3.filter.return_value = q3
        q3.first.return_value = existing_vote

        db.query.side_effect = [q1, q2, q3]

        vote_on_review(db, "test-skill", review.id, user_id, "helpful")
        db.commit.assert_not_called()

    def test_review_not_found_raises(self) -> None:
        skill = _mock_skill()

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.filter.return_value = q2
        q2.first.return_value = None

        db.query.side_effect = [q1, q2]

        with pytest.raises(ValueError, match="Review not found"):
            vote_on_review(db, "test-skill", uuid.uuid4(), uuid.uuid4(), "helpful")


class TestListComments:
    def test_returns_paginated_comments(self) -> None:
        skill = _mock_skill()
        comment = _mock_comment(skill_id=skill.id)

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.options.return_value = q2
        q2.filter.return_value = q2
        q2.count.return_value = 1
        q2.order_by.return_value = q2
        q2.offset.return_value = q2
        q2.limit.return_value = q2
        q2.all.return_value = [comment]

        db.query.side_effect = [q1, q2]

        items, total = list_comments(db, "test-skill")
        assert total == 1
        assert items[0]["body"] == "Nice work!"


class TestCreateComment:
    def test_creates_comment(self) -> None:
        skill = _mock_skill()
        user_id = uuid.uuid4()
        comment = _mock_comment(skill_id=skill.id)

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill
        db.query.return_value = q1

        with patch("skillhub.services.reviews.Comment") as MockComment:
            MockComment.return_value = comment
            result = create_comment(db, "test-skill", user_id, "Nice work!")

        db.add.assert_called()
        db.commit.assert_called_once()
        assert result["body"] == "Nice work!"


class TestDeleteComment:
    def test_owner_can_delete(self) -> None:
        skill = _mock_skill()
        user_id = uuid.uuid4()
        comment = _mock_comment(skill_id=skill.id)
        comment.user_id = user_id

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.options.return_value = q2
        q2.filter.return_value = q2
        q2.first.return_value = comment
        q2.update.return_value = 1

        db.query.side_effect = [q1, q2, q2]

        result = delete_comment(db, "test-skill", comment.id, user_id)
        assert comment.body == "[deleted]"
        db.commit.assert_called_once()

    def test_platform_team_can_delete_others_comment(self) -> None:
        skill = _mock_skill()
        owner_id = uuid.uuid4()
        platform_user = uuid.uuid4()
        comment = _mock_comment(skill_id=skill.id)
        comment.user_id = owner_id

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.options.return_value = q2
        q2.filter.return_value = q2
        q2.first.return_value = comment
        q2.update.return_value = 1

        db.query.side_effect = [q1, q2, q2]

        result = delete_comment(db, "test-skill", comment.id, platform_user, is_platform_team=True)
        assert comment.body == "[deleted]"

    def test_non_owner_cannot_delete(self) -> None:
        skill = _mock_skill()
        owner_id = uuid.uuid4()
        other_id = uuid.uuid4()
        comment = _mock_comment(skill_id=skill.id)
        comment.user_id = owner_id

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.options.return_value = q2
        q2.filter.return_value = q2
        q2.first.return_value = comment

        db.query.side_effect = [q1, q2]

        with pytest.raises(PermissionError, match="Only the comment owner"):
            delete_comment(db, "test-skill", comment.id, other_id)


class TestCreateReply:
    def test_creates_reply(self) -> None:
        skill = _mock_skill()
        comment = _mock_comment(skill_id=skill.id)
        user_id = uuid.uuid4()
        reply = _mock_reply(comment_id=comment.id)

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.filter.return_value = q2
        q2.first.return_value = comment

        db.query.side_effect = [q1, q2]

        with patch("skillhub.services.reviews.Reply") as MockReply:
            MockReply.return_value = reply
            result = create_reply(db, "test-skill", comment.id, user_id, "Thanks!")

        db.add.assert_called()
        db.commit.assert_called_once()
        assert result["body"] == "Thanks!"

    def test_comment_not_found_raises(self) -> None:
        skill = _mock_skill()

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.filter.return_value = q2
        q2.first.return_value = None

        db.query.side_effect = [q1, q2]

        with pytest.raises(ValueError, match="Comment not found"):
            create_reply(db, "test-skill", uuid.uuid4(), uuid.uuid4(), "Reply")


class TestVoteOnComment:
    def test_new_upvote(self) -> None:
        skill = _mock_skill()
        comment = _mock_comment(skill_id=skill.id)
        comment.upvote_count = 0
        user_id = uuid.uuid4()

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.filter.return_value = q2
        q2.first.return_value = comment

        q3 = MagicMock()
        q3.filter.return_value = q3
        q3.first.return_value = None  # no existing vote

        db.query.side_effect = [q1, q2, q3]

        vote_on_comment(db, "test-skill", comment.id, user_id)
        assert comment.upvote_count == 1
        db.commit.assert_called_once()

    def test_already_voted_is_idempotent(self) -> None:
        skill = _mock_skill()
        comment = _mock_comment(skill_id=skill.id)
        user_id = uuid.uuid4()
        existing = MagicMock()

        db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value = q1
        q1.first.return_value = skill

        q2 = MagicMock()
        q2.filter.return_value = q2
        q2.first.return_value = comment

        q3 = MagicMock()
        q3.filter.return_value = q3
        q3.first.return_value = existing

        db.query.side_effect = [q1, q2, q3]

        vote_on_comment(db, "test-skill", comment.id, user_id)
        db.commit.assert_not_called()
