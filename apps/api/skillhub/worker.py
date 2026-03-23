"""ARQ worker — background jobs for analytics and exports."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


async def aggregate_daily_metrics(ctx: dict[str, Any]) -> dict[str, Any]:
    """Nightly: populate daily_metrics from raw events."""
    logger.info("aggregate_daily_metrics: started")
    # Placeholder — actual aggregation SQL goes here when DB is available
    return {"status": "ok", "message": "aggregation placeholder"}


async def recalculate_trending(ctx: dict[str, Any]) -> dict[str, Any]:
    """Recompute trending scores."""
    logger.info("recalculate_trending: started")
    return {"status": "ok", "message": "trending recalc placeholder"}


async def clean_expired_exports(ctx: dict[str, Any]) -> dict[str, Any]:
    """Remove export files older than 24 hours."""
    export_dir = os.environ.get("EXPORT_DIR", "/tmp/skillhub-exports")
    if not os.path.isdir(export_dir):
        return {"removed": 0}
    cutoff = time.time() - 86400
    removed = 0
    for fname in os.listdir(export_dir):
        fpath = os.path.join(export_dir, fname)
        if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
            os.remove(fpath)
            removed += 1
    logger.info("clean_expired_exports: removed %d files", removed)
    return {"removed": removed}


# WorkerSettings for ARQ (used when running `python -m arq skillhub.worker.WorkerSettings`)
# Not importing arq at module level to avoid hard dependency when arq isn't installed
try:
    from arq import cron
    from arq.connections import RedisSettings

    class WorkerSettings:
        """ARQ worker configuration."""

        functions = [aggregate_daily_metrics, recalculate_trending, clean_expired_exports]
        cron_jobs = [
            cron(aggregate_daily_metrics, hour=2, minute=0),
            cron(recalculate_trending, hour=2, minute=30),
            cron(clean_expired_exports, hour=3, minute=0),
        ]
        redis_settings = RedisSettings.from_dsn(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        )
        max_jobs = 4
        job_timeout = 600

except ImportError:
    # arq not installed — worker features unavailable but API still runs
    pass
