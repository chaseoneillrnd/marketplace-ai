"""MCP tool: list_installed — list locally installed skills with stale flag."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import httpx

from skillhub_mcp.api_client import APIClient
from skillhub_mcp.config import MCPSettings

logger = logging.getLogger(__name__)

_VERSION_RE = re.compile(r"^version:\s*(.+)$", re.MULTILINE)


def _read_installed_version(skill_path: Path) -> str | None:
    """Read the version from SKILL.md frontmatter."""
    content = skill_path.read_text()
    match = _VERSION_RE.search(content)
    return match.group(1).strip() if match else None


async def list_installed(
    *,
    settings: MCPSettings,
    api_client: APIClient,
) -> list[dict[str, Any]]:
    """List all locally installed skills with a stale flag.

    Reads the skills directory, extracts version from each SKILL.md frontmatter,
    then checks the API for the latest version to determine staleness.
    """
    skills_dir = Path(settings.skills_dir)
    if not skills_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        slug = skill_dir.name
        installed_version = _read_installed_version(skill_md) or "unknown"

        # Check latest version from API
        latest_version = installed_version
        try:
            response = await api_client.get(f"/api/v1/skills/{slug}/versions/latest")
            api_data = response.json()
            latest_version = api_data.get("version", installed_version)
        except (httpx.HTTPStatusError, httpx.RequestError):
            logger.warning("Could not check latest version for %s", slug)

        results.append({
            "slug": slug,
            "installed_version": installed_version,
            "latest_version": latest_version,
            "stale": installed_version != latest_version,
            "path": str(skill_md),
        })

    return results
