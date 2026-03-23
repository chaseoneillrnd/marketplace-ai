"""Tests for reviews and comments service layer."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from skillhub.services.reviews import (
    BAYESIAN_C,
    BAYESIAN_M,
    DuplicateReviewError,
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

SKILL_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
OTHER_USER_ID = uuid.uuid4()
REVIEW_ID = uuid.uuid4()
COMMENT_ID = uuid.uuid4()


def _mock_skill(**overrides: Any) -> MagicMock:
    skill = MagicMock()
    skill.id = overrides.get("id", SKILL_ID)
    skill.slug = overrides.get("slug", "test-skill")
    return skill


def _mock_review(**overrides: Any) -> MagicMock:
    review = MagicMock()
    review.id = overrides.get("id", REVIEW_ID)
    review.skill_id = overrides.get("skill_id", SKILL_ID)
    review.user_id = overrides.get("user_id", USER_ID)
    review.rating = overrides.get("rating", 4)
    review.body = overrides.get("body", "Great skill!")
    review.helpful_count = overrides.get("helpful_count", 0)
    review.unhelpful_count = overrides.get("unhelpful_count", 0)
    review.created_at = overrides.get("created_at", datetime.now(UTC))
    review.updated_at = overrides.get("updated_at", datetime.now(UTC))
    return review


class TestBayesianRating:
    """Tests for the Bayesian avg_rating formula."""

    def test_bayesian_formula_correct_single_review(self) -> None:
        """Bayesian: (C*m + sum) / (C + count) with C=5, m=3.0."""
        # With one 5-star review: (5*3.0 + 5) / (5+1) = 20/6 = 3.33
        count = 1
        sum_ratings = Decimal("5")
        expected = round((BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + count), 2)
        assert expected == Decimal("3.33")

    def test_bayesian_formula_multiple_reviews(self) -> None:
        """Bayesian avg with 10 reviews averaging 4.5."""
        count = 10
        sum_ratings = Decimal("45")
        expected = round((BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + count), 2)
        assert expected == Decimal("4.00")

    def test_bayesian_formula_no_reviews(self) -> None:
        """With zero reviews, result should be m (3.0)."""
        count = 0
        sum_ratings = Decimal("0")
        expected = round((BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + count), 2)
        assert expected == BAYESIAN_M


class TestCreateReview:
    """Tests for create_review."""

    def test_valid_review_created(self) -> None:
        """Valid review creates row and returns dict."""
        from sqlalchemy.exc import IntegrityError

        db = MagicMock()
        skill = _mock_skill()
        # First .query().filter().first() → skill lookup
        # Then .query(func...).filter().first() → recalculate stats returns (1, 5)
        db.query.return_value.filter.return_value.first.side_effect = [
            skill, (1, 5)
        ]
        db.flush.return_value = None

        result = create_review(db, "test-skill", USER_ID, 5, "Excellent!")

        assert result["user_id"] == USER_ID
        assert result["rating"] == 5
        assert result["body"] == "Excellent!"
        db.add.assert_called()
        db.commit.assert_called_once()

    def test_duplicate_review_returns_409(self) -> None:
        """Second review by same user raises DuplicateReviewError."""
        from sqlalchemy.exc import IntegrityError

        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        db.flush.side_effect = IntegrityError("", {}, Exception())

        with pytest.raises(DuplicateReviewError):
            create_review(db, "test-skill", USER_ID, 5, "Again!")


class TestUpdateReview:
    """Tests for update_review."""

    def test_owner_can_update(self) -> None:
        """Review owner can update body/rating."""
        db = MagicMock()
        skill = _mock_skill()
        review = _mock_review(user_id=USER_ID)
        # skill lookup, review lookup, recalculate stats
        db.query.return_value.filter.return_value.first.side_effect = [
            skill, review, (1, 3)
        ]

        result = update_review(
            db, "test-skill", REVIEW_ID, USER_ID, rating=3, body="Updated"
        )

        assert review.rating == 3
        assert review.body == "Updated"
        db.commit.assert_called_once()

    def test_non_owner_gets_403(self) -> None:
        """PATCH review by non-owner raises PermissionError."""
        db = MagicMock()
        skill = _mock_skill()
        review = _mock_review(user_id=OTHER_USER_ID)
        db.query.return_value.filter.return_value.first.side_effect = [skill, review]

        with pytest.raises(PermissionError, match="owner"):
            update_review(db, "test-skill", REVIEW_ID, USER_ID, rating=1)


class TestVoteOnReview:
    """Tests for vote_on_review."""

    def test_vote_upsert_is_idempotent(self) -> None:
        """Voting twice changes the vote type, doesn't create duplicate."""
        db = MagicMock()
        skill = _mock_skill()
        review = _mock_review(helpful_count=1)
        existing_vote = MagicMock()
        existing_vote.vote = MagicMock()
        existing_vote.vote.value = "helpful"
        # Make the comparison work
        from skillhub_db.models.social import VoteType
        existing_vote.vote = VoteType.HELPFUL

        db.query.return_value.filter.return_value.first.side_effect = [
            skill, review, existing_vote
        ]

        vote_on_review(db, "test-skill", REVIEW_ID, USER_ID, "unhelpful")

        db.commit.assert_called_once()
        # Should NOT add a new vote (upsert)
        assert existing_vote.vote == VoteType.UNHELPFUL

    def test_new_vote_creates_record(self) -> None:
        """First vote creates a new ReviewVote."""
        db = MagicMock()
        skill = _mock_skill()
        review = _mock_review()
        db.query.return_value.filter.return_value.first.side_effect = [
            skill, review, None
        ]

        vote_on_review(db, "test-skill", REVIEW_ID, USER_ID, "helpful")

        db.add.assert_called()
        db.commit.assert_called_once()


class TestListReviews:
    """Tests for list_reviews."""

    def test_returns_paginated_reviews(self) -> None:
        """List returns reviews sorted by helpful_count DESC."""
        db = MagicMock()
        skill = _mock_skill()
        review = _mock_review()
        db.query.return_value.filter.return_value.first.return_value = skill
        db.query.return_value.filter.return_value.count.return_value = 1
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [review]

        items, total = list_reviews(db, "test-skill")

        assert total == 1
        assert len(items) == 1
        assert items[0]["id"] == REVIEW_ID


class TestCreateComment:
    """Tests for create_comment."""

    def test_creates_comment(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill

        result = create_comment(db, "test-skill", USER_ID, "Hello!")

        assert result["body"] == "Hello!"
        db.add.assert_called()
        db.commit.assert_called_once()


class TestDeleteComment:
    """Tests for delete_comment (soft delete)."""

    def test_soft_delete_replaces_body_with_deleted(self) -> None:
        """Soft delete sets body to [deleted] and sets deleted_at."""
        db = MagicMock()
        skill = _mock_skill()
        comment = MagicMock()
        comment.id = COMMENT_ID
        comment.skill_id = SKILL_ID
        comment.user_id = USER_ID
        comment.body = "Original content"
        comment.upvote_count = 0
        comment.deleted_at = None
        comment.created_at = datetime.now(UTC)
        comment.replies = []
        db.query.return_value.filter.return_value.first.side_effect = [skill]
        db.query.return_value.options.return_value.filter.return_value.first.return_value = comment

        result = delete_comment(db, "test-skill", COMMENT_ID, USER_ID)

        assert comment.body == "[deleted]"
        # deleted_at is now set via query-based update, so verify update was called
        db.query.return_value.filter.return_value.update.assert_called()
        db.commit.assert_called_once()

    def test_non_owner_non_platform_gets_403(self) -> None:
        """Non-owner and non-platform user cannot delete."""
        db = MagicMock()
        skill = _mock_skill()
        comment = MagicMock()
        comment.id = COMMENT_ID
        comment.user_id = OTHER_USER_ID
        db.query.return_value.filter.return_value.first.side_effect = [skill]
        db.query.return_value.options.return_value.filter.return_value.first.return_value = comment

        with pytest.raises(PermissionError, match="owner or platform"):
            delete_comment(db, "test-skill", COMMENT_ID, USER_ID, is_platform_team=False)

    def test_platform_team_can_delete(self) -> None:
        """Platform team can delete any comment."""
        db = MagicMock()
        skill = _mock_skill()
        comment = MagicMock()
        comment.id = COMMENT_ID
        comment.skill_id = SKILL_ID
        comment.user_id = OTHER_USER_ID
        comment.body = "Some content"
        comment.upvote_count = 0
        comment.deleted_at = None
        comment.created_at = datetime.now(UTC)
        comment.replies = []
        db.query.return_value.filter.return_value.first.side_effect = [skill]
        db.query.return_value.options.return_value.filter.return_value.first.return_value = comment

        result = delete_comment(db, "test-skill", COMMENT_ID, USER_ID, is_platform_team=True)

        assert comment.body == "[deleted]"


class TestCommentVote:
    """Tests for vote_on_comment."""

    def test_vote_is_idempotent(self) -> None:
        """Second vote on same comment does not create duplicate."""
        db = MagicMock()
        skill = _mock_skill()
        comment = MagicMock()
        comment.id = COMMENT_ID
        comment.upvote_count = 1
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            skill, comment, existing
        ]

        vote_on_comment(db, "test-skill", COMMENT_ID, USER_ID)

        # Should NOT add or increment (idempotent)
        db.add.assert_not_called()
        db.commit.assert_not_called()


class TestCreateReply:
    """Tests for create_reply."""

    def test_creates_reply(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        comment = MagicMock()
        comment.id = COMMENT_ID
        db.query.return_value.filter.return_value.first.side_effect = [skill, comment]

        result = create_reply(db, "test-skill", COMMENT_ID, USER_ID, "A reply")

        assert result["body"] == "A reply"
        db.add.assert_called()
        db.commit.assert_called_once()
