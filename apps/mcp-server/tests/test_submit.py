"""Tests for submit_skill MCP tool."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from skillhub_mcp.tools.submit import submit_skill


class TestSubmitSkill:
    """Tests for the submit_skill tool function."""

    @pytest.mark.asyncio()
    async def test_submit_reads_file_and_posts(self, mock_api_client: Any, tmp_path: Any) -> None:
        """submit_skill reads local file and calls POST /api/v1/submissions."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: My Skill\ncategory: engineering\nshort_desc: A test skill\n---\n# My Skill\n\nContent here."
        )

        mock_api_client.post = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={
                    "id": "sub-123",
                    "display_id": "SUB-001",
                    "status": "gate1_passed",
                },
            )
        )

        result = await submit_skill(
            skill_md_path=str(skill_file),
            declared_divisions=["engineering-org"],
            division_justification="Used by engineers",
            api_client=mock_api_client,
        )

        assert result["id"] == "sub-123"
        assert result["display_id"] == "SUB-001"
        assert result["status"] == "gate1_passed"

    @pytest.mark.asyncio()
    async def test_submit_file_not_found(self, mock_api_client: Any) -> None:
        """submit_skill returns error when file doesn't exist."""
        result = await submit_skill(
            skill_md_path="/nonexistent/SKILL.md",
            declared_divisions=["engineering-org"],
            api_client=mock_api_client,
        )

        assert result["success"] is False
        assert result["error"] == "file_not_found"

    @pytest.mark.asyncio()
    async def test_submit_sends_complete_payload(self, mock_api_client: Any, tmp_path: Any) -> None:
        """submit_skill sends all required fields in the POST body."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: Test Skill\ncategory: data\nshort_desc: Analyzes data\n---\n# Test Skill\n\nThis is test content."
        )

        mock_api_client.post = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={"id": "sub-456", "display_id": "SUB-002", "status": "gate1_passed"},
            )
        )

        await submit_skill(
            skill_md_path=str(skill_file),
            declared_divisions=["data-org"],
            division_justification="Data team tool",
            api_client=mock_api_client,
        )

        call_args = mock_api_client.post.call_args
        posted_json = call_args.kwargs.get("json") or call_args[1].get("json", {})
        assert posted_json["name"] == "Test Skill"
        assert posted_json["category"] == "data"
        assert posted_json["short_desc"] == "Analyzes data"
        assert posted_json["declared_divisions"] == ["data-org"]
        assert posted_json["division_justification"] == "Data team tool"
        assert "# Test Skill" in posted_json["content"]
