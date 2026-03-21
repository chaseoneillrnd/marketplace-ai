"""MCP tool: fork_skill — fork a skill to the user's namespace."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)


async def fork_skill(
    slug: str,
    *,
    api_client: APIClient,
) -> dict[str, Any]:
    """Fork a skill via the SkillHub API."""
    try:
        response = await api_client.post(f"/api/v1/skills/{slug}/fork")
        return response.json()  # type: ignore[no-any-return]
    except httpx.HTTPStatusError as exc:
        logger.error("Fork failed for %s: %s", slug, exc)
        return {"success": False, "error": "api_error"}
