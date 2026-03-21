"""Shared fixtures for MCP server tests."""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import AsyncMock

import jwt
import pytest

from skillhub_mcp.api_client import APIClient
from skillhub_mcp.config import MCPSettings

TEST_JWT_SECRET = "test-secret-for-mcp-tests"
TEST_JWT_ALGORITHM = "HS256"


def make_token(
    payload: dict[str, Any] | None = None,
    secret: str = TEST_JWT_SECRET,
    algorithm: str = TEST_JWT_ALGORITHM,
    expired: bool = False,
) -> str:
    """Generate a JWT for testing."""
    data: dict[str, Any] = payload or {
        "sub": "test-user-id",
        "user_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "username": "testuser",
        "division": "Engineering Org",
        "is_platform_team": False,
    }
    if expired:
        data["exp"] = int(time.time()) - 3600
    elif "exp" not in data:
        data["exp"] = int(time.time()) + 3600
    return jwt.encode(data, secret, algorithm=algorithm)


@pytest.fixture()
def test_settings(tmp_path: Any) -> MCPSettings:
    """Return MCP settings with a temp skills directory."""
    return MCPSettings(
        api_base_url="http://testserver",
        skills_dir=str(tmp_path / "skills"),
        host="127.0.0.1",
        port=8001,
        debug=True,
    )


@pytest.fixture()
def mock_api_client() -> APIClient:
    """Return an APIClient with mocked HTTP methods."""
    client = APIClient(base_url="http://testserver", token=make_token())
    client.get = AsyncMock()  # type: ignore[assignment]
    client.post = AsyncMock()  # type: ignore[assignment]
    return client
