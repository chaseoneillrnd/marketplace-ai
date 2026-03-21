"""Tests for MCP server tool registration."""

from __future__ import annotations

import pytest

from skillhub_mcp.server import mcp


class TestServerRegistration:
    """Tests that all 8 tools are registered on the MCP server."""

    @pytest.mark.asyncio()
    async def test_all_eight_tools_registered(self) -> None:
        """All 8 MCP tools should be registered."""
        tools = await mcp.list_tools()
        tool_names = {t.name for t in tools}

        expected = {
            "search_skills",
            "get_skill",
            "install_skill",
            "update_skill",
            "list_installed",
            "fork_skill",
            "submit_skill",
            "get_submission_status",
        }
        assert tool_names == expected

    @pytest.mark.asyncio()
    async def test_tool_count(self) -> None:
        """Exactly 8 tools should be registered."""
        tools = await mcp.list_tools()
        assert len(tools) == 8

    @pytest.mark.asyncio()
    async def test_install_skill_has_description(self) -> None:
        """install_skill tool should have a meaningful description."""
        tools = await mcp.list_tools()
        install_tool = next(t for t in tools if t.name == "install_skill")
        assert "division" in install_tool.description.lower()
