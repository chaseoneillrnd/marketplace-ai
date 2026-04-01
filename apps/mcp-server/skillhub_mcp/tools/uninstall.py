"""MCP tool: uninstall_skill — uninstall a skill from the local filesystem."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import httpx
from opentelemetry import trace

from skillhub_mcp.api_client import APIClient
from skillhub_mcp.config import MCPSettings
from skillhub_mcp.tools.install import _is_valid_slug

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


async def uninstall_skill(
    slug: str,
    *,
    settings: MCPSettings,
    api_client: APIClient,
) -> dict[str, Any]:
    """Uninstall a skill by removing its local directory and recording via API."""
    with _tracer.start_as_current_span("uninstall_skill") as span:
        span.set_attribute("skill.slug", slug)

        # Slug validation — prevent path traversal (especially critical for rmtree)
        if not _is_valid_slug(slug):
            span.set_attribute("error", True)
            return {"success": False, "error": "invalid_slug"}

        skill_dir = Path(settings.skills_dir) / slug
        if not skill_dir.exists():
            span.set_attribute("error", True)
            return {"success": False, "error": "not_installed"}

        try:
            shutil.rmtree(skill_dir)
            logger.info("Removed local skill directory: %s", skill_dir)
        except OSError as exc:
            span.set_attribute("error", True)
            logger.error("Failed to remove skill directory %s: %s", skill_dir, exc)
            return {"success": False, "error": "filesystem_error", "detail": str(exc)}

        try:
            await api_client.delete(f"/api/v1/skills/{slug}/install")
        except httpx.HTTPStatusError as exc:
            logger.warning("Failed to record uninstall for %s: %s", slug, exc)
        except httpx.RequestError as exc:
            logger.warning("Network error recording uninstall for %s: %s", slug, exc)

        return {"success": True, "slug": slug}
