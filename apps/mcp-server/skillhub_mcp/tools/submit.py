"""MCP tool: submit_skill — submit a local SKILL.md for review."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import httpx
from opentelemetry import trace

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


def _parse_frontmatter(content: str) -> dict[str, Any] | None:
    """Parse YAML-like frontmatter from SKILL.md content.

    Expects content starting with --- and ending with ---.
    Returns parsed key-value pairs or None if no frontmatter found.
    """
    lines = content.strip().split("\n")
    if not lines or lines[0].strip() != "---":
        return None

    frontmatter: dict[str, Any] = {}
    i = 1
    while i < len(lines):
        line = lines[i].strip()
        if line == "---":
            return frontmatter
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            # Handle list values (simple inline YAML)
            if value.startswith("[") and value.endswith("]"):
                items = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
                frontmatter[key] = items
            elif value == "":
                # Could be a multi-line list
                items = []
                i += 1
                while i < len(lines) and lines[i].strip().startswith("- "):
                    items.append(lines[i].strip().removeprefix("- ").strip())
                    i += 1
                frontmatter[key] = items
                continue
            else:
                frontmatter[key] = value.strip("\"'")
        i += 1
    return None  # No closing ---


async def submit_skill(
    skill_md_path: str,
    *,
    declared_divisions: list[str],
    division_justification: str = "",
    api_client: APIClient,
) -> dict[str, Any]:
    """Submit a local SKILL.md file for review via the SkillHub API.

    Parses frontmatter to extract name, short_desc, and category.
    Requires declared_divisions to specify which org divisions should access the skill.
    """
    with _tracer.start_as_current_span("submit_skill") as span:
        span.set_attribute("skill.md_path", skill_md_path)

        path = Path(skill_md_path)
        if not path.exists():
            span.set_attribute("error", True)
            span.set_attribute("error.type", "file_not_found")
            return {"success": False, "error": "file_not_found"}

        content = path.read_text()

        # Parse frontmatter to extract required submission fields
        frontmatter = _parse_frontmatter(content)
        if frontmatter is None:
            span.set_attribute("error", True)
            span.set_attribute("error.type", "missing_frontmatter")
            return {
                "success": False,
                "error": "missing_frontmatter",
                "detail": "SKILL.md must have YAML frontmatter with name, category, and short_desc",
            }

        name = frontmatter.get("name")
        category = frontmatter.get("category")
        short_desc = frontmatter.get("short_desc", "")

        missing = [f for f in ("name", "category") if not frontmatter.get(f)]
        if missing:
            span.set_attribute("error", True)
            span.set_attribute("error.type", "missing_fields")
            return {
                "success": False,
                "error": "missing_frontmatter_fields",
                "detail": f"Frontmatter missing required fields: {', '.join(missing)}",
            }

        try:
            response = await api_client.post(
                "/api/v1/submissions",
                json={
                    "name": name,
                    "short_desc": short_desc,
                    "category": category,
                    "content": content,
                    "declared_divisions": declared_divisions,
                    "division_justification": division_justification,
                },
            )
            return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPStatusError as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.type", "HTTPStatusError")
            logger.error("Submission failed: %s", exc)
            return {"success": False, "error": "api_error", "detail": str(exc)}
