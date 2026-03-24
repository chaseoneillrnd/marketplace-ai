"""HTTP client for communicating with the SkillHub Flask/APIFlask backend."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from opentelemetry import trace

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


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
        with _tracer.start_as_current_span("http.get") as span:
            span.set_attribute("http.method", "GET")
            span.set_attribute("http.path", path)
            url = f"{self.base_url}{path}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._headers(), params=params)
                span.set_attribute("http.status_code", response.status_code)
                response.raise_for_status()
                return response

    async def post(self, path: str, json: dict[str, Any] | None = None) -> httpx.Response:
        """Send an async POST request."""
        with _tracer.start_as_current_span("http.post") as span:
            span.set_attribute("http.method", "POST")
            span.set_attribute("http.path", path)
            url = f"{self.base_url}{path}"
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self._headers(), json=json)
                span.set_attribute("http.status_code", response.status_code)
                response.raise_for_status()
                return response

    async def patch(self, path: str, json: dict[str, Any] | None = None) -> httpx.Response:
        """Send an async PATCH request."""
        with _tracer.start_as_current_span("http.patch") as span:
            span.set_attribute("http.method", "PATCH")
            span.set_attribute("http.path", path)
            url = f"{self.base_url}{path}"
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=self._headers(), json=json)
                span.set_attribute("http.status_code", response.status_code)
                response.raise_for_status()
                return response

    async def delete(self, path: str) -> httpx.Response:
        """Send an async DELETE request."""
        with _tracer.start_as_current_span("http.delete") as span:
            span.set_attribute("http.method", "DELETE")
            span.set_attribute("http.path", path)
            url = f"{self.base_url}{path}"
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=self._headers())
                span.set_attribute("http.status_code", response.status_code)
                response.raise_for_status()
                return response
