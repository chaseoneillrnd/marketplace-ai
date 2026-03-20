"""Shared test fixtures for db tests."""

import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# Import all models to register them with metadata
import skillhub_db.models  # noqa: F401
from skillhub_db.base import Base


@pytest.fixture()
def engine():
    """Create an in-memory SQLite engine for testing."""
    eng = create_engine("sqlite:///:memory:")

    # Enable foreign key support in SQLite
    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def db(engine) -> Generator[Session, None, None]:
    """Yield a test database session."""
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def division(db: Session):
    """Create a test division."""
    from skillhub_db.models.division import Division

    div = Division(slug="engineering-org", name="Engineering Org", color="#3B82F6")
    db.add(div)
    db.commit()
    return div


@pytest.fixture()
def category(db: Session):
    """Create a test category."""
    from skillhub_db.models.skill import Category

    cat = Category(slug="engineering", name="Engineering", sort_order=1)
    db.add(cat)
    db.commit()
    return cat


@pytest.fixture()
def user(db: Session, division):
    """Create a test user."""
    from skillhub_db.models.user import User

    u = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="test@acme.com",
        username="test",
        name="Test User",
        division="engineering-org",
        role="Senior Engineer",
    )
    db.add(u)
    db.commit()
    return u


@pytest.fixture()
def skill(db: Session, user, category):
    """Create a test skill."""
    from skillhub_db.models.skill import Skill

    s = Skill(
        slug="pr-review-assistant",
        name="PR Review Assistant",
        short_desc="AI-powered code review",
        category="engineering",
        author_id=user.id,
    )
    db.add(s)
    db.commit()
    return s
