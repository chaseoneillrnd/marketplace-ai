"""Tests for the app factory."""

from __future__ import annotations

from fastapi import FastAPI

from skillhub.config import Settings
from skillhub.main import create_app


def test_create_app_returns_fastapi_instance() -> None:
    settings = Settings(
        database_url="sqlite:///:memory:",
        jwt_secret="test",
    )
    application = create_app(settings=settings)
    assert isinstance(application, FastAPI)
    assert application.title == settings.app_name
    assert application.version == settings.app_version
