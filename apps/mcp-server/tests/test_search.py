"""Tests for search_skills MCP tool."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from skillhub_mcp.tools.search import search_skills


def _mock_browse_response() -> httpx.Response:
    """Build a fake response for GET /api/v1/skills."""
    body = {
        "items": [
            {
                "slug": "pr-review-assistant",
                "name": "PR Review Assistant",
                "short_desc": "Helps review PRs",
                "category": "code-review",
                "divisions": ["Engineering Org"],
                "version": "2.3.1",
                "install_count": 42,
                "avg_rating": "4.5",
            },
            {
                "slug": "test-writer",
                "name": "Test Writer",
                "short_desc": "Generates tests",
                "category": "testing",
                "divisions": ["Engineering Org"],
                "version": "1.0.0",
                "install_count": 15,
                "avg_rating": "4.2",
            },
        ],
        "page": 1,
        "per_page": 20,
        "total": 2,
        "has_more": False,
    }
    return httpx.Response(status_code=200, json=body)


class TestSearchSkills:
    """Tests for the search_skills tool function."""

    @pytest.mark.asyncio()
    async def test_search_returns_list_with_correct_fields(self, mock_api_client: Any) -> None:
        """search_skills returns list with expected skill summary fields."""
        mock_api_client.get = AsyncMock(return_value=_mock_browse_response())

        result = await search_skills(
            query="review",
            api_client=mock_api_client,
        )

        assert len(result["items"]) == 2
        first = result["items"][0]
        assert first["slug"] == "pr-review-assistant"
        assert first["name"] == "PR Review Assistant"
        assert "install_count" in first

    @pytest.mark.asyncio()
    async def test_search_passes_query_params(self, mock_api_client: Any) -> None:
        """search_skills passes query, category, divisions, sort to API."""
        mock_api_client.get = AsyncMock(return_value=_mock_browse_response())

        await search_skills(
            query="test",
            category="testing",
            divisions=["Engineering Org"],
            sort="installs",
            api_client=mock_api_client,
        )

        mock_api_client.get.assert_called_once()
        call_args = mock_api_client.get.call_args
        params = call_args.kwargs.get("params") or call_args[1].get("params", {})
        assert params["q"] == "test"
        assert params["category"] == "testing"
        assert params["sort"] == "installs"

    @pytest.mark.asyncio()
    async def test_search_empty_results(self, mock_api_client: Any) -> None:
        """search_skills returns empty list when no results."""
        empty_response = httpx.Response(
            status_code=200,
            json={"items": [], "page": 1, "per_page": 20, "total": 0, "has_more": False},
        )
        mock_api_client.get = AsyncMock(return_value=empty_response)

        result = await search_skills(query="nonexistent", api_client=mock_api_client)

        assert result["items"] == []
        assert result["total"] == 0
