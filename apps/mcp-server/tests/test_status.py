"""Tests for get_submission_status MCP tool."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from skillhub_mcp.tools.status import get_submission_status


class TestGetSubmissionStatus:
    """Tests for the get_submission_status tool function."""

    @pytest.mark.asyncio()
    async def test_status_returns_submission(self, mock_api_client: Any) -> None:
        """get_submission_status returns submission details."""
        mock_api_client.get = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={
                    "id": "sub-123",
                    "display_id": "SUB-001",
                    "status": "approved",
                    "skill_name": "My Skill",
                    "submitted_at": "2026-03-20T10:00:00Z",
                },
            )
        )

        result = await get_submission_status(submission_id="sub-123", api_client=mock_api_client)

        assert result["id"] == "sub-123"
        assert result["status"] == "approved"

    @pytest.mark.asyncio()
    async def test_status_not_found(self, mock_api_client: Any) -> None:
        """get_submission_status returns error for unknown ID."""
        mock_api_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("GET", "http://testserver/api/v1/submissions/unknown"),
                response=httpx.Response(
                    status_code=404,
                    json={"detail": "Not found"},
                    request=httpx.Request("GET", "http://testserver/api/v1/submissions/unknown"),
                ),
            )
        )

        result = await get_submission_status(submission_id="unknown", api_client=mock_api_client)

        assert result["success"] is False
        assert result["error"] == "not_found"
