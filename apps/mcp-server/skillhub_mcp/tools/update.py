"""MCP tool: update_skill — update an installed skill to the latest version."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import httpx
from opentelemetry import trace

from skillhub_mcp.api_client import APIClient
from skillhub_mcp.config import MCPSettings
from skillhub_mcp.tools.install import _is_valid_slug

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)

_VERSION_RE = re.compile(r"^version:\s*(.+)$", re.MULTILINE)


def _read_installed_version(skill_path: Path) -> str | None:
    """Read the version from SKILL.md frontmatter."""
    if not skill_path.exists():
        return None
    content = skill_path.read_text()
    match = _VERSION_RE.search(content)
    return match.group(1).strip() if match else None


async def update_skill(
    slug: str,
    *,
    settings: MCPSettings,
    api_client: APIClient,
    user_claims: dict[str, Any],
) -> dict[str, Any]:
    """Check if an installed skill is stale and update it if so.

    Reads the installed SKILL.md frontmatter, compares to the API's current version,
    and updates the local file if a newer version is available.
    """
    with _tracer.start_as_current_span("update_skill") as span:
        span.set_attribute("skill.slug", slug)

        # Slug validation — prevent path traversal
        if not _is_valid_slug(slug):
            span.set_attribute("error", True)
            return {"success": False, "error": "invalid_slug"}

        skill_path = Path(settings.skills_dir) / slug / "SKILL.md"
        installed_version = _read_installed_version(skill_path)

        if installed_version is None:
            span.set_attribute("error", True)
            span.set_attribute("error.type", "not_installed")
            return {"success": False, "error": "not_installed"}

        span.set_attribute("skill.installed_version", installed_version)

        # Fetch latest from API
        try:
            response = await api_client.get(f"/api/v1/skills/{slug}/versions/latest")
            data = response.json()
        except httpx.HTTPStatusError as exc:
            span.set_attribute("error", True)
            if exc.response.status_code == 404:
                return {"success": False, "error": "not_found"}
            return {"success": False, "error": "api_error"}
        except httpx.RequestError as exc:
            span.set_attribute("error", True)
            logger.error("Network error fetching skill %s: %s", slug, exc)
            return {"success": False, "error": "network_error"}

        latest_version: str = data.get("version", "")
        span.set_attribute("skill.latest_version", latest_version)

        if installed_version == latest_version:
            span.set_attribute("skill.updated", False)
            return {"updated": False, "version": installed_version}

        # Division check before writing
        skill_divisions: list[str] = data.get("divisions", [])
        user_division: str = user_claims.get("division", "")
        if skill_divisions and user_division not in skill_divisions:
            span.set_attribute("error", True)
            span.set_attribute("error.type", "division_restricted")
            return {"success": False, "error": "division_restricted"}

        # Write updated content
        content: str = data.get("content", "")
        skill_path.write_text(content)
        logger.info("Updated %s from %s to %s", slug, installed_version, latest_version)
        span.set_attribute("skill.updated", True)

        # Record install via API
        try:
            await api_client.post(
                f"/api/v1/skills/{slug}/install",
                json={"method": "mcp", "version": latest_version},
            )
        except httpx.HTTPStatusError:
            logger.warning("Failed to record update install for %s", slug)

        return {
            "updated": True,
            "from_version": installed_version,
            "to_version": latest_version,
            "restart_required": True,
            "note": "Restart Claude Code to load the updated skill.",
        }
