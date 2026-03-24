# Async Callsite Audit — FastAPI → Flask Migration

**Date:** 2026-03-23
**Status:** Complete
**Verdict:** All async code is sync-convertible. No third-party async-only dependencies.

## Summary

| Location | Async Functions | Sync-Convertible | Strategy |
|----------|----------------|-------------------|----------|
| services/llm_judge.py | 1 | YES | httpx.AsyncClient → httpx.Client |
| services/submissions.py | 1 | YES | Depends on llm_judge sync first |
| cache.py | 3 | YES | aioredis → redis-py (sync) |
| routers/submissions.py | 1 | YES | Depends on run_gate2_scan sync |
| worker.py | 3 | YES | Remove async keyword (no real async I/O) |
| **Total source** | **9** | **9/9** | |
| tests/ | 18 | YES | Remove @pytest.mark.asyncio |

## Critical Dependency Chain

```
1. llm_judge.py: evaluate()          ← httpx.AsyncClient → httpx.Client
   ↓
2. submissions.py: run_gate2_scan()  ← remove await, becomes sync
   ↓
3. routers/submissions.py: scan_submission()  ← remove async def
```

Convert in this order. Step 1 unblocks everything downstream.

## Detailed Inventory

### Tier 1 — Root Cause (convert first)

#### `apps/api/skillhub/services/llm_judge.py:34`
- **Function:** `async def evaluate(self, content: str) -> dict`
- **Why async:** Uses `httpx.AsyncClient` for HTTP POST to LLM router
- **Sync equivalent:** `httpx.Client` (symmetric API, mechanical conversion)
- **Change:** `async with httpx.AsyncClient()` → `with httpx.Client()`, remove `await`
- **Risk:** LOW — httpx sync/async APIs are identical

### Tier 2 — Cascading (converts automatically after Tier 1)

#### `apps/api/skillhub/services/submissions.py:207`
- **Function:** `async def run_gate2_scan(db, submission_id)`
- **Why async:** Calls `await judge.evaluate(content)`
- **After Tier 1:** Remove `async def` → `def`, remove `await` on evaluate call
- **Also touches DB:** Queries Submission, writes SubmissionGateResult + AuditLog, calls db.commit()
- **Risk:** LOW — DB calls are already sync

#### `apps/api/skillhub/routers/submissions.py:111`
- **Function:** `async def scan_submission(...)` (route handler)
- **Why async:** Calls `await run_gate2_scan()`
- **After Tier 2:** Remove `async def` → `def`, remove `await`
- **Risk:** LOW

### Tier 3 — Independent (convert anytime)

#### `apps/api/skillhub/cache.py:21`
- **Function:** `async def get_redis()` — FastAPI dependency
- **Why async:** Convention; no actual async I/O
- **Change:** Remove `async` keyword
- **Risk:** NONE

#### `apps/api/skillhub/cache.py:26`
- **Function:** `async def cache_get(redis, key, ttl, factory)`
- **Why async:** `await redis.get()`, `await redis.setex()`
- **Change:** Replace async redis client with sync `redis-py`; remove `await`
- **Risk:** LOW — redis-py has identical method signatures

#### `apps/api/skillhub/cache.py:36`
- **Function:** `async def cache_set(redis, key, value, ttl)`
- **Why async:** `await redis.setex()`
- **Change:** Same as cache_get
- **Risk:** LOW

### Tier 4 — Worker (leave as-is OR convert)

#### `apps/api/skillhub/worker.py:13,20,26`
- **Functions:** `aggregate_daily_metrics()`, `recalculate_trending()`, `clean_expired_exports()`
- **Why async:** ARQ requires async task signatures
- **Reality:** No actual async I/O in any of them (logging, os.listdir, os.remove)
- **Decision:** Leave as-is if staying on ARQ (ARQ manages its own event loop). Convert to sync only if switching to Celery/RQ.
- **Risk:** NONE — worker is process-external to Flask

## Test Files Requiring Updates

| Test File | Async Tests | Change |
|-----------|------------|--------|
| test_cache.py | 5 | Remove @pytest.mark.asyncio, async/await |
| test_llm_judge.py | 5 | Remove @pytest.mark.asyncio, async/await |
| test_submission_pipeline_fixes.py | 8 | Remove @pytest.mark.asyncio, async/await |
| test_submissions_service.py | 2 | Remove @pytest.mark.asyncio, async/await |
| test_worker.py | 0 (uses asyncio.run()) | Call functions directly |

## Libraries Affected

| Current | Replacement | Change Type |
|---------|-------------|-------------|
| httpx.AsyncClient | httpx.Client | Import swap |
| aioredis / async redis | redis-py (sync) | Package swap |
| pytest-asyncio | (remove) | Dev dependency removal |

## Shared Libraries

- **libs/db:** Zero async. Fully sync. No changes needed.
- **libs/python-common:** Zero async. No changes needed.

## Decision

**Strategy: Full sync conversion (not isolation wrapper).**

Rationale: The async surface is exactly one function deep (llm_judge.evaluate). Converting it to sync with httpx.Client is a ~20 line change that eliminates all downstream async. An isolation wrapper (asyncio.run() in threads) adds runtime complexity for zero benefit when the sync equivalent is trivial.
