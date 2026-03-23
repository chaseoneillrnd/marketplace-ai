"""Comprehensive tests for MCP server tools — install, search, update, fork, submit, error handling."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from skillhub_mcp.config import MCPSettings
from skillhub_mcp.tools.fork import fork_skill
from skillhub_mcp.tools.install import install_skill
from skillhub_mcp.tools.search import search_skills
from skillhub_mcp.tools.submit import submit_skill
from skillhub_mcp.tools.update import update_skill


def _write_installed_skill(skills_dir: str, slug: str, version: str, content: str = "") -> Path:
    """Write a SKILL.md with frontmatter version to the skills dir."""
    skill_dir = Path(skills_dir) / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    md_content = f"---\nversion: {version}\n---\n{content or f'# {slug}'}"
    skill_path.write_text(md_content)
    return skill_path


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


def _mock_version_response(
    slug: str = "pr-review-assistant",
    version: str = "2.3.1",
    divisions: list[str] | None = None,
    content: str = "# PR Review Assistant\n\nHelps review PRs.",
) -> httpx.Response:
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
    return httpx.Response(status_code=200, json={"success": True})


def _mock_404_response(url: str = "http://testserver/api/v1/skills/unknown") -> httpx.Response:
    request = httpx.Request("GET", url)
    return httpx.Response(status_code=404, json={"detail": "Not found"}, request=request)


# --- Install Tool with Division Enforcement ---


class TestInstallWithDivisionEnforcement:
    """Test install_skill MCP tool with division checks."""

    @pytest.mark.asyncio()
    async def test_install_authorized_division_writes_file(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        mock_api_client.get = AsyncMock(return_value=_mock_version_response())
        mock_api_client.post = AsyncMock(return_value=_mock_install_response())

        result = await install_skill(
            slug="pr-review-assistant",
            version="latest",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["success"] is True
        assert result["version"] == "2.3.1"
        skill_path = Path(test_settings.skills_dir) / "pr-review-assistant" / "SKILL.md"
        assert skill_path.exists()

    @pytest.mark.asyncio()
    async def test_install_unauthorized_division_returns_restricted(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        mock_api_client.get = AsyncMock(
            return_value=_mock_version_response(divisions=["Sales Org"])
        )

        result = await install_skill(
            slug="sales-skill",
            version="latest",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["success"] is False
        assert result["error"] == "division_restricted"
        skill_path = Path(test_settings.skills_dir) / "sales-skill" / "SKILL.md"
        assert not skill_path.exists()

    @pytest.mark.asyncio()
    async def test_install_unknown_slug_returns_not_found(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
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
    async def test_install_latest_resolves_version(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
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
    async def test_install_no_division_in_response_succeeds(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """Skills with no division restrictions allow any user."""
        mock_api_client.get = AsyncMock(
            return_value=_mock_version_response(divisions=[])
        )
        mock_api_client.post = AsyncMock(return_value=_mock_install_response())

        result = await install_skill(
            slug="open-skill",
            version="latest",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Any Division"},
        )

        assert result["success"] is True


# --- Search Tool ---


class TestSearchSkillsComprehensive:
    """Test search_skills MCP tool with query parameters."""

    @pytest.mark.asyncio()
    async def test_search_returns_items(self, mock_api_client: Any) -> None:
        mock_api_client.get = AsyncMock(return_value=_mock_browse_response())

        result = await search_skills(query="review", api_client=mock_api_client)

        assert len(result["items"]) == 1
        assert result["items"][0]["slug"] == "pr-review-assistant"

    @pytest.mark.asyncio()
    async def test_search_passes_all_params(self, mock_api_client: Any) -> None:
        mock_api_client.get = AsyncMock(return_value=_mock_browse_response())

        await search_skills(
            query="test",
            category="testing",
            divisions=["Engineering Org"],
            sort="installs",
            api_client=mock_api_client,
        )

        call_args = mock_api_client.get.call_args
        params = call_args.kwargs.get("params") or call_args[1].get("params", {})
        assert params["q"] == "test"
        assert params["category"] == "testing"
        assert params["sort"] == "installs"

    @pytest.mark.asyncio()
    async def test_search_empty_results(self, mock_api_client: Any) -> None:
        empty = httpx.Response(
            status_code=200,
            json={"items": [], "page": 1, "per_page": 20, "total": 0, "has_more": False},
        )
        mock_api_client.get = AsyncMock(return_value=empty)

        result = await search_skills(query="nonexistent", api_client=mock_api_client)

        assert result["items"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio()
    async def test_search_api_error_returns_error(self, mock_api_client: Any) -> None:
        mock_api_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error",
                request=httpx.Request("GET", "http://testserver/api/v1/skills"),
                response=httpx.Response(
                    status_code=500,
                    json={"detail": "Internal error"},
                    request=httpx.Request("GET", "http://testserver/api/v1/skills"),
                ),
            )
        )

        result = await search_skills(query="test", api_client=mock_api_client)

        assert result.get("success") is False or result.get("error") is not None


# --- Update Tool Version Detection ---


class TestUpdateSkillVersionDetection:
    """Test update_skill detects version changes."""

    @pytest.mark.asyncio()
    async def test_update_stale_version(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
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
    async def test_update_already_current(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
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
    async def test_update_not_installed(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        result = await update_skill(
            slug="not-installed",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["success"] is False
        assert result["error"] == "not_installed"

    @pytest.mark.asyncio()
    async def test_update_division_restricted(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """Update blocked if new version restricts user's division."""
        _write_installed_skill(test_settings.skills_dir, "sales-skill", "1.0.0")
        mock_api_client.get = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={
                    "slug": "sales-skill",
                    "version": "2.0.0",
                    "content": "# Sales Skill v2",
                    "divisions": ["Sales Org"],
                },
            )
        )

        result = await update_skill(
            slug="sales-skill",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["success"] is False
        assert result["error"] == "division_restricted"

    @pytest.mark.asyncio()
    async def test_update_api_404(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        _write_installed_skill(test_settings.skills_dir, "deleted-skill", "1.0.0")
        mock_api_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("GET", "http://testserver/api/v1/skills/deleted-skill/versions/latest"),
                response=_mock_404_response("http://testserver/api/v1/skills/deleted-skill/versions/latest"),
            )
        )

        result = await update_skill(
            slug="deleted-skill",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result["success"] is False
        assert result["error"] == "not_found"


# --- Fork Tool ---


class TestForkSkillComprehensive:
    """Test fork_skill MCP tool API delegation."""

    @pytest.mark.asyncio()
    async def test_fork_returns_success(self, mock_api_client: Any) -> None:
        mock_api_client.post = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={"success": True, "new_slug": "my-fork"},
            )
        )

        result = await fork_skill(slug="original-skill", api_client=mock_api_client)

        assert result["success"] is True
        assert result["new_slug"] == "my-fork"

    @pytest.mark.asyncio()
    async def test_fork_calls_correct_endpoint(self, mock_api_client: Any) -> None:
        mock_api_client.post = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={"success": True, "new_slug": "forked"},
            )
        )

        await fork_skill(slug="my-skill", api_client=mock_api_client)

        mock_api_client.post.assert_called_once_with("/api/v1/skills/my-skill/fork")

    @pytest.mark.asyncio()
    async def test_fork_api_403_returns_error(self, mock_api_client: Any) -> None:
        mock_api_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Forbidden",
                request=httpx.Request("POST", "http://testserver/api/v1/skills/locked/fork"),
                response=httpx.Response(
                    status_code=403,
                    json={"detail": "Forbidden"},
                    request=httpx.Request("POST", "http://testserver/api/v1/skills/locked/fork"),
                ),
            )
        )

        result = await fork_skill(slug="locked", api_client=mock_api_client)

        assert result["success"] is False


# --- Submit Tool ---


class TestSubmitSkillComprehensive:
    """Test submit_skill MCP tool with validation."""

    @pytest.mark.asyncio()
    async def test_submit_reads_file_and_posts(self, mock_api_client: Any, tmp_path: Any) -> None:
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: My Skill\ncategory: testing\nshort_desc: A test skill\n---\n# My Skill\n\nContent.")

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
            declared_divisions=["engineering"],
            api_client=mock_api_client,
        )

        assert result["submission_id"] == "sub-123"
        assert result["status"] == "pending_review"

    @pytest.mark.asyncio()
    async def test_submit_file_not_found(self, mock_api_client: Any) -> None:
        result = await submit_skill(
            skill_md_path="/nonexistent/SKILL.md",
            declared_divisions=["engineering"],
            api_client=mock_api_client,
        )

        assert result["success"] is False
        assert result["error"] == "file_not_found"

    @pytest.mark.asyncio()
    async def test_submit_sends_content(self, mock_api_client: Any, tmp_path: Any) -> None:
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: Test Skill\ncategory: testing\nshort_desc: A test\n---\n# Test Skill\n\nTest content.")

        mock_api_client.post = AsyncMock(
            return_value=httpx.Response(
                status_code=200,
                json={"submission_id": "sub-456", "display_id": "SUB-002", "status": "pending_review"},
            )
        )

        await submit_skill(skill_md_path=str(skill_file), declared_divisions=["engineering"], api_client=mock_api_client)

        call_args = mock_api_client.post.call_args
        posted_json = call_args.kwargs.get("json") or call_args[1].get("json", {})
        assert "# Test Skill" in posted_json["content"]

    @pytest.mark.asyncio()
    async def test_submit_api_error(self, mock_api_client: Any, tmp_path: Any) -> None:
        """API failure during submit returns error."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: Test\ncategory: testing\n---\n# Test\n\nContent.")

        mock_api_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error",
                request=httpx.Request("POST", "http://testserver/api/v1/submissions"),
                response=httpx.Response(
                    status_code=500,
                    json={"detail": "Internal error"},
                    request=httpx.Request("POST", "http://testserver/api/v1/submissions"),
                ),
            )
        )

        result = await submit_skill(
            skill_md_path=str(skill_file),
            declared_divisions=["engineering"],
            api_client=mock_api_client,
        )

        assert result.get("success") is False or result.get("error") is not None


# --- Error Handling for API Timeouts ---


class TestErrorHandling:
    """Test timeout and network error handling."""

    @pytest.mark.asyncio()
    async def test_install_api_timeout(
        self, test_settings: MCPSettings, mock_api_client: Any
    ) -> None:
        """API timeout during install returns error."""
        mock_api_client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Connection timed out")
        )

        result = await install_skill(
            slug="timeout-skill",
            version="latest",
            settings=test_settings,
            api_client=mock_api_client,
            user_claims={"division": "Engineering Org"},
        )

        assert result.get("success") is False or result.get("error") is not None

    @pytest.mark.asyncio()
    async def test_search_api_timeout(self, mock_api_client: Any) -> None:
        """API timeout during search returns error."""
        mock_api_client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Connection timed out")
        )

        result = await search_skills(query="test", api_client=mock_api_client)

        assert result.get("success") is False or result.get("error") is not None
