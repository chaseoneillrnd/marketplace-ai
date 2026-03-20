"""Tests for Social domain models."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from skillhub_db.models.social import (
    Comment,
    Favorite,
    Follow,
    Fork,
    Install,
    Review,
    ReviewVote,
    VoteType,
)


class TestInstall:
    def test_install_creates(self, db: Session, skill, user):
        install = Install(
            skill_id=skill.id,
            user_id=user.id,
            version="1.0.0",
            method="claude-code",
        )
        db.add(install)
        db.commit()
        assert install.id is not None
        assert install.uninstalled_at is None


class TestFavorite:
    def test_favorite_composite_pk(self, db: Session, skill, user):
        fav = Favorite(user_id=user.id, skill_id=skill.id)
        db.add(fav)
        db.commit()
        assert fav.user_id == user.id
        assert fav.skill_id == skill.id


class TestFollow:
    def test_follow_composite_pk(self, db: Session, user, division):
        from skillhub_db.models.user import User

        user2 = User(
            email="bob@acme.com",
            username="bob",
            name="Bob",
            division="engineering-org",
            role="Eng",
        )
        db.add(user2)
        db.commit()
        follow = Follow(follower_id=user.id, followed_user_id=user2.id)
        db.add(follow)
        db.commit()
        assert follow.follower_id == user.id


class TestReview:
    def test_review_unique_constraint(self, db: Session, skill, user):
        r1 = Review(skill_id=skill.id, user_id=user.id, rating=5, body="Great skill!")
        db.add(r1)
        db.commit()

        r2 = Review(skill_id=skill.id, user_id=user.id, rating=3, body="Changed my mind")
        db.add(r2)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_review_defaults(self, db: Session, skill, user):
        r = Review(skill_id=skill.id, user_id=user.id, rating=4, body="Good")
        db.add(r)
        db.commit()
        assert r.helpful_count == 0
        assert r.unhelpful_count == 0


class TestReviewVote:
    def test_review_vote(self, db: Session, skill, user, division):
        r = Review(skill_id=skill.id, user_id=user.id, rating=5, body="test")
        db.add(r)
        db.commit()

        from skillhub_db.models.user import User

        voter = User(
            email="voter@acme.com",
            username="voter",
            name="Voter",
            division="engineering-org",
            role="Eng",
        )
        db.add(voter)
        db.commit()

        vote = ReviewVote(review_id=r.id, user_id=voter.id, vote=VoteType.HELPFUL)
        db.add(vote)
        db.commit()
        assert vote.vote == VoteType.HELPFUL


class TestComment:
    def test_comment_soft_delete(self, db: Session, skill, user):
        c = Comment(skill_id=skill.id, user_id=user.id, body="Nice skill")
        db.add(c)
        db.commit()
        assert c.deleted_at is None
        assert c.upvote_count == 0


class TestFork:
    def test_fork_creates(self, db: Session, skill, user, category):
        from skillhub_db.models.skill import Skill

        forked = Skill(
            slug="pr-review-fork",
            name="PR Review Fork",
            short_desc="Forked version",
            category="engineering",
            author_id=user.id,
        )
        db.add(forked)
        db.commit()

        fork = Fork(
            original_skill_id=skill.id,
            forked_skill_id=forked.id,
            forked_by=user.id,
            upstream_version_at_fork="1.0.0",
        )
        db.add(fork)
        db.commit()
        assert fork.id is not None
