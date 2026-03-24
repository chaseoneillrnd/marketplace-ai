"""Tests for the Redis cache module."""

import json
from unittest.mock import AsyncMock

import pytest

from skillhub.cache import TTL, cache_get, cache_set


class TestCacheGet:
    """Tests for cache_get."""

    @pytest.mark.asyncio
    async def test_returns_none_when_redis_is_none(self):
        result = await cache_get(None, "some_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_cache_miss(self):
        redis = AsyncMock()
        redis.get.return_value = None
        result = await cache_get(redis, "missing_key")
        assert result is None
        redis.get.assert_awaited_once_with("missing_key")

    @pytest.mark.asyncio
    async def test_returns_parsed_json_on_hit(self):
        redis = AsyncMock()
        redis.get.return_value = json.dumps({"count": 42})
        result = await cache_get(redis, "hit_key")
        assert result == {"count": 42}


class TestCacheSet:
    """Tests for cache_set."""

    @pytest.mark.asyncio
    async def test_does_nothing_when_redis_is_none(self):
        # Should not raise
        await cache_set(None, "key", {"data": 1}, 300)

    @pytest.mark.asyncio
    async def test_calls_setex_with_correct_args(self):
        redis = AsyncMock()
        await cache_set(redis, "my_key", {"val": "hello"}, 600)
        redis.setex.assert_awaited_once_with(
            "my_key", 600, json.dumps({"val": "hello"}, default=str)
        )


class TestTTLConstants:
    """Tests for TTL configuration."""

    def test_dashboard_summary_ttl(self):
        assert TTL["dashboard_summary"] == 300

    def test_dashboard_timeseries_ttl(self):
        assert TTL["dashboard_timeseries"] == 3600

    def test_dashboard_funnel_ttl(self):
        assert TTL["dashboard_funnel"] == 7200

    def test_export_rate_ttl(self):
        assert TTL["export_rate"] == 86400
