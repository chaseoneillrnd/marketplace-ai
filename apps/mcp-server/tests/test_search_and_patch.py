"""Tests for MCP search tool filter params (#16) and API client PATCH method (#19)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from skillhub_mcp.api_client import APIClient
from skillhub_mcp.tools.search import search_skills


def _mock_browse_response(items: list[dict[str, Any]] | None = None) -> httpx.Response:
    if items is None:
        items = [
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
        ]
    body = {
        "items": items,
        "page": 1,
        "per_page": 20,
        "total": len(items),
        "has_more": False,
    }
    return httpx.Response(status_code=200, json=body)


# --- #16: MCP Search Tool Filter Params ---


class TestSearchToolFilterParams:
    """Test that search_skills passes all filter params to the API client."""

    @pytest.mark.anyio
    async def test_search_passes_install_method(self) -> None:
        client = APIClient(base_url="http://testserver")
        client.get = AsyncMock(return_value=_mock_browse_response())  # type: ignore[assignment]

        result = await search_skills(
            install_method="mcp",
            api_client=client,
        )

        client.get.assert_called_once()
        call_params = client.get.call_args.kwargs.get("params") or client.get.call_args[1].get("params")
        assert call_params["install_method"] == "mcp"

    @pytest.mark.anyio
    async def test_search_passes_verified_flag(self) -> None:
        client = APIClient(base_url="http://testserver")
        client.get = AsyncMock(return_value=_mock_browse_response())  # type: ignore[assignment]

        result = await search_skills(
            verified=True,
            api_client=client,
        )

        call_params = client.get.call_args.kwargs.get("params") or client.get.call_args[1].get("params")
        assert call_params["verified"] is True

    @pytest.mark.anyio
    async def test_search_passes_featured_flag(self) -> None:
        client = APIClient(base_url="http://testserver")
        client.get = AsyncMock(return_value=_mock_browse_response())  # type: ignore[assignment]

        result = await search_skills(
            featured=True,
            api_client=client,
        )

        call_params = client.get.call_args.kwargs.get("params") or client.get.call_args[1].get("params")
        assert call_params["featured"] is True

    @pytest.mark.anyio
    async def test_search_passes_pagination(self) -> None:
        client = APIClient(base_url="http://testserver")
        client.get = AsyncMock(return_value=_mock_browse_response())  # type: ignore[assignment]

        result = await search_skills(
            page=3,
            per_page=10,
            api_client=client,
        )

        call_params = client.get.call_args.kwargs.get("params") or client.get.call_args[1].get("params")
        assert call_params["page"] == 3
        assert call_params["per_page"] == 10

    @pytest.mark.anyio
    async def test_search_passes_all_params_together(self) -> None:
        client = APIClient(base_url="http://testserver")
        client.get = AsyncMock(return_value=_mock_browse_response())  # type: ignore[assignment]

        result = await search_skills(
            query="review",
            category="code-review",
            divisions=["Engineering Org"],
            sort="popular",
            install_method="claude-code",
            verified=True,
            featured=False,
            page=2,
            per_page=5,
            api_client=client,
        )

        call_params = client.get.call_args.kwargs.get("params") or client.get.call_args[1].get("params")
        assert call_params["q"] == "review"
        assert call_params["category"] == "code-review"
        assert call_params["divisions"] == ["Engineering Org"]
        assert call_params["sort"] == "popular"
        assert call_params["install_method"] == "claude-code"
        assert call_params["verified"] is True
        assert call_params["featured"] is False
        assert call_params["page"] == 2
        assert call_params["per_page"] == 5

    @pytest.mark.anyio
    async def test_search_omits_none_params(self) -> None:
        """None-valued optional params should NOT appear in the request params."""
        client = APIClient(base_url="http://testserver")
        client.get = AsyncMock(return_value=_mock_browse_response())  # type: ignore[assignment]

        result = await search_skills(api_client=client)

        call_params = client.get.call_args.kwargs.get("params") or client.get.call_args[1].get("params")
        assert "q" not in call_params
        assert "category" not in call_params
        assert "install_method" not in call_params
        assert "verified" not in call_params
        assert "featured" not in call_params
        # page and per_page should always be present
        assert call_params["page"] == 1
        assert call_params["per_page"] == 20


# --- #19: MCP API Client PATCH Method ---


class TestAPIClientPatch:
    """Test the PATCH method on APIClient."""

    @pytest.mark.anyio
    async def test_patch_method_exists(self) -> None:
        """APIClient has a patch method."""
        client = APIClient(base_url="http://testserver", token="test-token")
        assert hasattr(client, "patch")
        assert callable(client.patch)

    @pytest.mark.anyio
    async def test_patch_sends_request(self) -> None:
        """PATCH method sends a PATCH request with JSON body via mocked client."""
        client = APIClient(base_url="http://testserver", token="test-token")
        mock_response = httpx.Response(
            status_code=200,
            json={"id": "123", "role": "admin"},
        )
        client.patch = AsyncMock(return_value=mock_response)  # type: ignore[assignment]

        response = await client.patch("/api/v1/admin/users/123", json={"role": "admin"})
        assert response.status_code == 200
        assert response.json() == {"id": "123", "role": "admin"}

    @pytest.mark.anyio
    async def test_patch_follows_same_pattern_as_post(self) -> None:
        """PATCH method signature matches post (path + json kwargs)."""
        import inspect

        client = APIClient(base_url="http://testserver")
        post_sig = inspect.signature(client.post)
        patch_sig = inspect.signature(client.patch)

        post_params = list(post_sig.parameters.keys())
        patch_params = list(patch_sig.parameters.keys())
        assert post_params == patch_params

    @pytest.mark.anyio
    async def test_patch_includes_auth_in_headers(self) -> None:
        """PATCH uses the same _headers() method that includes auth token."""
        client = APIClient(base_url="http://testserver", token="my-bearer-token")
        headers = client._headers()
        assert headers["Authorization"] == "Bearer my-bearer-token"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.anyio
    async def test_patch_no_auth_when_no_token(self) -> None:
        """Without a token, Authorization header is absent."""
        client = APIClient(base_url="http://testserver")
        headers = client._headers()
        assert "Authorization" not in headers
