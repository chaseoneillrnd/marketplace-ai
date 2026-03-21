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
        skill_file.write_text("---\nname: My Skill\n---\n# My Skill\n\nContent here.")

        mock_api_client.post = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={
                    "submission_id": "sub-123",
                    "display_id": "SUB-001",
                    "status": "pending_review",
                },
            )
        )

        result = await submit_skill(
            skill_md_path=str(skill_file),
            api_client=mock_api_client,
        )

        assert result["submission_id"] == "sub-123"
        assert result["display_id"] == "SUB-001"
        assert result["status"] == "pending_review"

    @pytest.mark.asyncio()
    async def test_submit_file_not_found(self, mock_api_client: Any) -> None:
        """submit_skill returns error when file doesn't exist."""
        result = await submit_skill(
            skill_md_path="/nonexistent/SKILL.md",
            api_client=mock_api_client,
        )

        assert result["success"] is False
        assert result["error"] == "file_not_found"

    @pytest.mark.asyncio()
    async def test_submit_sends_content_to_api(self, mock_api_client: Any, tmp_path: Any) -> None:
        """submit_skill sends the file content in the POST body."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Test Skill\n\nThis is test content.")

        mock_api_client.post = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={"submission_id": "sub-456", "display_id": "SUB-002", "status": "pending_review"},
            )
        )

        await submit_skill(skill_md_path=str(skill_file), api_client=mock_api_client)

        call_args = mock_api_client.post.call_args
        posted_json = call_args.kwargs.get("json") or call_args[1].get("json", {})
        assert "# Test Skill" in posted_json["content"]
