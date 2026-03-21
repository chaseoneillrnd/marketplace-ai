"""HTTP client for communicating with the SkillHub FastAPI backend."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class APIClient:
    """Thin wrapper around httpx for SkillHub API calls."""

    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        """Send an async GET request."""
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers(), params=params)
            response.raise_for_status()
            return response

    async def post(self, path: str, json: dict[str, Any] | None = None) -> httpx.Response:
        """Send an async POST request."""
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self._headers(), json=json)
            response.raise_for_status()
            return response
