"""Tests for list_installed MCP tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from skillhub_mcp.config import MCPSettings
from skillhub_mcp.tools.list_installed import list_installed


def _write_skill(skills_dir: str, slug: str, version: str) -> None:
    """Write a SKILL.md with frontmatter to the skills directory."""
    skill_dir = Path(skills_dir) / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"---\nversion: {version}\n---\n# {slug}")


class TestListInstalled:
    """Tests for the list_installed tool function."""

    @pytest.mark.asyncio()
    async def test_list_installed_reads_filesystem(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """list_installed reads local skills directory and returns installed skills."""
        _write_skill(test_settings.skills_dir, "skill-a", "1.0.0")
        _write_skill(test_settings.skills_dir, "skill-b", "2.1.0")

        # Mock API responses for latest version checks
        async def mock_get(path: str, **kwargs: Any) -> httpx.Response:
            if "skill-a" in path:
                return httpx.Response(status_code=200, json={"version": "1.0.0"})
            return httpx.Response(status_code=200, json={"version": "3.0.0"})

        mock_api_client.get = AsyncMock(side_effect=mock_get)

        result = await list_installed(
            settings=test_settings,
            api_client=mock_api_client,
        )

        assert len(result) == 2
        slugs = {s["slug"] for s in result}
        assert slugs == {"skill-a", "skill-b"}

    @pytest.mark.asyncio()
    async def test_list_installed_detects_stale(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """list_installed marks stale skills correctly."""
        _write_skill(test_settings.skills_dir, "stale-skill", "1.0.0")

        mock_api_client.get = AsyncMock(
            return_value=httpx.Response(status_code=200, json={"version": "2.0.0"})
        )

        result = await list_installed(
            settings=test_settings,
            api_client=mock_api_client,
        )

        assert len(result) == 1
        assert result[0]["slug"] == "stale-skill"
        assert result[0]["stale"] is True
        assert result[0]["installed_version"] == "1.0.0"
        assert result[0]["latest_version"] == "2.0.0"

    @pytest.mark.asyncio()
    async def test_list_installed_empty_dir(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """list_installed returns empty list when no skills installed."""
        result = await list_installed(
            settings=test_settings,
            api_client=mock_api_client,
        )

        assert result == []
