"""Health check endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(request: Request) -> dict[str, Any]:
    """Return application health status and version."""
    settings = request.app.state.settings
    return {"status": "ok", "version": settings.app_version}
