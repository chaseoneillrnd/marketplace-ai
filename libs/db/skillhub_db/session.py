"""Database session management."""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://skillhub:skillhub@localhost:5433/skillhub")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, closing it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
