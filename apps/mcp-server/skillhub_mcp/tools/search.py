"""MCP tool: search_skills — search and browse skills from SkillHub."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from opentelemetry import trace

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


async def search_skills(
    query: str | None = None,
    category: str | None = None,
    divisions: list[str] | None = None,
    sort: str | None = None,
    install_method: str | None = None,
    verified: bool | None = None,
    featured: bool | None = None,
    page: int = 1,
    per_page: int = 20,
    *,
    api_client: APIClient,
) -> dict[str, Any]:
    """Search skills via the SkillHub API.

    Returns a paginated list of skill summaries matching the given filters.
    """
    with _tracer.start_as_current_span("search_skills") as span:
        span.set_attribute("skill.query", query or "")
        span.set_attribute("skill.category", category or "")
        span.set_attribute("skill.sort", sort or "")

        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        if divisions:
            params["divisions"] = divisions
        if sort:
            params["sort"] = sort
        if install_method:
            params["install_method"] = install_method
        if verified is not None:
            params["verified"] = verified
        if featured is not None:
            params["featured"] = featured

        try:
            response = await api_client.get("/api/v1/skills", params=params)
            result: dict[str, Any] = response.json()
            span.set_attribute("skill.result_count", len(result.get("items", [])))
            return result
        except httpx.HTTPStatusError as exc:
            span.set_attribute("error", True)
            logger.error("API error searching skills: %s", exc)
            return {"success": False, "error": "api_error", "detail": str(exc.response.status_code)}
        except httpx.RequestError as exc:
            span.set_attribute("error", True)
            logger.error("Network error searching skills: %s", exc)
            return {"success": False, "error": "network_error", "detail": str(exc)}
