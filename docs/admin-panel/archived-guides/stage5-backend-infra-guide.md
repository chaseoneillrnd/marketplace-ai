# Stage 5: Backend Infrastructure — Analytics Engine, ARQ Worker & Redis Cache

**Target audience:** Claude Code agents
**Prerequisites:** Stages 1–4 complete (migrations 001 + e20cb641 applied, OTel tracing wired, admin endpoints live)
**Estimated implementation time:** 14–18 two-to-five-minute TDD tasks
**Coverage gate:** ≥ 80% (pytest-cov --cov-fail-under=80)

---

## Overview

Stage 5 builds the data pipeline that feeds the admin dashboard. By the end of this stage:

- A `daily_metrics` table holds pre-aggregated analytics per division per day
- An `export_jobs` table tracks async CSV/JSON export requests
- An ARQ background worker runs nightly aggregation, trending recalculation, and export cleanup
- Four analytics API endpoints serve cached data with sub-50 ms p99 latency
- Redis caching with explicit TTLs decouples the hot dashboard path from heavy DB queries
- Docker Compose gains an `arq-worker` service sharing an `export-staging` volume with the API

**Architecture principle:** The nightly cron job owns cache writes. API endpoints read from Redis; they do NOT write to Redis on cache miss. This keeps the critical path clean and prevents thundering-herd on cold start.

---

## TDD Task Breakdown

Work through tasks in order. Each task follows RED → GREEN → REFACTOR.

### Task 1 — Alembic migration: `daily_metrics`, `export_jobs`, `users.admin_scopes`, new indexes
### Task 2 — SQLAlchemy models: `DailyMetrics`, `ExportJob`
### Task 3 — `apps/api/skillhub/cache.py` — Redis dependency + key conventions
### Task 4 — `apps/api/skillhub/services/analytics.py` — `run_daily_aggregation()`
### Task 5 — Analytics service: DAU calculation from audit_log
### Task 6 — Analytics service: submission funnel counts
### Task 7 — Analytics service: `get_summary()` (Redis-read path)
### Task 8 — Analytics service: `get_time_series()`, `get_submission_funnel()`, `get_top_skills()`
### Task 9 — `apps/api/skillhub/routers/analytics.py` — four endpoints
### Task 10 — `apps/api/skillhub/services/exports.py` — request, rate-limit, generate
### Task 11 — Export router: POST, GET, download endpoints
### Task 12 — `apps/api/skillhub/worker.py` — WorkerSettings + cron jobs
### Task 13 — `apps/api/skillhub/scripts/backfill_metrics.py`
### Task 14 — `apps/api/skillhub/main.py` — lifespan: ARQ + Redis pools
### Task 15 — `libs/db/skillhub_db/session.py` — connection pool tuning
### Task 16 — `docker-compose.yml` — `arq-worker` service + `export-staging` volume
### Task 17 — `mise.toml` — worker and aggregate tasks
### Task 18 — Integration smoke test (optional, verify via `mise run worker:burst`)

---

## Task 1 — Alembic Migration

**File:** `libs/db/migrations/versions/XXXX_analytics_engine.py`

Generate with:
```bash
alembic -c libs/db/alembic.ini revision --autogenerate -m "analytics_engine"
```
Then replace the auto-generated body with the explicit DDL below.

### Migration DDL

```python
"""Analytics engine: daily_metrics, export_jobs, users.admin_scopes, new indexes.

Revision ID: <generated>
Revises: e20cb6415067
Create Date: <generated>
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "<generated>"
down_revision: str | None = "e20cb6415067"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── users.admin_scopes ───────────────────────────────────────────────────
    op.add_column(
        "users",
        sa.Column(
            "admin_scopes",
            postgresql.JSON(astext_type=sa.Text()),
            server_default="'[]'::json",
            nullable=False,
        ),
    )

    # ── Performance indexes on existing tables ───────────────────────────────
    op.create_index("ix_installs_installed_at", "installs", ["installed_at"])
    op.create_index("ix_submissions_created_at", "submissions", ["created_at"])

    # ── daily_metrics ────────────────────────────────────────────────────────
    # '__all__' sentinel is used for platform-wide rows.
    # We do NOT add a FK on division_slug so '__all__' rows are unconstrained.
    # Per-division rows use real slugs that exist in the divisions table;
    # the application enforces this in run_daily_aggregation().
    op.create_table(
        "daily_metrics",
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("division_slug", sa.Text(), nullable=False),
        # Activity
        sa.Column("new_installs", sa.Integer(), server_default="0", nullable=False),
        sa.Column("active_installs", sa.Integer(), server_default="0", nullable=False),
        sa.Column("uninstalls", sa.Integer(), server_default="0", nullable=False),
        sa.Column("dau", sa.Integer(), server_default="0", nullable=False),
        sa.Column("new_users", sa.Integer(), server_default="0", nullable=False),
        sa.Column("new_submissions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("published_skills", sa.Integer(), server_default="0", nullable=False),
        sa.Column("new_reviews", sa.Integer(), server_default="0", nullable=False),
        # Submission funnel
        sa.Column("funnel_submitted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("funnel_g1_pass", sa.Integer(), server_default="0", nullable=False),
        sa.Column("funnel_g2_pass", sa.Integer(), server_default="0", nullable=False),
        sa.Column("funnel_approved", sa.Integer(), server_default="0", nullable=False),
        sa.Column("funnel_published", sa.Integer(), server_default="0", nullable=False),
        # Gate 3 median wait in seconds
        sa.Column("gate3_median_wait", sa.BigInteger(), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("metric_date", "division_slug"),
    )
    op.create_index(
        "ix_daily_metrics_date",
        "daily_metrics",
        [sa.text("metric_date DESC")],
    )
    op.create_index(
        "ix_daily_metrics_division_date",
        "daily_metrics",
        ["division_slug", sa.text("metric_date DESC")],
    )

    # ── export_jobs ──────────────────────────────────────────────────────────
    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "requested_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column("format", sa.String(10), nullable=False),
        sa.Column(
            "filters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(20),
            server_default="queued",
            nullable=False,
        ),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_export_jobs_requested_by", "export_jobs", ["requested_by"])
    op.create_index("ix_export_jobs_created_at", "export_jobs", ["created_at"])


def downgrade() -> None:
    op.drop_table("export_jobs")
    op.drop_table("daily_metrics")
    op.drop_index("ix_submissions_created_at", table_name="submissions")
    op.drop_index("ix_installs_installed_at", table_name="installs")
    op.drop_column("users", "admin_scopes")
```

**Why no FK on `division_slug`:** PostgreSQL evaluates FK constraints per-row. The `'__all__'` sentinel would violate a FK referencing `divisions.slug`. The clean solution is to omit the FK and let the application guarantee that only `'__all__'` or valid division slugs appear (enforced in `run_daily_aggregation()`).

---

## Task 2 — SQLAlchemy Models

**File:** `libs/db/skillhub_db/models/analytics.py`

```python
"""Analytics models: DailyMetrics, ExportJob."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from skillhub_db.base import Base


class DailyMetrics(Base):
    """Pre-aggregated daily platform metrics, partitioned by division_slug.

    division_slug == '__all__' holds platform-wide totals.
    DAU in the '__all__' row is re-derived (not summed) to avoid cross-division
    double-counting for users who belong to multiple events on a given day.
    """

    __tablename__ = "daily_metrics"

    metric_date: Mapped[date] = mapped_column(Date(), primary_key=True)
    division_slug: Mapped[str] = mapped_column(Text(), primary_key=True)

    # Activity counters
    new_installs: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    active_installs: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    uninstalls: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    dau: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    new_users: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    new_submissions: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    published_skills: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    new_reviews: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)

    # Submission funnel
    funnel_submitted: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    funnel_g1_pass: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    funnel_g2_pass: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    funnel_approved: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    funnel_published: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)

    # Gate 3 median wait in seconds (nullable — may be absent before any G3 reviews)
    gate3_median_wait: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<DailyMetrics {self.metric_date} division={self.division_slug!r}>"


class ExportJob(Base):
    """Async data export request — created by admin, executed by ARQ worker."""

    __tablename__ = "export_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    requested_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    filters: Mapped[dict | None] = mapped_column(JSONB(), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="queued", nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text(), nullable=True)
    error: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ExportJob {self.id} scope={self.scope!r} status={self.status!r}>"
```

Register in `libs/db/skillhub_db/models/__init__.py`:
```python
from skillhub_db.models.analytics import DailyMetrics, ExportJob  # noqa: F401
```

---

## Task 3 — Redis Cache Module

**File:** `apps/api/skillhub/cache.py`

```python
"""Redis cache helpers — dependency injection + key conventions.

Architecture note
-----------------
Cache WRITES happen exclusively in the nightly ARQ job (see worker.py).
API endpoints only READ from Redis. On a cache miss the endpoint falls back
to a direct DB query — it does NOT write to Redis. This decouples the hot
API path from cache population latency and prevents thundering-herd on
cold boot.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis
from fastapi import Request

logger = logging.getLogger(__name__)

# ── TTL constants (seconds) ──────────────────────────────────────────────────
TTL_SUMMARY = 300        # 5 min — dashboard summary
TTL_TIMESERIES = 3600    # 1 hr  — time-series charts
TTL_FUNNEL = 7200        # 2 hr  — funnel rarely changes intra-day
TTL_TOP_SKILLS = 1800    # 30 min

# ── Key helpers ──────────────────────────────────────────────────────────────

def key_summary(division: str) -> str:
    """analytics:summary:{division}"""
    return f"analytics:summary:{division}"


def key_timeseries(division: str, days: int) -> str:
    """analytics:timeseries:{division}:{days}"""
    return f"analytics:timeseries:{division}:{days}"


def key_funnel(division: str, days: int) -> str:
    """analytics:funnel:{division}:{days}"""
    return f"analytics:funnel:{division}:{days}"


def key_top_skills(limit: int) -> str:
    """analytics:top_skills:{limit}"""
    return f"analytics:top_skills:{limit}"


# ── FastAPI dependency ───────────────────────────────────────────────────────

async def get_redis(request: Request) -> aioredis.Redis:  # type: ignore[type-arg]
    """Yield the shared Redis connection pool stored on app.state."""
    redis: aioredis.Redis = request.app.state.redis  # type: ignore[type-arg]
    return redis


# ── Read/write helpers ───────────────────────────────────────────────────────

async def cache_get(redis: aioredis.Redis, key: str) -> Any | None:  # type: ignore[type-arg]
    """Return deserialized value or None on miss/error."""
    try:
        raw = await redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.warning("Redis GET failed for key %r", key, exc_info=True)
        return None


async def cache_set(
    redis: aioredis.Redis,  # type: ignore[type-arg]
    key: str,
    value: Any,
    ttl: int,
) -> None:
    """Serialize and store value with TTL. Swallows errors — cache is best-effort."""
    try:
        await redis.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        logger.warning("Redis SETEX failed for key %r", key, exc_info=True)


async def cache_delete_pattern(redis: aioredis.Redis, pattern: str) -> int:  # type: ignore[type-arg]
    """Delete all keys matching pattern. Returns count deleted."""
    try:
        keys = await redis.keys(pattern)
        if not keys:
            return 0
        return int(await redis.delete(*keys))
    except Exception:
        logger.warning("Redis DELETE pattern %r failed", pattern, exc_info=True)
        return 0
```

---

## Task 4–6 — Analytics Service: Core Aggregation

**File:** `apps/api/skillhub/services/analytics.py`

### Overview

`run_daily_aggregation(db, target_date)` is the master function called by the ARQ cron job. It:

1. Computes per-division rows (installs JOIN users GROUP BY division)
2. Computes the `'__all__'` platform-wide row (DAU re-derived, not summed)
3. Upserts each row with `INSERT ON CONFLICT DO UPDATE` — fully idempotent

```python
"""Analytics aggregation service.

All functions are synchronous (SQLAlchemy Core + Session).
Called from ARQ worker tasks (which run in a thread pool executor
or directly as sync functions via arq's sync job support).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from skillhub_db.models.analytics import DailyMetrics, ExportJob
from skillhub_db.models.audit import AuditLog
from skillhub_db.models.skill import Skill
from skillhub_db.models.social import Install, Review  # Review if exists
from skillhub_db.models.submission import Submission, SubmissionStatus
from skillhub_db.models.user import User
from sqlalchemy import Date, cast, distinct, extract, func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# DAU event_types that count as "active" in audit_log
DAU_EVENT_TYPES = frozenset({
    "skill.install",
    "skill.uninstall",
    "skill.fork",
    "submission.create",
    "review.create",
    "comment.create",
})


# ── Idempotent upsert helper ─────────────────────────────────────────────────

def _upsert_daily_metrics(db: Session, row: dict[str, Any]) -> None:
    """INSERT ... ON CONFLICT DO UPDATE — safe to run multiple times for same date/division."""
    stmt = (
        pg_insert(DailyMetrics)
        .values(**row)
        .on_conflict_do_update(
            index_elements=["metric_date", "division_slug"],
            set_={
                k: v
                for k, v in row.items()
                if k not in ("metric_date", "division_slug")
            },
        )
    )
    db.execute(stmt)


# ── DAU helper ───────────────────────────────────────────────────────────────

def _compute_dau(db: Session, target_date: date, division_slug: str) -> int:
    """Count distinct actor_ids active on target_date for a given division.

    For '__all__' the query is platform-wide (no division filter).
    This avoids double-counting users who trigger events in multiple contexts.
    """
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=UTC)
    day_end = day_start + timedelta(days=1)

    base_q = (
        select(func.count(distinct(AuditLog.actor_id)))
        .where(AuditLog.event_type.in_(DAU_EVENT_TYPES))
        .where(AuditLog.created_at >= day_start)
        .where(AuditLog.created_at < day_end)
        .where(AuditLog.actor_id.isnot(None))
    )

    if division_slug != "__all__":
        # Join to users to filter by division
        base_q = base_q.join(User, User.id == AuditLog.actor_id).where(
            User.division == division_slug
        )

    result: int = db.execute(base_q).scalar_one_or_none() or 0
    return result


# ── Submission funnel helper ─────────────────────────────────────────────────

def _compute_funnel(
    db: Session, target_date: date, division_slug: str
) -> dict[str, int]:
    """Count submissions by terminal funnel status created on target_date."""
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=UTC)
    day_end = day_start + timedelta(days=1)

    base_q = (
        select(Submission.status, func.count(Submission.id))
        .where(Submission.created_at >= day_start)
        .where(Submission.created_at < day_end)
        .group_by(Submission.status)
    )

    if division_slug != "__all__":
        base_q = base_q.join(User, User.id == Submission.submitted_by).where(
            User.division == division_slug
        )

    rows = db.execute(base_q).all()
    counts: dict[str, int] = {r[0]: r[1] for r in rows}

    return {
        "funnel_submitted": counts.get(SubmissionStatus.SUBMITTED, 0),
        "funnel_g1_pass": counts.get(SubmissionStatus.GATE1_PASSED, 0),
        "funnel_g2_pass": counts.get(SubmissionStatus.GATE2_PASSED, 0),
        "funnel_approved": counts.get(SubmissionStatus.APPROVED, 0),
        "funnel_published": counts.get(SubmissionStatus.PUBLISHED, 0),
    }


# ── Gate 3 median wait ───────────────────────────────────────────────────────

def _compute_gate3_median_wait(db: Session, target_date: date) -> int | None:
    """Return median seconds between gate2_passed and gate3 review on target_date.

    Approximated via percentile_cont on audit_log timestamps.
    Returns None if no gate3 reviews occurred on target_date.
    """
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=UTC)
    day_end = day_start + timedelta(days=1)

    # Submissions that reached gate3 (APPROVED or GATE3_CHANGES_REQUESTED) on target_date
    # We approximate wait as (gate3_review_created_at - submission.created_at).
    # A more precise implementation queries submission_gate_results.created_at at gate=3.
    stmt = text("""
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY EXTRACT(EPOCH FROM (
                sgr.created_at - s.created_at
            ))
        )::BIGINT AS median_wait
        FROM submission_gate_results sgr
        JOIN submissions s ON s.id = sgr.submission_id
        WHERE sgr.gate = 3
          AND sgr.created_at >= :day_start
          AND sgr.created_at < :day_end
    """)
    result = db.execute(stmt, {"day_start": day_start, "day_end": day_end}).scalar_one_or_none()
    return int(result) if result is not None else None


# ── Main aggregation entry point ─────────────────────────────────────────────

def run_daily_aggregation(db: Session, target_date: date) -> int:
    """Aggregate metrics for target_date. Idempotent — safe to re-run.

    Returns number of rows upserted (divisions + 1 for '__all__').
    """
    logger.info("Starting daily aggregation for %s", target_date)
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=UTC)
    day_end = day_start + timedelta(days=1)

    # ── Fetch all active divisions ────────────────────────────────────────────
    division_rows = db.execute(text("SELECT slug FROM divisions")).fetchall()
    division_slugs: list[str] = [r[0] for r in division_rows]

    rows_written = 0

    for div_slug in division_slugs:
        row = _build_division_row(db, target_date, div_slug, day_start, day_end)
        _upsert_daily_metrics(db, row)
        rows_written += 1

    # ── Platform-wide '__all__' row ───────────────────────────────────────────
    all_row = _build_platform_row(db, target_date, day_start, day_end)
    _upsert_daily_metrics(db, all_row)
    rows_written += 1

    db.commit()
    logger.info("Daily aggregation complete: %d rows upserted for %s", rows_written, target_date)
    return rows_written


def _build_division_row(
    db: Session,
    target_date: date,
    division_slug: str,
    day_start: datetime,
    day_end: datetime,
) -> dict[str, Any]:
    """Build one division row dict."""
    # new_installs: installs created today for users in this division
    new_installs: int = db.execute(
        select(func.count(Install.id))
        .join(User, User.id == Install.user_id)
        .where(User.division == division_slug)
        .where(Install.installed_at >= day_start)
        .where(Install.installed_at < day_end)
    ).scalar_one() or 0

    # active_installs: installs with uninstalled_at IS NULL for this division
    active_installs: int = db.execute(
        select(func.count(Install.id))
        .join(User, User.id == Install.user_id)
        .where(User.division == division_slug)
        .where(Install.uninstalled_at.is_(None))
    ).scalar_one() or 0

    # uninstalls: installs uninstalled today
    uninstalls: int = db.execute(
        select(func.count(Install.id))
        .join(User, User.id == Install.user_id)
        .where(User.division == division_slug)
        .where(Install.uninstalled_at >= day_start)
        .where(Install.uninstalled_at < day_end)
    ).scalar_one() or 0

    # new_users: users created today in this division
    new_users: int = db.execute(
        select(func.count(User.id))
        .where(User.division == division_slug)
        .where(User.created_at >= day_start)
        .where(User.created_at < day_end)
    ).scalar_one() or 0

    # new_submissions: submissions created today by users in this division
    new_submissions: int = db.execute(
        select(func.count(Submission.id))
        .join(User, User.id == Submission.submitted_by)
        .where(User.division == division_slug)
        .where(Submission.created_at >= day_start)
        .where(Submission.created_at < day_end)
    ).scalar_one() or 0

    # published_skills: skills published today authored by users in this division
    published_skills: int = db.execute(
        select(func.count(Skill.id))
        .join(User, User.id == Skill.author_id)
        .where(User.division == division_slug)
        .where(Skill.published_at >= day_start)
        .where(Skill.published_at < day_end)
        .where(Skill.status == "published")
    ).scalar_one() or 0

    dau = _compute_dau(db, target_date, division_slug)
    funnel = _compute_funnel(db, target_date, division_slug)

    return {
        "metric_date": target_date,
        "division_slug": division_slug,
        "new_installs": new_installs,
        "active_installs": active_installs,
        "uninstalls": uninstalls,
        "dau": dau,
        "new_users": new_users,
        "new_submissions": new_submissions,
        "published_skills": published_skills,
        "new_reviews": 0,  # extend when Review model is finalized
        **funnel,
        "gate3_median_wait": None,  # only computed for __all__ row
        "computed_at": datetime.now(UTC),
    }


def _build_platform_row(
    db: Session,
    target_date: date,
    day_start: datetime,
    day_end: datetime,
) -> dict[str, Any]:
    """Build the platform-wide '__all__' row.

    DAU is re-derived (not summed from divisions) to avoid double-counting.
    """
    new_installs: int = db.execute(
        select(func.count(Install.id))
        .where(Install.installed_at >= day_start)
        .where(Install.installed_at < day_end)
    ).scalar_one() or 0

    active_installs: int = db.execute(
        select(func.count(Install.id))
        .where(Install.uninstalled_at.is_(None))
    ).scalar_one() or 0

    uninstalls: int = db.execute(
        select(func.count(Install.id))
        .where(Install.uninstalled_at >= day_start)
        .where(Install.uninstalled_at < day_end)
    ).scalar_one() or 0

    new_users: int = db.execute(
        select(func.count(User.id))
        .where(User.created_at >= day_start)
        .where(User.created_at < day_end)
    ).scalar_one() or 0

    new_submissions: int = db.execute(
        select(func.count(Submission.id))
        .where(Submission.created_at >= day_start)
        .where(Submission.created_at < day_end)
    ).scalar_one() or 0

    published_skills: int = db.execute(
        select(func.count(Skill.id))
        .where(Skill.published_at >= day_start)
        .where(Skill.published_at < day_end)
        .where(Skill.status == "published")
    ).scalar_one() or 0

    dau = _compute_dau(db, target_date, "__all__")
    funnel = _compute_funnel(db, target_date, "__all__")
    gate3_median = _compute_gate3_median_wait(db, target_date)

    return {
        "metric_date": target_date,
        "division_slug": "__all__",
        "new_installs": new_installs,
        "active_installs": active_installs,
        "uninstalls": uninstalls,
        "dau": dau,
        "new_users": new_users,
        "new_submissions": new_submissions,
        "published_skills": published_skills,
        "new_reviews": 0,
        **funnel,
        "gate3_median_wait": gate3_median,
        "computed_at": datetime.now(UTC),
    }


# ── Read-path functions (used by API endpoints) ──────────────────────────────

def get_summary(db: Session, division: str = "__all__") -> dict[str, Any]:
    """Return latest daily_metrics row + 7-day and 30-day deltas.

    Called by the analytics router on Redis cache miss.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    day_7 = today - timedelta(days=7)
    day_30 = today - timedelta(days=30)

    def _fetch(d: date) -> DailyMetrics | None:
        return db.get(DailyMetrics, {"metric_date": d, "division_slug": division})

    latest = _fetch(yesterday)
    week_ago = _fetch(day_7)
    month_ago = _fetch(day_30)

    if latest is None:
        return {"division": division, "available": False}

    def _delta(field: str, baseline: DailyMetrics | None) -> int | None:
        if baseline is None:
            return None
        return getattr(latest, field) - getattr(baseline, field)

    return {
        "division": division,
        "available": True,
        "as_of": yesterday.isoformat(),
        "dau": latest.dau,
        "active_installs": latest.active_installs,
        "new_installs_today": latest.new_installs,
        "new_submissions_today": latest.new_submissions,
        "published_skills": latest.published_skills,
        "deltas": {
            "dau_7d": _delta("dau", week_ago),
            "installs_7d": _delta("active_installs", week_ago),
            "dau_30d": _delta("dau", month_ago),
            "installs_30d": _delta("active_installs", month_ago),
        },
    }


def get_time_series(
    db: Session, days: int = 30, division: str = "__all__"
) -> list[dict[str, Any]]:
    """Return daily_metrics rows for the last N days, ordered ascending."""
    cutoff = date.today() - timedelta(days=days)
    rows = (
        db.query(DailyMetrics)
        .filter(
            DailyMetrics.division_slug == division,
            DailyMetrics.metric_date >= cutoff,
        )
        .order_by(DailyMetrics.metric_date)
        .all()
    )
    return [
        {
            "date": r.metric_date.isoformat(),
            "dau": r.dau,
            "new_installs": r.new_installs,
            "active_installs": r.active_installs,
            "new_users": r.new_users,
            "new_submissions": r.new_submissions,
        }
        for r in rows
    ]


def get_submission_funnel(
    db: Session, days: int = 30, division: str = "__all__"
) -> dict[str, Any]:
    """Aggregate submission funnel over last N days."""
    cutoff = date.today() - timedelta(days=days)
    rows = (
        db.query(DailyMetrics)
        .filter(
            DailyMetrics.division_slug == division,
            DailyMetrics.metric_date >= cutoff,
        )
        .all()
    )
    totals = {
        "submitted": sum(r.funnel_submitted for r in rows),
        "g1_pass": sum(r.funnel_g1_pass for r in rows),
        "g2_pass": sum(r.funnel_g2_pass for r in rows),
        "approved": sum(r.funnel_approved for r in rows),
        "published": sum(r.funnel_published for r in rows),
    }

    def _rate(num: int, den: int) -> float | None:
        return round(num / den * 100, 1) if den else None

    return {
        "division": division,
        "days": days,
        "totals": totals,
        "conversion_rates": {
            "submitted_to_g1": _rate(totals["g1_pass"], totals["submitted"]),
            "g1_to_g2": _rate(totals["g2_pass"], totals["g1_pass"]),
            "g2_to_approved": _rate(totals["approved"], totals["g2_pass"]),
            "approved_to_published": _rate(totals["published"], totals["approved"]),
            "end_to_end": _rate(totals["published"], totals["submitted"]),
        },
    }


def get_top_skills(db: Session, limit: int = 10) -> list[dict[str, Any]]:
    """Return top skills by install_count + trending_score."""
    rows = (
        db.query(Skill)
        .filter(Skill.status == "published")
        .order_by(Skill.install_count.desc(), Skill.trending_score.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "slug": r.slug,
            "name": r.name,
            "install_count": r.install_count,
            "trending_score": float(r.trending_score),
            "avg_rating": float(r.avg_rating),
        }
        for r in rows
    ]
```

---

## Task 7 — Analytics Schemas

**File:** `apps/api/skillhub/schemas/analytics.py`

```python
"""Pydantic schemas for analytics API responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SummaryDeltas(BaseModel):
    dau_7d: int | None
    installs_7d: int | None
    dau_30d: int | None
    installs_30d: int | None


class SummaryResponse(BaseModel):
    division: str
    available: bool
    as_of: str | None = None
    dau: int | None = None
    active_installs: int | None = None
    new_installs_today: int | None = None
    new_submissions_today: int | None = None
    published_skills: int | None = None
    deltas: SummaryDeltas | None = None


class TimeSeriesPoint(BaseModel):
    date: str
    dau: int
    new_installs: int
    active_installs: int
    new_users: int
    new_submissions: int


class TimeSeriesResponse(BaseModel):
    division: str
    days: int
    points: list[TimeSeriesPoint]


class FunnelTotals(BaseModel):
    submitted: int
    g1_pass: int
    g2_pass: int
    approved: int
    published: int


class FunnelRates(BaseModel):
    submitted_to_g1: float | None
    g1_to_g2: float | None
    g2_to_approved: float | None
    approved_to_published: float | None
    end_to_end: float | None


class FunnelResponse(BaseModel):
    division: str
    days: int
    totals: FunnelTotals
    conversion_rates: FunnelRates


class TopSkillItem(BaseModel):
    id: str
    slug: str
    name: str
    install_count: int
    trending_score: float
    avg_rating: float


class TopSkillsResponse(BaseModel):
    skills: list[TopSkillItem]


class ExportJobResponse(BaseModel):
    id: str
    scope: str
    format: str
    status: str
    row_count: int | None = None
    created_at: str
    completed_at: str | None = None


class ExportRequestBody(BaseModel):
    scope: str
    format: str = "csv"
    filters: dict[str, Any] | None = None
```

---

## Task 8 — Analytics Router

**File:** `apps/api/skillhub/routers/analytics.py`

```python
"""Analytics endpoints — admin dashboard data pipeline.

Cache strategy
--------------
All endpoints attempt a Redis cache read first.
On miss, they fall back to a live DB query and return results without
writing to cache (cache writes are owned by the ARQ nightly job).
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from skillhub.cache import (
    TTL_FUNNEL,
    TTL_SUMMARY,
    TTL_TIMESERIES,
    cache_get,
    get_redis,
    key_funnel,
    key_summary,
    key_timeseries,
)
from skillhub.dependencies import get_db, require_platform_team
from skillhub.schemas.analytics import (
    FunnelResponse,
    SummaryResponse,
    TimeSeriesResponse,
    TopSkillsResponse,
)
from skillhub.services.analytics import (
    get_submission_funnel,
    get_summary,
    get_time_series,
    get_top_skills,
)

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryResponse)
async def analytics_summary(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],  # type: ignore[type-arg]
    division: str = "__all__",
) -> SummaryResponse:
    """Platform or division summary with deltas. Cached 5 min."""
    cached = await cache_get(redis, key_summary(division))
    if cached:
        return SummaryResponse(**cached)

    data = get_summary(db, division=division)
    return SummaryResponse(**data)


@router.get("/time-series", response_model=TimeSeriesResponse)
async def analytics_time_series(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],  # type: ignore[type-arg]
    days: int = Query(default=30, ge=7, le=365),
    division: str = "__all__",
) -> TimeSeriesResponse:
    """Daily metrics time series. Cached 1 hr."""
    cached = await cache_get(redis, key_timeseries(division, days))
    if cached:
        return TimeSeriesResponse(**cached)

    points = get_time_series(db, days=days, division=division)
    return TimeSeriesResponse(division=division, days=days, points=points)


@router.get("/submission-funnel", response_model=FunnelResponse)
async def analytics_funnel(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],  # type: ignore[type-arg]
    days: int = Query(default=30, ge=7, le=365),
    division: str = "__all__",
) -> FunnelResponse:
    """Submission funnel conversion rates. Cached 2 hr."""
    cached = await cache_get(redis, key_funnel(division, days))
    if cached:
        return FunnelResponse(**cached)

    data = get_submission_funnel(db, days=days, division=division)
    return FunnelResponse(**data)


@router.get("/top-skills", response_model=TopSkillsResponse)
async def analytics_top_skills(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
    limit: int = Query(default=10, ge=1, le=50),
) -> TopSkillsResponse:
    """Top skills by install count and trending score. No cache (cheap query)."""
    skills = get_top_skills(db, limit=limit)
    return TopSkillsResponse(skills=skills)
```

Register in `apps/api/skillhub/main.py`:
```python
from skillhub.routers import analytics
# ...
app.include_router(analytics.router)
```

---

## Task 9 — Export Service

**File:** `apps/api/skillhub/services/exports.py`

```python
"""Export service — request, rate-limit, generate CSV/JSON.

Rate limit: 5 exports per user per 24 hr window (checked against export_jobs table).
Generate runs as an ARQ task; writes to /tmp/skillhub-exports/.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from skillhub_db.models.analytics import ExportJob
from skillhub_db.models.skill import Skill
from skillhub_db.models.social import Install
from skillhub_db.models.user import User
from sqlalchemy import func, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

EXPORT_DIR = Path(os.environ.get("EXPORT_DIR", "/tmp/skillhub-exports"))
RATE_LIMIT = 5  # exports per user per 24 hr


def _check_rate_limit(db: Session, user_id: str) -> bool:
    """Return True if user is within rate limit (< RATE_LIMIT exports in last 24 hr)."""
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    count: int = db.execute(
        select(func.count(ExportJob.id))
        .where(ExportJob.requested_by == uuid.UUID(user_id))
        .where(ExportJob.created_at >= cutoff)
    ).scalar_one() or 0
    return count < RATE_LIMIT


def request_export(
    db: Session,
    user_id: str,
    scope: str,
    format: str,
    filters: dict[str, Any] | None,
) -> ExportJob:
    """Create an export_jobs row and enqueue ARQ task.

    Raises ValueError on rate limit exceeded or invalid scope/format.
    """
    valid_scopes = {"installs", "skills", "users", "submissions"}
    valid_formats = {"csv", "json"}

    if scope not in valid_scopes:
        raise ValueError(f"Invalid scope {scope!r}. Valid: {valid_scopes}")
    if format not in valid_formats:
        raise ValueError(f"Invalid format {format!r}. Valid: {valid_formats}")

    if not _check_rate_limit(db, user_id):
        raise ValueError(f"Rate limit exceeded: {RATE_LIMIT} exports per 24 hr")

    job = ExportJob(
        id=uuid.uuid4(),
        requested_by=uuid.UUID(user_id),
        scope=scope,
        format=format,
        filters=filters,
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue ARQ task — import here to avoid circular import at module load
    # The ARQ pool is accessed via app.state.arq (not available in sync context).
    # Callers (the router) must enqueue after calling this function.
    logger.info("Export job %s created: scope=%s format=%s", job.id, scope, format)
    return job


def get_export_job(db: Session, job_id: str) -> ExportJob | None:
    """Retrieve an export job by ID."""
    return db.get(ExportJob, uuid.UUID(job_id))


def generate_export(db: Session, job_id: str) -> None:
    """ARQ task body — generate the export file and update job status.

    Called from worker.py as a sync function.
    """
    job = db.get(ExportJob, uuid.UUID(job_id))
    if job is None:
        logger.error("Export job %s not found", job_id)
        return

    job.status = "running"
    db.commit()

    try:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        data = _fetch_scope_data(db, job.scope, job.filters or {})
        file_path = EXPORT_DIR / f"{job_id}.{job.format}"

        if job.format == "csv":
            _write_csv(data, file_path)
        else:
            _write_json(data, file_path)

        job.status = "completed"
        job.row_count = len(data)
        job.file_path = str(file_path)
        job.completed_at = datetime.now(UTC)
    except Exception as exc:
        logger.exception("Export job %s failed", job_id)
        job.status = "failed"
        job.error = str(exc)
        job.completed_at = datetime.now(UTC)

    db.commit()


def _fetch_scope_data(db: Session, scope: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Return rows for the requested scope."""
    if scope == "installs":
        rows = db.execute(
            select(
                Install.id,
                Install.skill_id,
                Install.user_id,
                Install.version,
                Install.method,
                Install.installed_at,
                Install.uninstalled_at,
            )
        ).all()
        return [
            {
                "id": str(r.id),
                "skill_id": str(r.skill_id),
                "user_id": str(r.user_id),
                "version": r.version,
                "method": r.method,
                "installed_at": r.installed_at.isoformat() if r.installed_at else None,
                "uninstalled_at": r.uninstalled_at.isoformat() if r.uninstalled_at else None,
            }
            for r in rows
        ]

    if scope == "skills":
        rows = db.query(Skill).all()
        return [
            {
                "id": str(r.id),
                "slug": r.slug,
                "name": r.name,
                "status": r.status,
                "install_count": r.install_count,
                "trending_score": float(r.trending_score),
                "published_at": r.published_at.isoformat() if r.published_at else None,
            }
            for r in rows
        ]

    if scope == "users":
        rows = db.query(User).all()
        return [
            {
                "id": str(r.id),
                "email": r.email,
                "username": r.username,
                "division": r.division,
                "role": r.role,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    # scope == "submissions" — import here to avoid circular dep at module level
    from skillhub_db.models.submission import Submission

    rows2 = db.query(Submission).all()
    return [
        {
            "id": str(r.id),
            "display_id": r.display_id,
            "name": r.name,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows2
    ]


def _write_csv(data: list[dict[str, Any]], path: Path) -> None:
    if not data:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)


def _write_json(data: list[dict[str, Any]], path: Path) -> None:
    path.write_text(json.dumps(data, indent=2))


def clean_expired_exports(older_than_hours: int = 48) -> int:
    """Delete export files older than threshold. Returns count deleted."""
    if not EXPORT_DIR.exists():
        return 0
    cutoff = datetime.now(UTC).timestamp() - (older_than_hours * 3600)
    deleted = 0
    for f in EXPORT_DIR.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink()
            deleted += 1
    logger.info("Cleaned %d expired export files", deleted)
    return deleted
```

---

## Task 10 — Export Router

**File:** `apps/api/skillhub/routers/exports.py`

```python
"""Export endpoints — request, status, download."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from skillhub.dependencies import get_db, require_platform_team
from skillhub.schemas.analytics import ExportJobResponse, ExportRequestBody
from skillhub.services.exports import get_export_job, request_export

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin/exports", tags=["exports"])


@router.post("", response_model=ExportJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    body: ExportRequestBody,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> ExportJobResponse:
    """Request a new data export. Returns 202 with job id."""
    user_id: str = current_user["user_id"]
    try:
        job = request_export(db, user_id=user_id, scope=body.scope, format=body.format, filters=body.filters)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    # Enqueue ARQ task
    arq_pool = getattr(request.app.state, "arq", None)
    if arq_pool is not None:
        await arq_pool.enqueue_job("generate_export", str(job.id))
    else:
        logger.warning("ARQ pool not available — export job %s queued but not enqueued", job.id)

    return ExportJobResponse(
        id=str(job.id),
        scope=job.scope,
        format=job.format,
        status=job.status,
        row_count=job.row_count,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


@router.get("/{job_id}", response_model=ExportJobResponse)
def get_export_status(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> ExportJobResponse:
    """Poll export job status."""
    job = get_export_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found")
    return ExportJobResponse(
        id=str(job.id),
        scope=job.scope,
        format=job.format,
        status=job.status,
        row_count=job.row_count,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


@router.get("/{job_id}/download")
def download_export(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> StreamingResponse:
    """Stream the export file. Only available when status == 'completed'."""
    job = get_export_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found")
    if job.status != "completed" or not job.file_path:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Export not ready (status={job.status})")

    file_path = Path(job.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Export file no longer available")

    media_type = "text/csv" if job.format == "csv" else "application/json"
    filename = f"skillhub-export-{job.scope}-{job_id[:8]}.{job.format}"

    def _iter():  # type: ignore[return]
        with file_path.open("rb") as f:
            while chunk := f.read(65536):
                yield chunk

    return StreamingResponse(
        _iter(),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

Register in `main.py`:
```python
from skillhub.routers import exports
app.include_router(exports.router)
```

---

## Task 11 — ARQ Worker

**File:** `apps/api/skillhub/worker.py`

```python
"""ARQ background worker.

Start with:  python -m skillhub.worker
Or via mise: mise run worker:start
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, date, datetime, timedelta

from arq import cron
from arq.connections import RedisSettings
from opentelemetry import trace

from skillhub.tracing import setup_tracing

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("skillhub.worker")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


def _parse_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into arq RedisSettings."""
    # arq RedisSettings accepts host, port, database, password separately
    import urllib.parse

    parsed = urllib.parse.urlparse(REDIS_URL)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or "0"),
        password=parsed.password,
    )


# ── Job: aggregate_daily_metrics ─────────────────────────────────────────────

async def aggregate_daily_metrics(ctx: dict) -> str:  # type: ignore[type-arg]
    """Nightly aggregation — runs at 02:00 UTC."""
    with tracer.start_as_current_span("worker.aggregate_daily_metrics") as span:
        yesterday = date.today() - timedelta(days=1)
        span.set_attribute("aggregation.date", yesterday.isoformat())
        logger.info("aggregate_daily_metrics: starting for %s", yesterday)

        from skillhub_db.session import SessionLocal
        from skillhub.services.analytics import run_daily_aggregation

        db = SessionLocal()
        try:
            rows = run_daily_aggregation(db, yesterday)
            span.set_attribute("aggregation.rows_upserted", rows)
            logger.info("aggregate_daily_metrics: %d rows upserted", rows)
        finally:
            db.close()

        # Bust summary caches for all divisions + __all__
        await _bust_summary_caches(ctx)
        return f"aggregated {rows} rows for {yesterday}"


async def _bust_summary_caches(ctx: dict) -> None:  # type: ignore[type-arg]
    """Delete all analytics:summary:* keys from Redis."""
    from skillhub.cache import cache_delete_pattern

    redis = ctx.get("redis")
    if redis is None:
        logger.warning("No Redis in ARQ ctx — skipping cache bust")
        return
    deleted = await cache_delete_pattern(redis, "analytics:summary:*")
    logger.info("Cache bust: deleted %d summary keys", deleted)


# ── Job: recalculate_trending ─────────────────────────────────────────────────

async def recalculate_trending(ctx: dict) -> str:  # type: ignore[type-arg]
    """Recalculate trending scores — runs at 02:30 UTC."""
    with tracer.start_as_current_span("worker.recalculate_trending") as span:
        logger.info("recalculate_trending: starting")

        from skillhub_db.session import SessionLocal
        from skillhub.services.skills import recalculate_trending_scores

        db = SessionLocal()
        try:
            count = recalculate_trending_scores(db)
            span.set_attribute("trending.skills_updated", count)
            logger.info("recalculate_trending: %d skills updated", count)
        finally:
            db.close()

        # Bust top-skills cache
        redis = ctx.get("redis")
        if redis is not None:
            from skillhub.cache import cache_delete_pattern
            await cache_delete_pattern(redis, "analytics:top_skills:*")

        return f"updated trending for {count} skills"


# ── Job: clean_expired_exports ────────────────────────────────────────────────

async def clean_expired_exports(ctx: dict) -> str:  # type: ignore[type-arg]
    """Clean export files older than 48 hr — runs at 03:00 UTC."""
    with tracer.start_as_current_span("worker.clean_expired_exports"):
        logger.info("clean_expired_exports: starting")

        from skillhub.services.exports import clean_expired_exports as _clean

        deleted = _clean(older_than_hours=48)
        return f"deleted {deleted} expired export files"


# ── Job: generate_export (enqueued on demand) ─────────────────────────────────

async def generate_export(ctx: dict, job_id: str) -> str:  # type: ignore[type-arg]
    """Generate an export file for a queued job."""
    with tracer.start_as_current_span("worker.generate_export") as span:
        span.set_attribute("export.job_id", job_id)
        logger.info("generate_export: job_id=%s", job_id)

        from skillhub_db.session import SessionLocal
        from skillhub.services.exports import generate_export as _gen

        db = SessionLocal()
        try:
            _gen(db, job_id)
        finally:
            db.close()

        return f"export {job_id} complete"


# ── Worker settings ──────────────────────────────────────────────────────────

class WorkerSettings:
    """ARQ worker configuration."""

    functions = [generate_export]

    cron_jobs = [
        cron(aggregate_daily_metrics, hour=2, minute=0),
        cron(recalculate_trending, hour=2, minute=30),
        cron(clean_expired_exports, hour=3, minute=0),
    ]

    redis_settings = _parse_redis_settings()
    max_jobs = 4
    job_timeout = 600  # 10 minutes

    on_startup = _on_startup
    on_shutdown = _on_shutdown


async def _on_startup(ctx: dict) -> None:  # type: ignore[type-arg]
    """Worker startup: configure OTel tracing."""
    from skillhub.config import Settings
    settings = Settings()
    setup_tracing(settings)
    logger.info("ARQ worker started — Redis: %s", REDIS_URL)


async def _on_shutdown(ctx: dict) -> None:  # type: ignore[type-arg]
    logger.info("ARQ worker shutting down")


# Patch WorkerSettings after function definitions (Python forward reference workaround)
WorkerSettings.on_startup = _on_startup  # type: ignore[attr-defined]
WorkerSettings.on_shutdown = _on_shutdown  # type: ignore[attr-defined]


if __name__ == "__main__":
    import asyncio
    from arq import run_worker
    run_worker(WorkerSettings)
```

**Entry point:** `python -m skillhub.worker` calls `run_worker(WorkerSettings)`.

---

## Task 12 — Backfill Script

**File:** `apps/api/skillhub/scripts/backfill_metrics.py`

```python
"""Backfill daily_metrics from earliest install date to yesterday.

Usage:
    python -m skillhub.scripts.backfill_metrics
    mise run db:aggregate:backfill
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import UTC, date, datetime, timedelta

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


def main() -> None:
    """Iterate day-by-day from earliest install to yesterday and aggregate."""
    from skillhub_db.session import SessionLocal
    from skillhub_db.models.social import Install
    from skillhub.services.analytics import run_daily_aggregation
    from sqlalchemy import func, select

    db = SessionLocal()
    try:
        # Find earliest install date
        earliest_dt: datetime | None = db.execute(
            select(func.min(Install.installed_at))
        ).scalar_one_or_none()

        if earliest_dt is None:
            logger.info("No installs found — nothing to backfill")
            return

        start_date = earliest_dt.date()
        end_date = date.today() - timedelta(days=1)

        if start_date > end_date:
            logger.info("start_date %s is after end_date %s — nothing to backfill", start_date, end_date)
            return

        logger.info("Backfilling from %s to %s", start_date, end_date)
        current = start_date
        total_days = 0

        while current <= end_date:
            logger.info("Aggregating %s ...", current)
            try:
                rows = run_daily_aggregation(db, current)
                logger.info("  %d rows upserted", rows)
            except Exception:
                logger.exception("  Failed to aggregate %s — continuing", current)
            current += timedelta(days=1)
            total_days += 1

        logger.info("Backfill complete: %d days processed", total_days)
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

**Note:** each call to `run_daily_aggregation()` commits its own transaction. This keeps individual day failures isolated.

---

## Task 13 — FastAPI Lifespan (modify main.py)

Replace the existing `create_app()` function with a version that uses `@asynccontextmanager` lifespan:

```python
"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from skillhub.config import Settings
from skillhub.routers import admin, analytics, auth, exports, flags, health, skills, social, submissions, users

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create and teardown ARQ pool + Redis pool."""
    settings: Settings = app.state.settings

    # ── Redis pool ────────────────────────────────────────────────────────────
    redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
    app.state.redis = aioredis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    logger.info("Redis pool created: %s", redis_url)

    # ── ARQ pool ──────────────────────────────────────────────────────────────
    try:
        from arq import create_pool
        from arq.connections import RedisSettings
        import urllib.parse

        parsed = urllib.parse.urlparse(redis_url)
        arq_settings = RedisSettings(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            database=int(parsed.path.lstrip("/") or "0"),
            password=parsed.password,
        )
        app.state.arq = await create_pool(arq_settings)
        logger.info("ARQ pool created")
    except Exception:
        app.state.arq = None
        logger.warning("ARQ pool creation failed — exports will queue without enqueuing", exc_info=True)

    yield

    # ── Teardown ──────────────────────────────────────────────────────────────
    await app.state.redis.aclose()
    logger.info("Redis pool closed")
    if app.state.arq is not None:
        await app.state.arq.aclose()
        logger.info("ARQ pool closed")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    # Store settings before lifespan runs (lifespan reads app.state.settings)
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # OpenTelemetry setup (unchanged)
    from skillhub.tracing import setup_tracing
    setup_tracing(settings)
    # ... existing OTel instrumentation blocks ...

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(skills.router)
    app.include_router(users.router)
    app.include_router(social.router)
    app.include_router(submissions.router)
    app.include_router(flags.router)
    app.include_router(admin.router)
    app.include_router(analytics.router)
    app.include_router(exports.router)
    return app


app = create_app()
```

**Add to `config.py`:**
```python
redis_url: str = "redis://localhost:6379/0"
```

---

## Task 14 — Connection Pool Tuning

**File:** `libs/db/skillhub_db/session.py`

```python
"""Database session management."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://skillhub:skillhub@localhost:5433/skillhub")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, closing it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Rationale:**
- `pool_size=10`: steady-state concurrent requests
- `max_overflow=20`: burst headroom before blocking
- `pool_timeout=30`: fail fast on pool exhaustion rather than hang
- `pool_recycle=1800`: recycle connections every 30 min to avoid stale TCP state
- `pool_pre_ping=True`: validate connection before use (prevents "server closed connection" errors after idle periods)

---

## Task 15 — Docker Compose Additions

Add to `docker-compose.yml`:

```yaml
  arq-worker:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
    command: python -m skillhub.worker
    environment:
      DATABASE_URL: postgresql://skillhub:skillhub@postgres:5432/skillhub
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET: ${JWT_SECRET:-dev-secret-change-me}
      STUB_AUTH_ENABLED: ${STUB_AUTH_ENABLED:-true}
      EXPORT_DIR: /exports
      OTEL_EXPORTER_OTLP_ENDPOINT: http://jaeger:4317
      OTEL_SERVICE_NAME: skillhub-worker
      OTEL_TRACES_ENABLED: "true"
    volumes:
      - ./apps/api:/app/apps/api
      - ./libs:/app/libs
      - export-staging:/exports
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      jaeger:
        condition: service_started
    restart: unless-stopped
```

Add the `export-staging` volume mount to the `api` service:
```yaml
  api:
    # ... existing config ...
    volumes:
      - ./apps/api:/app/apps/api
      - ./libs:/app/libs
      - export-staging:/exports   # ← add this
```

Add to the `volumes:` block:
```yaml
volumes:
  pgdata:
  export-staging:
```

---

## Task 16 — mise.toml Additions

Add these tasks to `mise.toml`:

```toml
# ─── Worker ───────────────────────────────────────────────────────────────────

[tasks."worker:start"]
description = "Start ARQ worker (foreground)"
run = "python -m skillhub.worker"
env = { PYTHONPATH = "apps/api:libs/db:libs/python-common" }

[tasks."worker:burst"]
description = "Run ARQ worker in burst mode (process queue + exit)"
run = "arq skillhub.worker.WorkerSettings --burst"
env = { PYTHONPATH = "apps/api:libs/db:libs/python-common" }

# ─── Aggregation ──────────────────────────────────────────────────────────────

[tasks."db:aggregate"]
description = "Run daily aggregation for yesterday"
run = """
python -c "
from datetime import date, timedelta
from skillhub_db.session import SessionLocal
from skillhub.services.analytics import run_daily_aggregation
db = SessionLocal()
try:
    rows = run_daily_aggregation(db, date.today() - timedelta(days=1))
    print(f'Aggregated {rows} rows')
finally:
    db.close()
"
"""
env = { PYTHONPATH = "apps/api:libs/db:libs/python-common" }

[tasks."db:aggregate:backfill"]
description = "Backfill daily_metrics from earliest install to yesterday"
run = "python -m skillhub.scripts.backfill_metrics"
env = { PYTHONPATH = "apps/api:libs/db:libs/python-common" }

# ─── Exports ─────────────────────────────────────────────────────────────────

[tasks."export:clean"]
description = "Clean export files older than 48 hr"
run = """
python -c "
from skillhub.services.exports import clean_expired_exports
deleted = clean_expired_exports()
print(f'Deleted {deleted} files')
"
"""
env = { PYTHONPATH = "apps/api:libs/db:libs/python-common" }
```

---

## Task 17 — pyproject.toml: Add ARQ + Redis Dependencies

Add to `apps/api/pyproject.toml` dependencies:

```toml
dependencies = [
  # ... existing ...
  "arq>=0.25",
  "redis[hiredis]>=5.0",
]
```

The `hiredis` extra gives a C-accelerated parser — strongly recommended for high-throughput Redis usage.

---

## Test Suite

### File: `apps/api/tests/test_analytics_service.py`

```python
"""Tests for analytics aggregation service."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from skillhub.services.analytics import (
    _compute_dau,
    _compute_funnel,
    get_submission_funnel,
    get_summary,
    get_time_series,
    get_top_skills,
    run_daily_aggregation,
)
from skillhub_db.models.analytics import DailyMetrics
from skillhub_db.models.audit import AuditLog
from skillhub_db.models.division import Division
from skillhub_db.models.skill import Skill
from skillhub_db.models.social import Install
from skillhub_db.models.submission import Submission, SubmissionStatus
from skillhub_db.models.user import User


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def division(db: Session) -> Division:
    d = Division(slug="eng", name="Engineering")
    db.add(d)
    db.commit()
    return d


@pytest.fixture
def user(db: Session, division: Division) -> User:
    u = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        name="Test User",
        division=division.slug,
        role="engineer",
    )
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def skill(db: Session, user: User) -> Skill:
    s = Skill(
        id=uuid.uuid4(),
        slug="my-skill",
        name="My Skill",
        short_desc="A test skill",
        category="tools",
        author_id=user.id,
        status="published",
        install_count=5,
        trending_score=1.5,
    )
    db.add(s)
    db.commit()
    return s


@pytest.fixture
def install(db: Session, skill: Skill, user: User) -> Install:
    today = datetime.now(UTC)
    i = Install(
        id=uuid.uuid4(),
        skill_id=skill.id,
        user_id=user.id,
        version="1.0.0",
        method="claude-code",
        installed_at=today,
    )
    db.add(i)
    db.commit()
    return i


# ── Tests ────────────────────────────────────────────────────────────────────

class TestRunDailyAggregation:
    def test_idempotent_upsert(self, db: Session, install: Install, division: Division) -> None:
        """Running aggregation twice for same date should not raise and should update row."""
        target = date.today()
        rows1 = run_daily_aggregation(db, target)
        rows2 = run_daily_aggregation(db, target)
        assert rows1 >= 1
        assert rows2 >= 1  # second run upserts same rows

    def test_creates_all_row(self, db: Session, install: Install, division: Division) -> None:
        """Aggregation must create a '__all__' row."""
        target = date.today()
        run_daily_aggregation(db, target)
        row = db.get(DailyMetrics, {"metric_date": target, "division_slug": "__all__"})
        assert row is not None

    def test_creates_division_row(self, db: Session, install: Install, division: Division) -> None:
        target = date.today()
        run_daily_aggregation(db, target)
        row = db.get(DailyMetrics, {"metric_date": target, "division_slug": division.slug})
        assert row is not None

    def test_new_installs_counted(self, db: Session, install: Install, division: Division) -> None:
        target = date.today()
        run_daily_aggregation(db, target)
        row = db.get(DailyMetrics, {"metric_date": target, "division_slug": "__all__"})
        assert row is not None
        assert row.new_installs >= 1


class TestComputeDAU:
    def test_dau_from_audit_log(self, db: Session, user: User, division: Division) -> None:
        today = date.today()
        entry = AuditLog(
            id=uuid.uuid4(),
            event_type="skill.install",
            actor_id=user.id,
            created_at=datetime.now(UTC),
        )
        db.add(entry)
        db.commit()

        dau = _compute_dau(db, today, "__all__")
        assert dau >= 1

    def test_dau_excludes_null_actors(self, db: Session, division: Division) -> None:
        entry = AuditLog(
            id=uuid.uuid4(),
            event_type="skill.install",
            actor_id=None,
            created_at=datetime.now(UTC),
        )
        db.add(entry)
        db.commit()

        dau = _compute_dau(db, date.today(), "__all__")
        assert dau == 0

    def test_dau_per_division(self, db: Session, user: User, division: Division) -> None:
        entry = AuditLog(
            id=uuid.uuid4(),
            event_type="skill.fork",
            actor_id=user.id,
            created_at=datetime.now(UTC),
        )
        db.add(entry)
        db.commit()

        dau_eng = _compute_dau(db, date.today(), "eng")
        dau_other = _compute_dau(db, date.today(), "other-div")
        assert dau_eng >= 1
        assert dau_other == 0


class TestGetSummary:
    def test_returns_unavailable_when_no_data(self, db: Session) -> None:
        result = get_summary(db, division="nonexistent")
        assert result["available"] is False

    def test_returns_summary_when_data_exists(self, db: Session, install: Install, division: Division) -> None:
        yesterday = date.today() - timedelta(days=1)
        dm = DailyMetrics(
            metric_date=yesterday,
            division_slug="__all__",
            dau=42,
            active_installs=100,
            new_installs=5,
            new_submissions=2,
            published_skills=10,
        )
        db.add(dm)
        db.commit()

        result = get_summary(db)
        assert result["available"] is True
        assert result["dau"] == 42


class TestGetTimeSeries:
    def test_returns_empty_list_when_no_data(self, db: Session) -> None:
        result = get_time_series(db, days=7)
        assert result == []

    def test_ordered_ascending(self, db: Session) -> None:
        for i in range(3):
            dm = DailyMetrics(
                metric_date=date.today() - timedelta(days=i + 1),
                division_slug="__all__",
            )
            db.add(dm)
        db.commit()

        result = get_time_series(db, days=7)
        dates = [r["date"] for r in result]
        assert dates == sorted(dates)


class TestGetTopSkills:
    def test_returns_top_by_install_count(self, db: Session, skill: Skill) -> None:
        result = get_top_skills(db, limit=5)
        assert len(result) >= 1
        assert result[0]["install_count"] >= 1
```

### File: `apps/api/tests/test_analytics_router.py`

```python
"""Tests for analytics API endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub_db.models.analytics import DailyMetrics


class TestSummaryEndpoint:
    def test_requires_platform_team(self, client: TestClient) -> None:
        """Unauthenticated request must return 401."""
        resp = client.get("/api/v1/admin/analytics/summary")
        assert resp.status_code == 401

    def test_returns_summary(self, client: TestClient, platform_token: str, db) -> None:
        yesterday = date.today() - timedelta(days=1)
        dm = DailyMetrics(metric_date=yesterday, division_slug="__all__", dau=99)
        db.add(dm)
        db.commit()

        with patch("skillhub.routers.analytics.cache_get", new=AsyncMock(return_value=None)):
            resp = client.get(
                "/api/v1/admin/analytics/summary",
                headers={"Authorization": f"Bearer {platform_token}"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert data["dau"] == 99

    def test_returns_cached_result(self, client: TestClient, platform_token: str) -> None:
        cached = {
            "division": "__all__",
            "available": True,
            "as_of": "2026-03-22",
            "dau": 42,
            "active_installs": 100,
            "new_installs_today": 5,
            "new_submissions_today": 2,
            "published_skills": 10,
            "deltas": None,
        }
        with patch("skillhub.routers.analytics.cache_get", new=AsyncMock(return_value=cached)):
            resp = client.get(
                "/api/v1/admin/analytics/summary",
                headers={"Authorization": f"Bearer {platform_token}"},
            )
        assert resp.status_code == 200
        assert resp.json()["dau"] == 42


class TestTimeSeriesEndpoint:
    def test_days_validation(self, client: TestClient, platform_token: str) -> None:
        with patch("skillhub.routers.analytics.cache_get", new=AsyncMock(return_value=None)):
            resp = client.get(
                "/api/v1/admin/analytics/time-series?days=3",
                headers={"Authorization": f"Bearer {platform_token}"},
            )
        assert resp.status_code == 422  # days must be >= 7


class TestExportEndpoints:
    def test_create_export_rate_limit(self, client: TestClient, platform_token: str, db) -> None:
        """6th export in 24 hr must return 400."""
        from skillhub_db.models.analytics import ExportJob
        from skillhub_db.models.user import User

        # Create 5 existing export jobs
        user = db.query(User).filter(User.is_platform_team == True).first()
        if user:
            for _ in range(5):
                job = ExportJob(
                    id=uuid.uuid4(),
                    requested_by=user.id,
                    scope="skills",
                    format="csv",
                    status="completed",
                    created_at=datetime.now(UTC),
                )
                db.add(job)
            db.commit()

        resp = client.post(
            "/api/v1/admin/exports",
            json={"scope": "skills", "format": "csv"},
            headers={"Authorization": f"Bearer {platform_token}"},
        )
        # Rate limited if user existed
        assert resp.status_code in (202, 400)

    def test_invalid_scope_returns_400(self, client: TestClient, platform_token: str) -> None:
        resp = client.post(
            "/api/v1/admin/exports",
            json={"scope": "invalid_scope", "format": "csv"},
            headers={"Authorization": f"Bearer {platform_token}"},
        )
        assert resp.status_code == 400
```

### File: `apps/api/tests/test_cache.py`

```python
"""Tests for Redis cache helpers."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skillhub.cache import (
    TTL_SUMMARY,
    cache_delete_pattern,
    cache_get,
    cache_set,
    key_summary,
    key_timeseries,
)


@pytest.mark.asyncio
class TestCacheHelpers:
    async def test_cache_get_returns_none_on_miss(self) -> None:
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        result = await cache_get(redis, "missing:key")
        assert result is None

    async def test_cache_get_deserializes_json(self) -> None:
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=json.dumps({"dau": 42}))
        result = await cache_get(redis, "analytics:summary:__all__")
        assert result == {"dau": 42}

    async def test_cache_get_returns_none_on_error(self) -> None:
        redis = AsyncMock()
        redis.get = AsyncMock(side_effect=ConnectionError("redis down"))
        result = await cache_get(redis, "any:key")
        assert result is None  # swallows error

    async def test_cache_set_serializes_and_stores(self) -> None:
        redis = AsyncMock()
        redis.setex = AsyncMock()
        await cache_set(redis, "k", {"x": 1}, ttl=300)
        redis.setex.assert_called_once()
        args = redis.setex.call_args[0]
        assert args[0] == "k"
        assert args[1] == 300

    async def test_cache_set_swallows_errors(self) -> None:
        redis = AsyncMock()
        redis.setex = AsyncMock(side_effect=ConnectionError("redis down"))
        # Should not raise
        await cache_set(redis, "k", {}, ttl=300)

    async def test_cache_delete_pattern(self) -> None:
        redis = AsyncMock()
        redis.keys = AsyncMock(return_value=["analytics:summary:__all__", "analytics:summary:eng"])
        redis.delete = AsyncMock(return_value=2)
        count = await cache_delete_pattern(redis, "analytics:summary:*")
        assert count == 2


class TestKeyConventions:
    def test_summary_key(self) -> None:
        assert key_summary("__all__") == "analytics:summary:__all__"
        assert key_summary("eng") == "analytics:summary:eng"

    def test_timeseries_key(self) -> None:
        assert key_timeseries("__all__", 30) == "analytics:timeseries:__all__:30"
```

### File: `apps/api/tests/test_exports_service.py`

```python
"""Tests for export service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from skillhub.services.exports import clean_expired_exports, generate_export, request_export, RATE_LIMIT
from skillhub_db.models.analytics import ExportJob
from skillhub_db.models.division import Division
from skillhub_db.models.user import User


@pytest.fixture
def platform_user(db: Session) -> User:
    d = Division(slug="platform", name="Platform")
    db.add(d)
    db.flush()
    u = User(
        id=uuid.uuid4(),
        email="platform@example.com",
        username="platform",
        name="Platform Admin",
        division="platform",
        role="admin",
        is_platform_team=True,
    )
    db.add(u)
    db.commit()
    return u


class TestRequestExport:
    def test_creates_queued_job(self, db: Session, platform_user: User) -> None:
        job = request_export(db, str(platform_user.id), "skills", "csv", None)
        assert job.status == "queued"
        assert job.scope == "skills"
        assert job.format == "csv"

    def test_invalid_scope_raises(self, db: Session, platform_user: User) -> None:
        with pytest.raises(ValueError, match="Invalid scope"):
            request_export(db, str(platform_user.id), "bad_scope", "csv", None)

    def test_invalid_format_raises(self, db: Session, platform_user: User) -> None:
        with pytest.raises(ValueError, match="Invalid format"):
            request_export(db, str(platform_user.id), "skills", "xlsx", None)

    def test_rate_limit_enforced(self, db: Session, platform_user: User) -> None:
        for _ in range(RATE_LIMIT):
            request_export(db, str(platform_user.id), "skills", "csv", None)

        with pytest.raises(ValueError, match="Rate limit exceeded"):
            request_export(db, str(platform_user.id), "skills", "csv", None)


class TestGenerateExport:
    def test_generates_csv(self, db: Session, platform_user: User, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setenv("EXPORT_DIR", str(tmp_path))
        import skillhub.services.exports as exports_module
        exports_module.EXPORT_DIR = tmp_path

        job = request_export(db, str(platform_user.id), "skills", "csv", None)
        generate_export(db, str(job.id))

        db.refresh(job)
        assert job.status == "completed"
        assert job.file_path is not None
        assert Path(job.file_path).exists()

    def test_handles_missing_job(self, db: Session) -> None:
        # Should not raise — logs error and returns
        generate_export(db, str(uuid.uuid4()))


class TestCleanExpiredExports:
    def test_deletes_old_files(self, tmp_path: Path, monkeypatch) -> None:
        import skillhub.services.exports as exports_module
        exports_module.EXPORT_DIR = tmp_path

        old_file = tmp_path / "old.csv"
        old_file.write_text("data")
        import os, time
        old_time = time.time() - (49 * 3600)
        os.utime(old_file, (old_time, old_time))

        new_file = tmp_path / "new.csv"
        new_file.write_text("data")

        deleted = clean_expired_exports(older_than_hours=48)
        assert deleted == 1
        assert not old_file.exists()
        assert new_file.exists()
```

---

## Verification Checklist

Run these in order after implementation:

```bash
# 1. Apply migration
mise run db:migrate

# 2. Run all API tests with coverage gate
mise run test:api:coverage
# Expected: ≥ 80% coverage, all tests green

# 3. Type check
mise run typecheck:api

# 4. Lint
mise run lint:api

# 5. Build arq-worker Docker image
docker compose build arq-worker

# 6. Verify worker connects to Redis (burst mode — exits after processing queue)
mise run worker:burst
# Expected: "ARQ worker started — Redis: redis://...", then exits cleanly

# 7. Run backfill (dry run with empty DB is fine)
mise run db:aggregate:backfill

# 8. Smoke test analytics endpoints (requires dev server running)
mise run dev:api &
curl -s http://localhost:8000/api/v1/admin/analytics/summary \
  -H "Authorization: Bearer <platform_token>" | python -m json.tool
```

---

## Common Pitfalls

### 1. `__all__` sentinel and PostgreSQL composite PK

NULL != NULL in a composite PK. Never use `NULL` for the platform-wide row — always use the string `'__all__'`.

### 2. ARQ cron vs. ARQ function

`cron()` jobs run at a UTC schedule; they are NOT enqueued via `arq_pool.enqueue_job()`. Only `functions` listed in `WorkerSettings.functions` can be enqueued. `cron_jobs` are separate. Ensure `generate_export` is in `functions` and the three nightly jobs are in `cron_jobs`.

### 3. Redis decode_responses=True

The `aioredis.from_url(..., decode_responses=True)` flag means all Redis values are returned as Python `str`, not `bytes`. This is required for `json.loads()` to work without extra decoding. Ensure the ARQ pool uses a separate connection (ARQ manages its own pool internally).

### 4. OTel forward reference in worker.py

Python requires functions to be defined before they are referenced. The `WorkerSettings` class references `_on_startup` and `_on_shutdown` which must be defined before the class body. The patch pattern at the bottom handles this.

### 5. Session lifecycle in ARQ jobs

ARQ jobs are async but `SessionLocal()` is synchronous. Create a new session at the start of each job and close it in a `finally` block. Do NOT use `get_db()` (which is a FastAPI dependency generator) in worker code.

### 6. Export download vs. StreamingResponse

`StreamingResponse` with a generator function does not hold the file handle open after the response completes. The generator reads in 64 KB chunks to keep memory bounded for large exports.

### 7. `pool_pre_ping=True` performance

`pool_pre_ping` adds a lightweight `SELECT 1` before handing a connection from the pool. In high-throughput scenarios this adds ~0.1 ms per request. The tradeoff is correct — it prevents cryptic "server closed connection" errors after idle periods that are much more expensive to debug.

---

## Dependencies Reference

Add to `apps/api/pyproject.toml`:

```toml
"arq>=0.25",
"redis[hiredis]>=5.0",
```

Both packages must be available in the `arq-worker` Docker image, which uses the same `Dockerfile` as the `api` service.

---

## File Creation Summary

| File | Action |
|------|--------|
| `libs/db/migrations/versions/XXXX_analytics_engine.py` | Create (Alembic) |
| `libs/db/skillhub_db/models/analytics.py` | Create |
| `libs/db/skillhub_db/models/__init__.py` | Edit (register models) |
| `apps/api/skillhub/cache.py` | Create |
| `apps/api/skillhub/services/analytics.py` | Create |
| `apps/api/skillhub/services/exports.py` | Create |
| `apps/api/skillhub/schemas/analytics.py` | Create |
| `apps/api/skillhub/routers/analytics.py` | Create |
| `apps/api/skillhub/routers/exports.py` | Create |
| `apps/api/skillhub/worker.py` | Create |
| `apps/api/skillhub/scripts/__init__.py` | Create (empty) |
| `apps/api/skillhub/scripts/backfill_metrics.py` | Create |
| `apps/api/skillhub/main.py` | Edit (lifespan, register routers) |
| `apps/api/skillhub/config.py` | Edit (add `redis_url`) |
| `libs/db/skillhub_db/session.py` | Edit (pool tuning) |
| `docker-compose.yml` | Edit (arq-worker, export-staging) |
| `mise.toml` | Edit (5 new tasks) |
| `apps/api/pyproject.toml` | Edit (arq, redis deps) |
| `apps/api/tests/test_analytics_service.py` | Create |
| `apps/api/tests/test_analytics_router.py` | Create |
| `apps/api/tests/test_cache.py` | Create |
| `apps/api/tests/test_exports_service.py` | Create |
