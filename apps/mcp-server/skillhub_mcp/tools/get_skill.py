"""MCP tool: get_skill — get full detail for a skill."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)


async def get_skill(
    slug: str,
    version: str = "latest",
    *,
    api_client: APIClient,
) -> dict[str, Any]:
    """Fetch full skill detail from the SkillHub API."""
    try:
        response = await api_client.get(f"/api/v1/skills/{slug}/versions/{version}")
        return response.json()  # type: ignore[no-any-return]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return {"success": False, "error": "not_found"}
        logger.error("API error fetching skill %s: %s", slug, exc)
        return {"success": False, "error": "api_error"}
