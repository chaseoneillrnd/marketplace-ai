"""Database session management using raw SQLAlchemy scoped_session."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

if TYPE_CHECKING:
    from flask import Flask

    from skillhub_flask.config import AppConfig

logger = logging.getLogger(__name__)

_scoped_session: scoped_session[Session] | None = None


def init_db(app: Flask, config: AppConfig) -> None:
    """Initialize the database session factory and register teardown."""
    global _scoped_session  # noqa: PLW0603

    if config.session_factory is not None:
        # Test injection — wrap the provided factory in a scoped_session
        _scoped_session = scoped_session(
            sessionmaker(class_=Session),
        )
        # Override the session factory to use the injected one
        app.extensions["db_session_factory"] = config.session_factory
    else:
        engine = create_engine(
            config.settings.database_url,
            pool_pre_ping=True,
        )
        factory = sessionmaker(bind=engine, autocommit=False, autoflush=True)
        _scoped_session = scoped_session(factory)
        app.extensions["db_session_factory"] = None

    @app.teardown_appcontext
    def shutdown_session(exception: BaseException | None = None) -> None:
        if _scoped_session is not None:
            if exception:
                _scoped_session.rollback()
            _scoped_session.remove()


def get_db() -> Session:
    """Return a database session for the current request.

    If a test session_factory is configured on the app, use that.
    Otherwise, use the scoped_session.
    """
    from flask import current_app

    test_factory = current_app.extensions.get("db_session_factory")
    if test_factory is not None:
        return test_factory()

    if _scoped_session is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _scoped_session()
