"""SkillHub MCP Server — exposes 9 tools for Claude Code skill management."""

from __future__ import annotations

import logging
from typing import Any

import jwt
from mcp.server.fastmcp import FastMCP

from skillhub_mcp.api_client import APIClient
from skillhub_mcp.config import MCPSettings
from skillhub_mcp.tools.fork import fork_skill as _fork_skill
from skillhub_mcp.tracing import setup_tracing
from skillhub_mcp.tools.get_skill import get_skill as _get_skill
from skillhub_mcp.tools.install import install_skill as _install_skill
from skillhub_mcp.tools.list_installed import list_installed as _list_installed
from skillhub_mcp.tools.search import search_skills as _search_skills
from skillhub_mcp.tools.status import get_submission_status as _get_submission_status
from skillhub_mcp.tools.submit import submit_skill as _submit_skill
from skillhub_mcp.tools.uninstall import uninstall_skill as _uninstall_skill
from skillhub_mcp.tools.update import update_skill as _update_skill

logger = logging.getLogger(__name__)

settings = MCPSettings()
tracer = setup_tracing(settings)

mcp = FastMCP(
    name="SkillHub",
    host=settings.host,
    port=settings.port,
    debug=settings.debug,
)


def _get_api_client(token: str | None = None) -> APIClient:
    """Create an API client with the given bearer token."""
    return APIClient(base_url=settings.api_base_url, token=token)


def _decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT without verification (the API will verify)."""
    return jwt.decode(token, options={"verify_signature": False})  # type: ignore[no-any-return]


# --- Tool 1: search_skills ---


@mcp.tool(
    name="search_skills",
    description="Search and browse skills in the SkillHub marketplace. "
    "Filter by query, category, divisions, sort order, install method, "
    "verified/featured status, and pagination.",
)
async def search_skills_tool(
    query: str | None = None,
    category: str | None = None,
    divisions: list[str] | None = None,
    sort: str | None = None,
    install_method: str | None = None,
    verified: bool | None = None,
    featured: bool | None = None,
    page: int = 1,
    per_page: int = 20,
    token: str | None = None,
) -> dict[str, Any]:
    """Search skills with optional filters."""
    client = _get_api_client(token)
    return await _search_skills(
        query=query,
        category=category,
        divisions=divisions,
        sort=sort,
        install_method=install_method,
        verified=verified,
        featured=featured,
        page=page,
        per_page=per_page,
        api_client=client,
    )


# --- Tool 2: get_skill ---


@mcp.tool(
    name="get_skill",
    description="Get full detail for a skill including content, versions, and metadata.",
)
async def get_skill_tool(
    slug: str,
    version: str = "latest",
    token: str | None = None,
) -> dict[str, Any]:
    """Get skill detail by slug and optional version."""
    client = _get_api_client(token)
    return await _get_skill(slug=slug, version=version, api_client=client)


# --- Tool 3: install_skill ---


@mcp.tool(
    name="install_skill",
    description="Install a skill from SkillHub to the local filesystem. "
    "Validates division access before writing SKILL.md.",
)
async def install_skill_tool(
    slug: str,
    version: str = "latest",
    token: str | None = None,
) -> dict[str, Any]:
    """Install a skill locally, enforcing division access."""
    client = _get_api_client(token)
    claims = _decode_token(token) if token else {}
    return await _install_skill(
        slug=slug,
        version=version,
        settings=settings,
        api_client=client,
        user_claims=claims,
    )


# --- Tool 4: update_skill ---


@mcp.tool(
    name="update_skill",
    description="Update an installed skill to the latest version. "
    "Compares local SKILL.md version to the API's current version.",
)
async def update_skill_tool(
    slug: str,
    token: str | None = None,
) -> dict[str, Any]:
    """Update a locally installed skill if a newer version exists."""
    client = _get_api_client(token)
    claims = _decode_token(token) if token else {}
    return await _update_skill(
        slug=slug,
        settings=settings,
        api_client=client,
        user_claims=claims,
    )


# --- Tool 5: uninstall_skill ---


@mcp.tool(
    name="uninstall_skill",
    description="Uninstall a skill by removing it from the local filesystem "
    "and recording the uninstall via the API.",
)
async def uninstall_skill_tool(
    slug: str,
    token: str | None = None,
) -> dict[str, Any]:
    """Uninstall a locally installed skill."""
    client = _get_api_client(token)
    return await _uninstall_skill(
        slug=slug,
        settings=settings,
        api_client=client,
    )


# --- Tool 6: list_installed ---


@mcp.tool(
    name="list_installed",
    description="List all locally installed skills with version info and stale flag.",
)
async def list_installed_tool(
    token: str | None = None,
) -> list[dict[str, Any]]:
    """List installed skills from the local filesystem."""
    client = _get_api_client(token)
    return await _list_installed(settings=settings, api_client=client)


# --- Tool 6: fork_skill ---


@mcp.tool(
    name="fork_skill",
    description="Fork a skill to your namespace for customization.",
)
async def fork_skill_tool(
    slug: str,
    token: str | None = None,
) -> dict[str, Any]:
    """Fork a skill via the API."""
    client = _get_api_client(token)
    return await _fork_skill(slug=slug, api_client=client)


# --- Tool 7: submit_skill ---


@mcp.tool(
    name="submit_skill",
    description="Submit a local SKILL.md file for review and publication. "
    "Parses frontmatter for name/category/short_desc. "
    "Requires declared_divisions listing which org divisions should access the skill.",
)
async def submit_skill_tool(
    skill_md_path: str,
    declared_divisions: list[str],
    division_justification: str = "",
    token: str | None = None,
) -> dict[str, Any]:
    """Submit a skill file for review."""
    client = _get_api_client(token)
    return await _submit_skill(
        skill_md_path=skill_md_path,
        declared_divisions=declared_divisions,
        division_justification=division_justification,
        api_client=client,
    )


# --- Tool 8: get_submission_status ---


@mcp.tool(
    name="get_submission_status",
    description="Check the status of a skill submission by ID.",
)
async def get_submission_status_tool(
    submission_id: str,
    token: str | None = None,
) -> dict[str, Any]:
    """Get the status of a submission."""
    client = _get_api_client(token)
    return await _get_submission_status(submission_id=submission_id, api_client=client)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
