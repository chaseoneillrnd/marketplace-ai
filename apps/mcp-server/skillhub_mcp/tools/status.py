"""MCP tool: get_submission_status — check submission status."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from opentelemetry import trace

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


async def get_submission_status(
    submission_id: str,
    *,
    api_client: APIClient,
) -> dict[str, Any]:
    """Fetch the status of a submission from the SkillHub API."""
    with _tracer.start_as_current_span("get_submission_status") as span:
        span.set_attribute("submission.id", submission_id)
        try:
            response = await api_client.get(f"/api/v1/submissions/{submission_id}")
            return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPStatusError as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.type", "HTTPStatusError")
            if exc.response.status_code == 404:
                return {"success": False, "error": "not_found"}
            logger.error("Failed to get submission status: %s", exc)
            return {"success": False, "error": "api_error"}
