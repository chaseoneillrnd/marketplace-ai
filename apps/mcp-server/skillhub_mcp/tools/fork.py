"""MCP tool: fork_skill — fork a skill to the user's namespace."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from opentelemetry import trace

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


async def fork_skill(
    slug: str,
    *,
    api_client: APIClient,
) -> dict[str, Any]:
    """Fork a skill via the SkillHub API."""
    with _tracer.start_as_current_span("fork_skill") as span:
        span.set_attribute("skill.slug", slug)
        try:
            response = await api_client.post(f"/api/v1/skills/{slug}/fork")
            return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPStatusError as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.type", "HTTPStatusError")
            logger.error("Fork failed for %s: %s", slug, exc)
            return {"success": False, "error": "api_error"}
