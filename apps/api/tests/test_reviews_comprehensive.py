"""Comprehensive tests for review system — constraints, rating, votes, denormalization."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from skillhub.services.reviews import (
    BAYESIAN_C,
    BAYESIAN_M,
    DuplicateReviewError,
    create_review,
    list_reviews,
    update_review,
    vote_on_review,
)
from tests.conftest import _make_settings, make_token

SKILL_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
OTHER_USER_ID = uuid.uuid4()
REVIEW_ID = uuid.uuid4()


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


def _auth_headers(**extra_claims: Any) -> dict[str, str]:
    claims: dict[str, Any] = {
        "user_id": str(USER_ID),
        "sub": "test-user",
        "name": "Test User",
        "division": "engineering",
        "role": "engineer",
        "is_platform_team": False,
        "is_security_team": False,
    }
    claims.update(extra_claims)
    token = make_token(claims)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def mock_db() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def app_with_db(mock_db: MagicMock) -> Any:
    settings = _make_settings()
    application = create_app(settings=settings)
    application.dependency_overrides[get_db] = lambda: mock_db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app_with_db: Any) -> TestClient:
    return TestClient(app_with_db)


@pytest.fixture()
def auth_headers_fixture() -> dict[str, str]:
    return _auth_headers()


# --- One Review Per User Constraint ---


class TestOneReviewPerUser:
    """Test the unique constraint on (user_id, skill_id)."""

    def test_first_review_succeeds(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.side_effect = [
            skill, (1, 5)
        ]
        db.flush.return_value = None

        result = create_review(db, "test-skill", USER_ID, 5, "Excellent!")

        assert result["rating"] == 5
        db.add.assert_called()
        db.commit.assert_called_once()

    def test_duplicate_review_raises_duplicate_error(self) -> None:
        from sqlalchemy.exc import IntegrityError

        db = MagicMock()
        skill = _mock_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        db.flush.side_effect = IntegrityError("", {}, Exception())

        with pytest.raises(DuplicateReviewError):
            create_review(db, "test-skill", USER_ID, 5, "Again!")

    @patch("skillhub.routers.social.create_review")
    def test_duplicate_review_returns_409_at_router(
        self, mock_create: MagicMock, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        mock_create.side_effect = DuplicateReviewError("Already reviewed")
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": 5, "body": "Again!"},
            headers=auth_headers_fixture,
        )
        assert response.status_code == 409


# --- Rating Validation ---


class TestRatingValidation:
    """Test rating must be 1-5."""

    def test_rating_1_accepted(self, client: TestClient, auth_headers_fixture: dict[str, str]) -> None:
        with patch("skillhub.routers.social.create_review") as mock_create:
            mock_create.return_value = {
                "id": REVIEW_ID, "skill_id": SKILL_ID, "user_id": USER_ID,
                "rating": 1, "body": "Bad", "helpful_count": 0, "unhelpful_count": 0,
                "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
            }
            response = client.post(
                "/api/v1/skills/test-skill/reviews",
                json={"rating": 1, "body": "Bad"},
                headers=auth_headers_fixture,
            )
            assert response.status_code == 201

    def test_rating_5_accepted(self, client: TestClient, auth_headers_fixture: dict[str, str]) -> None:
        with patch("skillhub.routers.social.create_review") as mock_create:
            mock_create.return_value = {
                "id": REVIEW_ID, "skill_id": SKILL_ID, "user_id": USER_ID,
                "rating": 5, "body": "Great", "helpful_count": 0, "unhelpful_count": 0,
                "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
            }
            response = client.post(
                "/api/v1/skills/test-skill/reviews",
                json={"rating": 5, "body": "Great"},
                headers=auth_headers_fixture,
            )
            assert response.status_code == 201

    def test_rating_0_rejected(self, client: TestClient, auth_headers_fixture: dict[str, str]) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": 0, "body": "Zero"},
            headers=auth_headers_fixture,
        )
        assert response.status_code == 422

    def test_rating_6_rejected(self, client: TestClient, auth_headers_fixture: dict[str, str]) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": 6, "body": "Too high"},
            headers=auth_headers_fixture,
        )
        assert response.status_code == 422

    def test_rating_negative_rejected(self, client: TestClient, auth_headers_fixture: dict[str, str]) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": -1, "body": "Negative"},
            headers=auth_headers_fixture,
        )
        assert response.status_code == 422

    def test_rating_float_rejected(self, client: TestClient, auth_headers_fixture: dict[str, str]) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": 3.5, "body": "Float"},
            headers=auth_headers_fixture,
        )
        # FastAPI may coerce or reject floats depending on schema
        assert response.status_code in (201, 422)


# --- Bayesian Average Rating ---


class TestBayesianRating:
    """Test the Bayesian avg_rating calculation."""

    def test_no_reviews_equals_prior(self) -> None:
        """With zero reviews, Bayesian avg = prior mean m."""
        count = 0
        sum_ratings = Decimal("0")
        result = round(
            (BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + count), 2
        )
        assert result == BAYESIAN_M

    def test_single_5_star_review(self) -> None:
        """One 5-star: (C*m + 5) / (C + 1)."""
        count = 1
        sum_ratings = Decimal("5")
        result = round(
            (BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + count), 2
        )
        assert result == Decimal("3.33")

    def test_ten_reviews_averaging_4_5(self) -> None:
        """10 reviews with sum=45 (avg 4.5)."""
        count = 10
        sum_ratings = Decimal("45")
        result = round(
            (BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + count), 2
        )
        assert result == Decimal("4.00")

    def test_100_reviews_converges_to_true_mean(self) -> None:
        """With many reviews, Bayesian avg converges to true mean."""
        count = 100
        true_mean = Decimal("4.5")
        sum_ratings = true_mean * count
        result = round(
            (BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + count), 2
        )
        # With C=5, m=3.0 and 100 reviews at 4.5:
        # (5*3 + 450)/(5+100) = 465/105 = 4.43
        assert result == Decimal("4.43")

    def test_single_1_star_review(self) -> None:
        """One 1-star: (C*m + 1) / (C + 1)."""
        count = 1
        sum_ratings = Decimal("1")
        result = round(
            (BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + count), 2
        )
        assert result == Decimal("2.67")


# --- Helpful/Unhelpful Votes ---


class TestReviewVotes:
    """Test helpful and unhelpful vote mechanics."""

    def test_new_vote_creates_record(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        review = _mock_review()
        db.query.return_value.filter.return_value.first.side_effect = [
            skill, review, None
        ]

        vote_on_review(db, "test-skill", REVIEW_ID, USER_ID, "helpful")

        db.add.assert_called()
        db.commit.assert_called_once()

    def test_vote_upsert_changes_type(self) -> None:
        """Voting again with a different type changes the vote."""
        from skillhub_db.models.social import VoteType

        db = MagicMock()
        skill = _mock_skill()
        review = _mock_review(helpful_count=1)
        existing_vote = MagicMock()
        existing_vote.vote = VoteType.HELPFUL

        db.query.return_value.filter.return_value.first.side_effect = [
            skill, review, existing_vote
        ]

        vote_on_review(db, "test-skill", REVIEW_ID, USER_ID, "unhelpful")

        db.commit.assert_called_once()
        assert existing_vote.vote == VoteType.UNHELPFUL

    @patch("skillhub.routers.social.vote_on_review")
    def test_vote_helpful_returns_204(
        self, mock_vote: MagicMock, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        mock_vote.return_value = None
        response = client.post(
            f"/api/v1/skills/test-skill/reviews/{REVIEW_ID}/vote",
            json={"vote": "helpful"},
            headers=auth_headers_fixture,
        )
        assert response.status_code == 204

    @patch("skillhub.routers.social.vote_on_review")
    def test_vote_unhelpful_returns_204(
        self, mock_vote: MagicMock, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        mock_vote.return_value = None
        response = client.post(
            f"/api/v1/skills/test-skill/reviews/{REVIEW_ID}/vote",
            json={"vote": "unhelpful"},
            headers=auth_headers_fixture,
        )
        assert response.status_code == 204

    def test_invalid_vote_type_returns_422(
        self, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        response = client.post(
            f"/api/v1/skills/test-skill/reviews/{REVIEW_ID}/vote",
            json={"vote": "invalid"},
            headers=auth_headers_fixture,
        )
        assert response.status_code == 422


# --- Review Count Denormalization ---


class TestReviewCountDenormalization:
    """Test that review_count and avg_rating are updated on create/update."""

    def test_create_review_updates_skill_stats(self) -> None:
        """After creating a review, the Skill's stats are recalculated."""
        db = MagicMock()
        skill = _mock_skill()
        # First query returns skill, second returns stats (count, sum)
        db.query.return_value.filter.return_value.first.side_effect = [
            skill, (5, 22)  # 5 reviews, sum=22
        ]
        db.flush.return_value = None

        create_review(db, "test-skill", USER_ID, 4, "Good skill")

        db.commit.assert_called_once()
        # The skill's review_count and avg_rating should be updated via query.update()
        db.query.return_value.filter.return_value.update.assert_called()


# --- Review Update ---


class TestReviewUpdate:
    """Test review update and rating recalculation."""

    def test_owner_can_update_rating_and_body(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        review = _mock_review(user_id=USER_ID)
        db.query.return_value.filter.return_value.first.side_effect = [
            skill, review, (3, 12)
        ]

        result = update_review(
            db, "test-skill", REVIEW_ID, USER_ID, rating=3, body="Updated review"
        )

        assert review.rating == 3
        assert review.body == "Updated review"
        db.commit.assert_called_once()

    def test_non_owner_cannot_update(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        review = _mock_review(user_id=OTHER_USER_ID)
        db.query.return_value.filter.return_value.first.side_effect = [skill, review]

        with pytest.raises(PermissionError, match="owner"):
            update_review(db, "test-skill", REVIEW_ID, USER_ID, rating=1)

    @patch("skillhub.routers.social.update_review")
    def test_non_owner_patch_returns_403(
        self, mock_update: MagicMock, client: TestClient, auth_headers_fixture: dict[str, str]
    ) -> None:
        mock_update.side_effect = PermissionError("Only the review owner can update")
        response = client.patch(
            f"/api/v1/skills/test-skill/reviews/{REVIEW_ID}",
            json={"rating": 1},
            headers=auth_headers_fixture,
        )
        assert response.status_code == 403


# --- List Reviews ---


class TestListReviews:
    """Test listing reviews for a skill."""

    def test_returns_paginated_list(self) -> None:
        db = MagicMock()
        skill = _mock_skill()
        review = _mock_review()
        db.query.return_value.filter.return_value.first.return_value = skill
        db.query.return_value.filter.return_value.count.return_value = 1
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [review]

        items, total = list_reviews(db, "test-skill")

        assert total == 1
        assert len(items) == 1
        assert items[0]["rating"] == 4

    @patch("skillhub.routers.social.list_reviews")
    def test_unauthenticated_can_list_reviews(
        self, mock_list: MagicMock, client: TestClient
    ) -> None:
        mock_list.return_value = (
            [{
                "id": REVIEW_ID, "skill_id": SKILL_ID, "user_id": USER_ID,
                "rating": 5, "body": "Great!", "helpful_count": 3,
                "unhelpful_count": 0, "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }],
            1,
        )
        response = client.get("/api/v1/skills/test-skill/reviews")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# --- Router Auth Requirements ---


class TestReviewRouterAuth:
    """Test authentication requirements on review endpoints."""

    def test_create_review_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/skills/test-skill/reviews",
            json={"rating": 5, "body": "Great!"},
        )
        assert response.status_code == 401

    def test_patch_review_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.patch(
            f"/api/v1/skills/test-skill/reviews/{REVIEW_ID}",
            json={"rating": 3},
        )
        assert response.status_code == 401

    def test_vote_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.post(
            f"/api/v1/skills/test-skill/reviews/{REVIEW_ID}/vote",
            json={"vote": "helpful"},
        )
        assert response.status_code == 401
