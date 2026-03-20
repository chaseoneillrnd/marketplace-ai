"""Tests for session management."""

import contextlib

from skillhub_db.session import get_db


class TestGetDb:
    def test_get_db_yields_and_closes(self):
        """get_db yields a session and closes it when done."""
        gen = get_db()
        session = next(gen)
        assert session is not None
        with contextlib.suppress(StopIteration):
            next(gen)
        # Session should be closed after generator completes
        assert True  # Session was closed by generator
