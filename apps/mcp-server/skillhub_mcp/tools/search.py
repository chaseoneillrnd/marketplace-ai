"""MCP tool: search_skills — search and browse skills from SkillHub."""

from __future__ import annotations

import logging
from typing import Any

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)


async def search_skills(
    query: str | None = None,
    category: str | None = None,
    divisions: list[str] | None = None,
    sort: str | None = None,
    *,
    api_client: APIClient,
) -> dict[str, Any]:
    """Search skills via the SkillHub API.

    Returns a paginated list of skill summaries matching the given filters.
    """
    params: dict[str, Any] = {}
    if query:
        params["q"] = query
    if category:
        params["category"] = category
    if divisions:
        params["divisions"] = divisions
    if sort:
        params["sort"] = sort

    response = await api_client.get("/api/v1/skills", params=params)
    return response.json()  # type: ignore[no-any-return]
