"""Tests for fork_skill MCP tool."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from skillhub_mcp.tools.fork import fork_skill


class TestForkSkill:
    """Tests for the fork_skill tool function."""

    @pytest.mark.asyncio()
    async def test_fork_returns_success(self, mock_api_client: Any) -> None:
        """fork_skill returns success with new slug."""
        mock_api_client.post = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={"success": True, "new_slug": "pr-review-assistant-fork-1"},
            )
        )

        result = await fork_skill(slug="pr-review-assistant", api_client=mock_api_client)

        assert result["success"] is True
        assert result["new_slug"] == "pr-review-assistant-fork-1"

    @pytest.mark.asyncio()
    async def test_fork_passes_slug_to_api(self, mock_api_client: Any) -> None:
        """fork_skill calls POST /api/v1/skills/{slug}/fork."""
        mock_api_client.post = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={"success": True, "new_slug": "my-fork"},
            )
        )

        await fork_skill(slug="original-skill", api_client=mock_api_client)

        mock_api_client.post.assert_called_once_with("/api/v1/skills/original-skill/fork")

    @pytest.mark.asyncio()
    async def test_fork_api_error(self, mock_api_client: Any) -> None:
        """fork_skill returns error on API failure."""
        mock_api_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Forbidden",
                request=httpx.Request("POST", "http://testserver/api/v1/skills/locked/fork"),
                response=httpx.Response(
                    status_code=403,
                    json={"detail": "Forbidden"},
                    request=httpx.Request("POST", "http://testserver/api/v1/skills/locked/fork"),
                ),
            )
        )

        result = await fork_skill(slug="locked", api_client=mock_api_client)

        assert result["success"] is False
