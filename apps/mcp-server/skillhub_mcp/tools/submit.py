"""MCP tool: submit_skill — submit a local SKILL.md for review."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import httpx

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)


async def submit_skill(
    skill_md_path: str,
    *,
    api_client: APIClient,
) -> dict[str, Any]:
    """Submit a local SKILL.md file for review via the SkillHub API."""
    path = Path(skill_md_path)
    if not path.exists():
        return {"success": False, "error": "file_not_found"}

    content = path.read_text()

    try:
        response = await api_client.post(
            "/api/v1/submissions",
            json={"content": content},
        )
        return response.json()  # type: ignore[no-any-return]
    except httpx.HTTPStatusError as exc:
        logger.error("Submission failed: %s", exc)
        return {"success": False, "error": "api_error"}
