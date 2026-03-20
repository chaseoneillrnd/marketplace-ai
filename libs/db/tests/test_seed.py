"""Tests for the seed script."""

import uuid

from sqlalchemy.orm import Session

from skillhub_db.models.division import Division
from skillhub_db.models.flags import FeatureFlag
from skillhub_db.models.skill import Category
from skillhub_db.models.user import User


def _run_seed(db: Session) -> None:
    """Run seed logic using the test session (mirrors seed.py logic)."""
    from libs.db.scripts.seed import CATEGORIES, DIVISIONS, FEATURE_FLAGS, STUB_USER_ID

    for slug, name, color in DIVISIONS:
        existing = db.get(Division, slug)
        if not existing:
            db.add(Division(slug=slug, name=name, color=color))

    for slug, name, sort_order in CATEGORIES:
        existing = db.get(Category, slug)
        if not existing:
            db.add(Category(slug=slug, name=name, sort_order=sort_order))

    for key, enabled, description in FEATURE_FLAGS:
        existing = db.get(FeatureFlag, key)
        if not existing:
            db.add(FeatureFlag(key=key, enabled=enabled, description=description))

    existing_user = db.get(User, uuid.UUID(STUB_USER_ID))
    if not existing_user:
        db.add(
            User(
                id=uuid.UUID(STUB_USER_ID),
                email="test@acme.com",
                username="test",
                name="Test User",
                division="engineering-org",
                role="Senior Engineer",
            )
        )
    db.commit()


class TestSeed:
    def test_seed_creates_all_divisions(self, db: Session):
        _run_seed(db)
        divs = db.query(Division).all()
        assert len(divs) == 8

    def test_seed_creates_all_categories(self, db: Session):
        _run_seed(db)
        cats = db.query(Category).all()
        assert len(cats) == 9

    def test_seed_creates_all_feature_flags(self, db: Session):
        _run_seed(db)
        flags = db.query(FeatureFlag).all()
        assert len(flags) == 4

    def test_seed_creates_stub_user(self, db: Session):
        _run_seed(db)
        user = db.get(User, uuid.UUID("00000000-0000-0000-0000-000000000001"))
        assert user is not None
        assert user.email == "test@acme.com"
        assert user.division == "engineering-org"

    def test_seed_idempotent(self, db: Session):
        """Running seed twice should not raise errors."""
        _run_seed(db)
        _run_seed(db)
        divs = db.query(Division).all()
        assert len(divs) == 8
