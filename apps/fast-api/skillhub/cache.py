"""Redis cache dependency and helpers."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import Request

logger = logging.getLogger(__name__)

TTL = {
    "dashboard_summary": 300,
    "dashboard_timeseries": 3600,
    "dashboard_funnel": 7200,
    "export_rate": 86400,
}


async def get_redis(request: Request):
    """Get Redis connection from app state."""
    return request.app.state.redis


async def cache_get(redis, key: str) -> Any | None:
    """Read from cache. Returns None on miss."""
    if redis is None:
        return None
    raw = await redis.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(redis, key: str, value: Any, ttl: int) -> None:
    """Write to cache with TTL."""
    if redis is None:
        return
    await redis.setex(key, ttl, json.dumps(value, default=str))
