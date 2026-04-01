"""MCP tool: get_skill — get full detail for a skill."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from opentelemetry import trace

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


async def get_skill(
    slug: str,
    *,
    api_client: APIClient,
) -> dict[str, Any]:
    """Fetch full skill detail from the SkillHub API.

    Calls the detail endpoint which returns author info, install counts,
    tags, trigger phrases, and embedded version content — not just the
    bare version payload.
    """
    with _tracer.start_as_current_span("get_skill") as span:
        span.set_attribute("skill.slug", slug)
        try:
            response = await api_client.get(f"/api/v1/skills/{slug}")
            return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPStatusError as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.type", "HTTPStatusError")
            if exc.response.status_code == 404:
                return {"success": False, "error": "not_found"}
            logger.error("API error fetching skill %s: %s", slug, exc)
            return {"success": False, "error": "api_error"}
