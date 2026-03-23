"""Tests for the seed script."""

import sys
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from skillhub_db.models.division import Division
from skillhub_db.models.flags import FeatureFlag
from skillhub_db.models.skill import Category
from skillhub_db.models.user import User

# Make seed_data importable from the scripts directory
_scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from seed_data import CATEGORIES, DIVISIONS, FEATURE_FLAGS, SEED_USERS


def _run_seed(db: Session) -> None:
    """Run seed logic using the test session (mirrors seed.py logic)."""
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

    for u in SEED_USERS:
        uid = uuid.UUID(u["id"])
        existing_user = db.get(User, uid)
        if not existing_user:
            db.add(
                User(
                    id=uid,
                    email=u["email"],
                    username=u["username"],
                    name=u["name"],
                    division=u["division"],
                    role=u["role"],
                )
            )
    db.commit()


# First seed user is the "test" user
_TEST_USER_ID = SEED_USERS[0]["id"]


class TestSeed:
    def test_seed_creates_all_divisions(self, db: Session):
        _run_seed(db)
        divs = db.query(Division).all()
        assert len(divs) == len(DIVISIONS)

    def test_seed_creates_all_categories(self, db: Session):
        _run_seed(db)
        cats = db.query(Category).all()
        assert len(cats) == len(CATEGORIES)

    def test_seed_creates_all_feature_flags(self, db: Session):
        _run_seed(db)
        flags = db.query(FeatureFlag).all()
        assert len(flags) == len(FEATURE_FLAGS)

    def test_seed_creates_stub_user(self, db: Session):
        _run_seed(db)
        user = db.get(User, uuid.UUID(_TEST_USER_ID))
        assert user is not None
        assert user.email == "test@acme.com"
        assert user.division == "engineering-org"

    def test_seed_idempotent(self, db: Session):
        """Running seed twice should not raise errors."""
        _run_seed(db)
        _run_seed(db)
        divs = db.query(Division).all()
        assert len(divs) == len(DIVISIONS)
