"""MCP tool: login — authenticate with SkillHub and obtain a bearer token."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from opentelemetry import trace

from skillhub_mcp.api_client import APIClient

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


async def login(
    username: str,
    password: str,
    *,
    api_client: APIClient,
) -> dict[str, Any]:
    """Authenticate via stub auth and return a bearer token."""
    with _tracer.start_as_current_span("login") as span:
        span.set_attribute("auth.username", username)
        try:
            response = await api_client.post(
                "/auth/token",
                json={"username": username, "password": password},
            )
            data = response.json()
            token = data.get("access_token", "")
            span.set_attribute("auth.success", True)
            return {
                "success": True,
                "token": token,
                "token_type": data.get("token_type", "bearer"),
            }
        except httpx.HTTPStatusError as exc:
            span.set_attribute("error", True)
            if exc.response.status_code == 401:
                return {"success": False, "error": "invalid_credentials"}
            logger.error("API error during login: %s", exc)
            return {"success": False, "error": "api_error"}
        except httpx.RequestError as exc:
            span.set_attribute("error", True)
            logger.error("Network error during login: %s", exc)
            return {"success": False, "error": "network_error"}
