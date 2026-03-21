"""MCP tool: get_submission_status — check submission status."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)


async def get_submission_status(
    submission_id: str,
    *,
    api_client: APIClient,
) -> dict[str, Any]:
    """Fetch the status of a submission from the SkillHub API."""
    try:
        response = await api_client.get(f"/api/v1/submissions/{submission_id}")
        return response.json()  # type: ignore[no-any-return]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return {"success": False, "error": "not_found"}
        logger.error("Failed to get submission status: %s", exc)
        return {"success": False, "error": "api_error"}
