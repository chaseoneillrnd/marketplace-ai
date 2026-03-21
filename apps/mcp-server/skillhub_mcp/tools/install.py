"""MCP tool: install_skill — install a skill from SkillHub to the local filesystem."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import httpx

from skillhub_mcp.api_client import APIClient
from skillhub_mcp.config import MCPSettings

logger = logging.getLogger(__name__)


async def install_skill(
    slug: str,
    version: str = "latest",
    *,
    settings: MCPSettings,
    api_client: APIClient,
    user_claims: dict[str, Any],
) -> dict[str, Any]:
    """Install a skill by slug, writing SKILL.md to the local skills directory.

    Division enforcement: the user's division (from JWT) must be in the skill's
    allowed divisions list. If not, the install is refused without writing any file.
    """
    # 1. Fetch the skill version from the API
    try:
        response = await api_client.get(f"/api/v1/skills/{slug}/versions/{version}")
        data = response.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return {"success": False, "error": "not_found"}
        logger.error("API error fetching skill %s: %s", slug, exc)
        return {"success": False, "error": "api_error"}

    # 2. Division enforcement — check BEFORE writing anything
    skill_divisions: list[str] = data.get("divisions", [])
    user_division: str = user_claims.get("division", "")
    if skill_divisions and user_division not in skill_divisions:
        logger.warning(
            "Division restricted: user=%s, skill=%s, allowed=%s",
            user_division,
            slug,
            skill_divisions,
        )
        return {"success": False, "error": "division_restricted"}

    # 3. Write SKILL.md to local filesystem
    resolved_version: str = data.get("version", version)
    content: str = data.get("content", "")
    skill_dir = Path(settings.skills_dir) / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(content)
    logger.info("Installed %s v%s to %s", slug, resolved_version, skill_path)

    # 4. Record the install via the API
    try:
        await api_client.post(
            f"/api/v1/skills/{slug}/install",
            json={"method": "mcp", "version": resolved_version},
        )
    except httpx.HTTPStatusError:
        logger.warning("Failed to record install for %s — skill was written locally", slug)

    return {
        "success": True,
        "version": resolved_version,
        "path": str(skill_path),
    }
