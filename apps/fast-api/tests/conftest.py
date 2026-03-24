"""Shared test fixtures for SkillHub API tests."""

from __future__ import annotations

import time
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient

from skillhub.config import Settings
from skillhub.main import create_app

TEST_JWT_SECRET = "test-secret-for-unit-tests"
TEST_JWT_ALGORITHM = "HS256"


def _make_settings(**overrides: Any) -> Settings:
    """Create a Settings instance suitable for testing (no real DB needed)."""
    defaults: dict[str, Any] = {
        "app_name": "SkillHub-Test",
        "app_version": "0.0.1-test",
        "debug": True,
        "database_url": "sqlite:///:memory:",
        "jwt_secret": TEST_JWT_SECRET,
        "jwt_algorithm": TEST_JWT_ALGORITHM,
        "jwt_expire_minutes": 60,
        "stub_auth_enabled": True,
    }
    defaults.update(overrides)
    return Settings(**defaults)


@pytest.fixture()
def test_settings() -> Settings:
    """Return a test-oriented Settings object."""
    return _make_settings()


@pytest.fixture()
def app(test_settings: Settings) -> Any:
    """Return a FastAPI application wired with test settings."""
    return create_app(settings=test_settings)


@pytest.fixture()
def client(app: Any) -> TestClient:
    """Return a TestClient bound to the test app."""
    return TestClient(app)


def make_token(
    payload: dict[str, Any] | None = None,
    secret: str = TEST_JWT_SECRET,
    algorithm: str = TEST_JWT_ALGORITHM,
    expired: bool = False,
) -> str:
    """Generate a JWT for testing purposes."""
    data: dict[str, Any] = payload or {"sub": "test-user", "division": "engineering"}
    if expired:
        data["exp"] = int(time.time()) - 3600  # 1 hour in the past
    elif "exp" not in data:
        data["exp"] = int(time.time()) + 3600  # 1 hour in the future
    return jwt.encode(data, secret, algorithm=algorithm)
