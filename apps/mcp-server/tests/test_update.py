"""Tests for update_skill MCP tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from skillhub_mcp.config import MCPSettings
from skillhub_mcp.tools.update import update_skill


def _write_installed_skill(skills_dir: str, slug: str, version: str, content: str = "") -> Path:
    """Write a SKILL.md with frontmatter version to the skills dir."""
    skill_dir = Path(skills_dir) / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    md_content = f"---\nversion: {version}\n---\n{content or f'# {slug}'}"
    skill_path.write_text(md_content)
    return skill_path


class TestUpdateSkill:
    """Tests for the update_skill tool function."""

    @pytest.mark.asyncio()
    async def test_update_detects_stale_version(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """update_skill detects a stale installed version and updates it."""
        _write_installed_skill(test_settings.skills_dir, "pr-review", "1.0.0")
        mock_api_client.get = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={
                    "slug": "pr-review",
                    "version": "2.0.0",
                    "content": "# PR Review v2",
                    "divisions": ["Engineering Org"],
                },
            )
        )
        mock_api_client.post = AsyncMock(
            return_value=httpx.Response(status_code=200, json={"success": True})
        )

        result = await update_skill(
            slug="pr-review",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["updated"] is True
        assert result["from_version"] == "1.0.0"
        assert result["to_version"] == "2.0.0"

    @pytest.mark.asyncio()
    async def test_update_no_ops_when_current(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """update_skill does nothing when already at latest version."""
        _write_installed_skill(test_settings.skills_dir, "pr-review", "2.0.0")
        mock_api_client.get = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={
                    "slug": "pr-review",
                    "version": "2.0.0",
                    "content": "# PR Review v2",
                    "divisions": ["Engineering Org"],
                },
            )
        )

        result = await update_skill(
            slug="pr-review",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["updated"] is False

    @pytest.mark.asyncio()
    async def test_update_skill_not_installed(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """update_skill returns error if skill is not installed locally."""
        result = await update_skill(
            slug="not-installed",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["success"] is False
        assert result["error"] == "not_installed"
