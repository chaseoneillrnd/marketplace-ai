"""Tests for install_skill MCP tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from skillhub_mcp.config import MCPSettings
from skillhub_mcp.tools.install import install_skill


def _mock_version_response(
    slug: str = "pr-review-assistant",
    version: str = "2.3.1",
    divisions: list[str] | None = None,
    content: str = "# PR Review Assistant\n\nHelps review PRs.",
) -> httpx.Response:
    """Build a fake response for GET /api/v1/skills/{slug}/versions/{version}."""
    if divisions is None:
        divisions = ["Engineering Org"]
    body = {
        "slug": slug,
        "version": version,
        "divisions": divisions,
        "content": content,
        "name": slug.replace("-", " ").title(),
    }
    return httpx.Response(status_code=200, json=body)


def _mock_install_response() -> httpx.Response:
    """Build a fake response for POST /api/v1/skills/{slug}/install."""
    return httpx.Response(status_code=200, json={"success": True})


def _mock_404_response() -> httpx.Response:
    """Build a fake 404 response."""
    request = httpx.Request("GET", "http://testserver/api/v1/skills/unknown/versions/latest")
    return httpx.Response(status_code=404, json={"detail": "Not found"}, request=request)


class TestInstallSkill:
    """Tests for the install_skill tool function."""

    @pytest.mark.asyncio()
    async def test_install_with_valid_division_writes_skill_md(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """install_skill with valid division writes SKILL.md to correct path."""
        mock_api_client.get = AsyncMock(return_value=_mock_version_response())
        mock_api_client.post = AsyncMock(return_value=_mock_install_response())

        token_payload = {"division": "Engineering Org"}
        result = await install_skill(
            slug="pr-review-assistant",
            version="latest",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims=token_payload,
        )

        assert result["success"] is True
        assert result["version"] == "2.3.1"
        skill_path = Path(test_settings.skills_dir) / "pr-review-assistant" / "SKILL.md"
        assert skill_path.exists()
        assert "PR Review Assistant" in skill_path.read_text()

    @pytest.mark.asyncio()
    async def test_install_with_invalid_division_returns_restricted(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """install_skill with wrong division returns division_restricted error."""
        mock_api_client.get = AsyncMock(
            return_value=_mock_version_response(divisions=["Sales Org"])
        )

        token_payload = {"division": "Engineering Org"}
        result = await install_skill(
            slug="sales-only-skill",
            version="latest",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims=token_payload,
        )

        assert result["success"] is False
        assert result["error"] == "division_restricted"
        # SKILL.md must NOT be written
        skill_path = Path(test_settings.skills_dir) / "sales-only-skill" / "SKILL.md"
        assert not skill_path.exists()

    @pytest.mark.asyncio()
    async def test_install_with_unknown_slug_returns_error(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """install_skill with unknown slug returns not_found error."""
        mock_api_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("GET", "http://testserver/api/v1/skills/unknown/versions/latest"),
                response=_mock_404_response(),
            )
        )

        result = await install_skill(
            slug="unknown-skill",
            version="latest",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["success"] is False
        assert result["error"] == "not_found"

    @pytest.mark.asyncio()
    async def test_install_latest_resolves_to_current_version(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """install_skill 'latest' resolves to the current version number."""
        mock_api_client.get = AsyncMock(
            return_value=_mock_version_response(version="3.0.0")
        )
        mock_api_client.post = AsyncMock(return_value=_mock_install_response())

        result = await install_skill(
            slug="pr-review-assistant",
            version="latest",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["success"] is True
        assert result["version"] == "3.0.0"

    @pytest.mark.asyncio()
    async def test_install_does_not_write_skill_md_on_division_failure(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """Division check must fail before any file write occurs."""
        mock_api_client.get = AsyncMock(
            return_value=_mock_version_response(divisions=["Finance Org"])
        )

        result = await install_skill(
            slug="finance-skill",
            version="1.0.0",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["success"] is False
        skill_dir = Path(test_settings.skills_dir) / "finance-skill"
        assert not skill_dir.exists()
