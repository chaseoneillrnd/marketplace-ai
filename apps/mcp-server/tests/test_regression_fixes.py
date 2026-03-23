"""Regression tests for MCP fixes: config, install path, submit payload."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from skillhub_mcp.config import MCPSettings
from skillhub_mcp.tools.submit import _parse_frontmatter, submit_skill


class TestMCPSettingsExtraIgnore:
    """Regression: MCPSettings crashed on extra env vars from .env."""

    def test_extra_env_vars_ignored(self) -> None:
        """MCPSettings should not crash when unknown env vars are present."""
        with patch.dict(os.environ, {
            "SKILLHUB_MCP_API_BASE_URL": "http://test:8000",
            "DATABASE_URL": "postgres://...",
            "REDIS_URL": "redis://...",
            "JWT_SECRET": "secret",
        }):
            settings = MCPSettings(_env_file=None)
            assert settings.api_base_url == "http://test:8000"

    def test_default_skills_dir_points_to_claude_skills(self) -> None:
        """Skills dir should be ~/.claude/skills, not ~/.local/share/claude/skills."""
        settings = MCPSettings(_env_file=None)
        expected = str(Path.home() / ".claude" / "skills")
        assert settings.skills_dir == expected

    def test_skills_dir_env_override(self) -> None:
        """SKILLHUB_MCP_SKILLS_DIR should override the default."""
        with patch.dict(os.environ, {"SKILLHUB_MCP_SKILLS_DIR": "/custom/path"}):
            settings = MCPSettings(_env_file=None)
            assert settings.skills_dir == "/custom/path"


class TestSubmitFrontmatterParsing:
    """Regression: submit_skill sent wrong payload (only content, no name/category)."""

    def test_parse_frontmatter_basic(self) -> None:
        content = '---\nname: My Skill\ncategory: engineering\nshort_desc: A great skill\n---\n# Content'
        result = _parse_frontmatter(content)
        assert result is not None
        assert result["name"] == "My Skill"
        assert result["category"] == "engineering"
        assert result["short_desc"] == "A great skill"

    def test_parse_frontmatter_with_list(self) -> None:
        content = '---\nname: Test\ntrigger_phrases: [review code, check code, lint code]\n---\n# X'
        result = _parse_frontmatter(content)
        assert result is not None
        assert result["trigger_phrases"] == ["review code", "check code", "lint code"]

    def test_parse_frontmatter_no_frontmatter(self) -> None:
        content = "# Just markdown\nNo frontmatter here."
        result = _parse_frontmatter(content)
        assert result is None

    def test_parse_frontmatter_unclosed(self) -> None:
        content = "---\nname: Test\n# No closing ---"
        result = _parse_frontmatter(content)
        assert result is None

    @pytest.mark.asyncio()
    async def test_submit_sends_complete_payload(self, tmp_path: Any) -> None:
        """submit_skill should send name, short_desc, category, content, declared_divisions."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: My Skill\ncategory: engineering\nshort_desc: A great skill\n---\n# Content"
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={"id": "sub-123", "status": "gate1_passed"},
            )
        )

        result = await submit_skill(
            skill_md_path=str(skill_file),
            declared_divisions=["engineering-org"],
            division_justification="Used by engineering",
            api_client=mock_client,
        )

        call_args = mock_client.post.call_args
        posted_json = call_args.kwargs.get("json") or call_args[1].get("json", {})

        assert posted_json["name"] == "My Skill"
        assert posted_json["category"] == "engineering"
        assert posted_json["short_desc"] == "A great skill"
        assert posted_json["declared_divisions"] == ["engineering-org"]
        assert posted_json["division_justification"] == "Used by engineering"
        assert "---" in posted_json["content"]

    @pytest.mark.asyncio()
    async def test_submit_missing_frontmatter_returns_error(self, tmp_path: Any) -> None:
        """submit_skill should error when SKILL.md has no frontmatter."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Just content\nNo frontmatter.")

        mock_client = AsyncMock()
        result = await submit_skill(
            skill_md_path=str(skill_file),
            declared_divisions=["engineering-org"],
            api_client=mock_client,
        )

        assert result["success"] is False
        assert result["error"] == "missing_frontmatter"

    @pytest.mark.asyncio()
    async def test_submit_missing_required_fields_returns_error(self, tmp_path: Any) -> None:
        """submit_skill should error when frontmatter lacks name or category."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nshort_desc: Only short desc\n---\n# Content")

        mock_client = AsyncMock()
        result = await submit_skill(
            skill_md_path=str(skill_file),
            declared_divisions=["engineering-org"],
            api_client=mock_client,
        )

        assert result["success"] is False
        assert result["error"] == "missing_frontmatter_fields"
        assert "name" in result["detail"]
        assert "category" in result["detail"]

    @pytest.mark.asyncio()
    async def test_submit_file_not_found(self) -> None:
        mock_client = AsyncMock()
        result = await submit_skill(
            skill_md_path="/nonexistent/SKILL.md",
            declared_divisions=["engineering-org"],
            api_client=mock_client,
        )
        assert result["success"] is False
        assert result["error"] == "file_not_found"
