"""Tests for get_skill MCP tool."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from skillhub_mcp.tools.get_skill import get_skill


def _mock_skill_detail_response() -> httpx.Response:
    """Build a fake response for GET /api/v1/skills/{slug}/versions/{version}."""
    body = {
        "slug": "pr-review-assistant",
        "name": "PR Review Assistant",
        "short_desc": "Helps review PRs",
        "content": "# PR Review Assistant\n\nFull content here.",
        "version": "2.3.1",
        "divisions": ["Engineering Org"],
        "category": "code-review",
        "install_count": 42,
    }
    return httpx.Response(status_code=200, json=body)


class TestGetSkill:
    """Tests for the get_skill tool function."""

    @pytest.mark.asyncio()
    async def test_get_skill_returns_detail(self, mock_api_client: Any) -> None:
        """get_skill returns full skill detail."""
        mock_api_client.get = AsyncMock(return_value=_mock_skill_detail_response())

        result = await get_skill(slug="pr-review-assistant", api_client=mock_api_client)

        assert result["slug"] == "pr-review-assistant"
        assert result["version"] == "2.3.1"
        assert "content" in result

    @pytest.mark.asyncio()
    async def test_get_skill_with_specific_version(self, mock_api_client: Any) -> None:
        """get_skill passes the version to the API."""
        mock_api_client.get = AsyncMock(return_value=_mock_skill_detail_response())

        await get_skill(slug="pr-review-assistant", version="2.3.1", api_client=mock_api_client)

        call_args = mock_api_client.get.call_args
        assert "/versions/2.3.1" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_get_skill_not_found(self, mock_api_client: Any) -> None:
        """get_skill returns error for unknown slug."""
        mock_api_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("GET", "http://testserver/api/v1/skills/unknown/versions/latest"),
                response=httpx.Response(
                    status_code=404,
                    json={"detail": "Not found"},
                    request=httpx.Request("GET", "http://testserver/api/v1/skills/unknown/versions/latest"),
                ),
            )
        )

        result = await get_skill(slug="unknown", api_client=mock_api_client)

        assert result["success"] is False
        assert result["error"] == "not_found"
