# Phase 2: Auth Endpoints + Async Sync Conversion — Implementation Guide

**Phase:** 2 of N
**Prerequisite:** Phase 1 complete (Flask skeleton with app factory, `before_request` auth middleware, health endpoint, validation helpers, test infrastructure)
**Estimated Time:** 2-3 hours (three tasks, 15-45 min each)
**Branch:** `feat/phase2-auth-async`

## Starting State

After Phase 1, the Flask app (`apps/api/`) has:
- `create_app()` factory using APIFlask
- `before_request` hook that decodes JWT and sets `g.current_user`
- `PUBLIC_ENDPOINTS` frozenset (currently: `"health.health_check"`)
- `validated_body()` and `validated_query()` decorators
- `session_factory` parameter on `create_app()` for test injection
- Health endpoint + test infrastructure with Flask test client
- `conftest.py` with `make_token()`, `_make_settings()`, test fixtures

The FastAPI reference app (`apps/api/skillhub/`) is preserved and readable.

## Architecture Decisions (from ADR-001)

- **Auth:** `before_request` hook fails closed; `PUBLIC_ENDPOINTS` is an allowlist
- **Stub Auth:** Separate blueprint, conditionally registered. Never imported in production.
- **Async:** Full sync conversion. `httpx.AsyncClient` -> `httpx.Client`, async redis -> sync `redis-py`
- **Worker:** Left async (ARQ manages its own event loop)

---

## Task 2.1: Port Auth Blueprint

**Time estimate:** 30-45 minutes
**Files to create/modify in `apps/api/`:**
- `skillhub/blueprints/auth.py` (new)
- `skillhub/blueprints/stub_auth.py` (new)
- `skillhub/app.py` (modify — register blueprints, update `PUBLIC_ENDPOINTS`)
- `tests/test_auth.py` (new — Flask test client)

### Context

The FastAPI auth router lives at `apps/api/skillhub/routers/auth.py`. It contains:
1. **Stub auth** — `POST /auth/token` (issue JWT), `GET /auth/dev-users` (list test identities)
2. **Auth me** — `GET /auth/me` (return `g.current_user` claims)
3. **OAuth placeholders** — `GET /auth/oauth/{provider}` (redirect URL), `GET /auth/oauth/{provider}/callback` (501)

In Flask, these split into two blueprints per ADR-001 Section 7:
- `auth_bp` — always registered (contains `/auth/me` and OAuth routes)
- `stub_auth_bp` — conditionally registered only when `stub_auth_enabled=True`

### Prompt 2.1.1: Write Failing Auth Tests (RED)

```
You are implementing Phase 2.1 of the SkillHub FastAPI-to-Flask migration.

CONTEXT:
- Flask app uses `before_request` hook for JWT auth (Phase 1)
- `g.current_user` is set by the hook for authenticated requests
- `PUBLIC_ENDPOINTS` frozenset controls which endpoints skip auth
- OAuth routes and stub auth routes must be in PUBLIC_ENDPOINTS when registered

READ these files first:
- apps/api/skillhub/routers/auth.py (FastAPI reference — the source of truth for behavior)
- apps/api/tests/test_auth.py (FastAPI test reference — port to Flask)
- apps/api/tests/conftest.py (shared fixtures — use the Flask equivalents)
- apps/api/skillhub/app.py (Flask app factory — understand PUBLIC_ENDPOINTS)

CREATE: apps/api/tests/test_auth_flask.py (or update test_auth.py if Phase 1 already replaced it)

Write tests for ALL of the following behaviors. Use Flask test client, NOT FastAPI TestClient.

TESTS REQUIRED:

class TestGetMe:
    - test_with_valid_token_returns_200: GET /auth/me with valid JWT returns 200 + user claims
    - test_without_token_returns_401: GET /auth/me without token returns 401
    - test_returns_division_and_email: Response includes division, email, username from JWT claims

class TestOAuthRedirect:
    - test_known_provider_returns_redirect: GET /auth/oauth/microsoft returns 200 with redirect_url and state
    - test_all_providers_accepted: Parametrize over {"microsoft", "google", "okta", "github", "oidc"}
    - test_unknown_provider_returns_404: GET /auth/oauth/unknown returns 404
    - test_oauth_redirect_is_public: No auth token needed (endpoint is in PUBLIC_ENDPOINTS)

class TestOAuthCallback:
    - test_known_provider_returns_501: GET /auth/oauth/microsoft/callback returns 501
    - test_unknown_provider_returns_404: GET /auth/oauth/unknown/callback returns 404
    - test_oauth_callback_is_public: No auth token needed

class TestStubAuthToken:
    - test_valid_credentials_returns_200: POST /auth/token with {"username": "test", "password": "user"} returns 200 + JWT
    - test_wrong_password_returns_401: wrong password returns 401
    - test_wrong_username_returns_401: unknown username returns 401
    - test_token_contains_correct_claims: Decode returned JWT — verify sub, user_id, division, email, exp, iat
    - test_stub_auth_not_available_when_disabled: When stub_auth_enabled=False, POST /auth/token returns 404 (NOT 403 — blueprint not registered)

class TestStubAuthDevUsers:
    - test_list_dev_users_returns_all: GET /auth/dev-users returns list with usernames alice, bob, carol, dave, admin, test
    - test_dev_users_not_available_when_disabled: When stub_auth_enabled=False, GET /auth/dev-users returns 404 (blueprint not registered)

class TestStubAuthContainment:
    - test_stub_blueprint_not_registered_when_disabled: Create app with stub_auth_enabled=False. Assert "stub_auth" not in app.blueprints.
    - test_stub_blueprint_registered_when_enabled: Create app with stub_auth_enabled=True. Assert "stub_auth" in app.blueprints.
    - test_stub_auth_module_not_imported_in_production_factory: When stub_auth_enabled=False, verify the stub_auth module is not imported (check sys.modules or use importlib inspection)

class TestAlgorithmConfusion:
    - test_alg_none_rejected: Craft unsigned JWT with alg=none, GET /auth/me returns 401
    - test_wrong_algorithm_rejected: Sign with HS384 when HS256 expected, returns 401
    - test_correct_algorithm_accepted: Valid HS256 token returns 200

FIXTURE REQUIREMENTS:
- Two app fixtures: one with stub_auth_enabled=True, one with stub_auth_enabled=False
- Use make_token() from conftest.py for JWT generation
- Use app.test_client() for Flask test client

CRITICAL: All tests must FAIL at this point (no implementation exists yet). Verify by running:
  cd apps/api && python -m pytest tests/test_auth_flask.py -x --tb=short
Expect ImportError or 404s.
```

### Prompt 2.1.2: Implement Auth Blueprint (GREEN)

```
You are implementing the auth blueprint for the Flask migration.

READ these files:
- apps/api/skillhub/routers/auth.py (FastAPI reference)
- apps/api/tests/test_auth_flask.py (failing tests from Prompt 2.1.1)
- apps/api/skillhub/app.py (Flask app factory)

CREATE: apps/api/skillhub/blueprints/auth.py

This blueprint contains:
1. GET /auth/me — returns jsonify(g.current_user). Requires auth (NOT in PUBLIC_ENDPOINTS).
2. GET /auth/oauth/<provider> — returns {"redirect_url": ..., "state": ...}. Public.
3. GET /auth/oauth/<provider>/callback — returns 501. Public.

IMPLEMENTATION:
```python
from flask import Blueprint, g, jsonify, abort
import secrets
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

OAUTH_PROVIDERS: frozenset[str] = frozenset({"microsoft", "google", "okta", "github", "oidc"})

@auth_bp.get("/me")
def get_me():
    """Return the authenticated user's JWT claims."""
    return jsonify(g.current_user)

@auth_bp.get("/oauth/<provider>")
def oauth_redirect(provider: str):
    """Return placeholder OAuth redirect URL."""
    if provider not in OAUTH_PROVIDERS:
        abort(404, description=f"Unknown provider: {provider}")
    state = secrets.token_urlsafe(32)
    logger.info("OAuth redirect initiated for provider=%s", provider)
    return jsonify({
        "redirect_url": f"https://auth.example.com/{provider}/authorize?state={state}",
        "state": state,
    })

@auth_bp.get("/oauth/<provider>/callback")
def oauth_callback(provider: str):
    """Placeholder — not yet implemented."""
    if provider not in OAUTH_PROVIDERS:
        abort(404, description=f"Unknown provider: {provider}")
    abort(501, description="OAuth callback not yet implemented")
```

CREATE: apps/api/skillhub/blueprints/stub_auth.py

This is a SEPARATE blueprint, conditionally registered:
```python
from __future__ import annotations
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid5

import jwt
from flask import Blueprint, abort, current_app, jsonify, request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

stub_auth_bp = Blueprint("stub_auth", __name__, url_prefix="/auth")

# Deterministic UUID namespace (same as FastAPI version)
STUB_USER_NAMESPACE = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

def _uid(username: str) -> str:
    return str(uuid5(STUB_USER_NAMESPACE, username))

# Dev user registry — same data as FastAPI version
STUB_USERS: dict[str, dict[str, Any]] = {
    "alice": { ... },  # Copy exact data from FastAPI auth.py
    ...
}

class TokenRequest(BaseModel):
    username: str
    password: str

@stub_auth_bp.post("/token")
def login():
    """Issue a JWT token using stub credentials."""
    settings = current_app.config["SETTINGS"]
    # Parse and validate request body
    data = request.get_json(force=True) or {}
    body = TokenRequest.model_validate(data)

    if body.password != "user" or body.username not in STUB_USERS:
        abort(401, description="Invalid credentials")

    user_claims = STUB_USERS[body.username]
    now = datetime.now(UTC)
    payload = {
        **user_claims,
        "sub": user_claims["user_id"],
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return jsonify({"access_token": token, "token_type": "bearer"})

@stub_auth_bp.get("/dev-users")
def list_dev_users():
    """List available dev stub users."""
    return jsonify([
        {
            "username": u["username"],
            "name": u["name"],
            "division": u["division"],
            "role": u["role"],
            "is_platform_team": u["is_platform_team"],
            "is_security_team": u["is_security_team"],
        }
        for u in STUB_USERS.values()
    ])
```

MODIFY: apps/api/skillhub/app.py — update create_app():

1. Always register auth_bp
2. Conditionally register stub_auth_bp:
```python
from skillhub.blueprints.auth import auth_bp
app.register_blueprint(auth_bp)

# Conditional stub auth registration
if config.stub_auth_enabled:
    from skillhub.blueprints.stub_auth import stub_auth_bp
    app.register_blueprint(stub_auth_bp)
```

3. Update PUBLIC_ENDPOINTS:
```python
PUBLIC_ENDPOINTS: frozenset[str] = frozenset({
    "health.health_check",
    "auth.oauth_redirect",
    "auth.oauth_callback",
    # stub_auth endpoints added dynamically below
})

# In create_app(), after conditional registration:
if config.stub_auth_enabled:
    # Add stub auth endpoints to public set
    PUBLIC_ENDPOINTS = PUBLIC_ENDPOINTS | frozenset({
        "stub_auth.login",
        "stub_auth.list_dev_users",
    })
```

Store the effective PUBLIC_ENDPOINTS on the app so before_request can access it:
```python
app.config["PUBLIC_ENDPOINTS"] = PUBLIC_ENDPOINTS
```

4. Update the before_request hook to read from app.config["PUBLIC_ENDPOINTS"]

VERIFY: Run tests:
  cd apps/api && python -m pytest tests/test_auth_flask.py -v
All tests from Prompt 2.1.1 must pass.

ALSO VERIFY security gates:
  cd apps/api && python -m pytest tests/test_security_migration_gate.py -k "TestAlgorithmConfusion or TestStubAuthContainment" -v
These security gate tests must pass against the Flask app (may need to be ported to Flask test client first — see acceptance criteria).
```

### Prompt 2.1.3: Refactor and Harden (REFACTOR)

```
You are doing the REFACTOR step for auth blueprints.

READ:
- apps/api/skillhub/blueprints/auth.py
- apps/api/skillhub/blueprints/stub_auth.py
- apps/api/skillhub/app.py
- apps/api/tests/test_auth_flask.py

REFACTOR CHECKLIST:
1. Error responses use {"detail": "..."} format (not Flask HTML) — verify abort() calls produce JSON
2. Ensure stub_auth_bp uses structured logging (no print())
3. Verify STUB_USERS data matches FastAPI version exactly (diff the dicts)
4. Ensure stub_auth.py has no import-time side effects that could leak into production
5. Add __all__ exports to blueprints/__init__.py
6. Run ruff check and ruff format on all modified files
7. Run mypy --strict on blueprints/ directory
8. Verify tests still pass after refactoring

VERIFY:
  cd apps/api && python -m pytest tests/test_auth_flask.py -v
  cd apps/api && ruff check skillhub/blueprints/
  cd apps/api && ruff format --check skillhub/blueprints/
```

### Acceptance Criteria — Task 2.1

- [ ] `GET /auth/me` returns 200 with JWT claims when authenticated, 401 without token
- [ ] `GET /auth/oauth/{provider}` returns 200 with redirect_url for known providers, 404 for unknown
- [ ] `GET /auth/oauth/{provider}/callback` returns 501 for known providers, 404 for unknown
- [ ] OAuth routes are public (no auth required)
- [ ] `POST /auth/token` returns JWT when `stub_auth_enabled=True`, 404 when disabled (blueprint not registered)
- [ ] `GET /auth/dev-users` returns user list when enabled, 404 when disabled
- [ ] `stub_auth` blueprint is NOT in `app.blueprints` when `stub_auth_enabled=False`
- [ ] `stub_auth` module is NOT imported when `stub_auth_enabled=False`
- [ ] Security Gate Class 2 (AlgorithmConfusion) passes
- [ ] Security Gate Class 4 (StubAuthContainment) passes
- [ ] All error responses use `{"detail": "..."}` JSON format
- [ ] ruff + mypy clean
- [ ] Test coverage >= 80% for `blueprints/auth.py` and `blueprints/stub_auth.py`

---

## Task 2.2: Convert llm_judge.py and Submissions to Sync

**Time estimate:** 20-30 minutes
**Files to modify in `apps/api/` (the FastAPI reference app, NOT the Flask app):**
- `skillhub/services/llm_judge.py`
- `skillhub/services/submissions.py`
- `skillhub/routers/submissions.py`
- `tests/test_llm_judge.py`
- `tests/test_submission_pipeline_fixes.py`
- `tests/test_submissions_service.py`

### Important: These Changes Target the FastAPI App

All changes in this task happen in the existing `apps/api/` codebase (the FastAPI reference). This is a prerequisite for porting these services to Flask. The conversion order is critical:

1. `llm_judge.py` (root cause — `httpx.AsyncClient`)
2. `submissions.py` (depends on `llm_judge.evaluate()`)
3. `routers/submissions.py` (depends on `run_gate2_scan()`)

Worker.py is NOT converted (ARQ requires async per ADR-001).

### Prompt 2.2.1: Write Failing Sync Tests (RED)

```
You are converting async code to sync in the SkillHub FastAPI app.

READ these files:
- apps/api/skillhub/services/llm_judge.py (currently async)
- apps/api/skillhub/services/submissions.py (line ~207: run_gate2_scan is async)
- apps/api/skillhub/routers/submissions.py (line ~111: scan_submission is async)
- apps/api/tests/test_llm_judge.py (5 tests use @pytest.mark.asyncio)
- apps/api/tests/test_submission_pipeline_fixes.py (8 tests use @pytest.mark.asyncio)
- apps/api/tests/test_submissions_service.py (2 tests use @pytest.mark.asyncio)
- docs/migration/async-audit.md (conversion plan)

IMPORTANT: Do NOT touch apps/api/skillhub/worker.py — ARQ requires async.

STEP 1: Modify test files to remove async patterns.

In tests/test_llm_judge.py — TestLLMJudgeService class (5 tests):
- Remove @pytest.mark.asyncio decorators
- Change `async def test_*` to `def test_*`
- Remove `await` from `service.evaluate()` calls
- Change `AsyncMock` to `MagicMock` where used
- Change `patch("httpx.AsyncClient.post", ...)` to `patch("httpx.Client.post", ...)`

In tests/test_submission_pipeline_fixes.py (8 tests):
- Remove @pytest.mark.asyncio decorators
- Change `async def` to `def`
- Remove `await` from `run_gate2_scan()` calls

In tests/test_submissions_service.py (2 tests):
- Remove @pytest.mark.asyncio decorators
- Change `async def` to `def`
- Remove `await` from `run_gate2_scan()` calls

VERIFY tests FAIL (implementation still async):
  cd apps/api && python -m pytest tests/test_llm_judge.py tests/test_submission_pipeline_fixes.py tests/test_submissions_service.py -x --tb=short
Expect: TypeError (calling coroutine without await) or similar async/sync mismatch errors.
```

### Prompt 2.2.2: Convert Source to Sync (GREEN)

```
You are converting async source code to sync.

READ:
- apps/api/skillhub/services/llm_judge.py
- apps/api/skillhub/services/submissions.py
- apps/api/skillhub/routers/submissions.py
- docs/migration/async-audit.md (reference for exact changes)

CONVERT IN ORDER:

1. llm_judge.py — LLMJudgeService.evaluate():
   - Line 34: `async def evaluate(` -> `def evaluate(`
   - Line 55: `async with httpx.AsyncClient(timeout=30.0) as client:` -> `with httpx.Client(timeout=30.0) as client:`
   - Line 56: `response = await client.post(` -> `response = client.post(`
   - Remove any remaining `await` keywords
   - Leave evaluate_gate2_sync() unchanged (already sync)
   - Leave import of `httpx` unchanged (httpx provides both sync and async)

2. submissions.py — run_gate2_scan():
   - Line ~207: `async def run_gate2_scan(` -> `def run_gate2_scan(`
   - Find `verdict = await judge.evaluate(content)` -> `verdict = judge.evaluate(content)`
   - Remove any other `await` in the function
   - All DB operations are already sync — no changes needed there

3. routers/submissions.py — scan_submission():
   - Line ~111: `async def scan_submission(` -> `def scan_submission(`
   - Line ~128: `result = await run_gate2_scan(db, sub_uuid)` -> `result = run_gate2_scan(db, sub_uuid)`

VERIFY:
  cd apps/api && python -m pytest tests/test_llm_judge.py tests/test_submission_pipeline_fixes.py tests/test_submissions_service.py -v
All tests must pass.

ALSO run the full test suite to check for regressions:
  cd apps/api && python -m pytest --tb=short
No new failures allowed.
```

### Prompt 2.2.3: Verify and Clean Up (REFACTOR)

```
VERIFY the async conversion is complete and clean.

CHECK:
1. No remaining `async def` in llm_judge.py, submissions.py (run_gate2_scan only), routers/submissions.py (scan_submission only)
2. No remaining `await` in those same functions
3. No remaining `@pytest.mark.asyncio` in the three test files
4. No remaining `AsyncMock` in test_llm_judge.py
5. worker.py still has `async def` (intentional — do NOT change)

VERIFY:
  cd apps/api && grep -rn "async def" skillhub/services/llm_judge.py
  # Should return nothing

  cd apps/api && grep -rn "async def" skillhub/services/submissions.py
  # Should return nothing (unless there are other async functions — only run_gate2_scan was converted)

  cd apps/api && grep -rn "AsyncClient" skillhub/services/llm_judge.py
  # Should return nothing

  cd apps/api && grep -rn "@pytest.mark.asyncio" tests/test_llm_judge.py tests/test_submission_pipeline_fixes.py tests/test_submissions_service.py
  # Should return nothing

RUN:
  cd apps/api && ruff check skillhub/services/llm_judge.py skillhub/services/submissions.py skillhub/routers/submissions.py
  cd apps/api && python -m pytest -v --tb=short
```

### Acceptance Criteria — Task 2.2

- [ ] `LLMJudgeService.evaluate()` is `def` (not `async def`)
- [ ] `evaluate()` uses `httpx.Client` (not `httpx.AsyncClient`)
- [ ] `run_gate2_scan()` is `def` (not `async def`)
- [ ] `scan_submission()` is `def` (not `async def`)
- [ ] No `await` in any of the three converted functions
- [ ] `worker.py` is unchanged (still async)
- [ ] 5 tests in `test_llm_judge.py` pass without `@pytest.mark.asyncio`
- [ ] 8 tests in `test_submission_pipeline_fixes.py` pass without `@pytest.mark.asyncio`
- [ ] 2 tests in `test_submissions_service.py` pass without `@pytest.mark.asyncio`
- [ ] Full test suite passes with no regressions
- [ ] ruff clean on all modified files

---

## Task 2.3: Convert cache.py to Sync + Port to Flask

**Time estimate:** 15-25 minutes
**Files to modify:**
- `apps/api/skillhub/cache.py` (sync conversion in FastAPI app)
- `apps/api/tests/test_cache.py` (update tests)
- Flask app: port sync cache to Flask app context

### Prompt 2.3.1: Write Failing Sync Cache Tests (RED)

```
You are converting the cache module from async to sync.

READ:
- apps/api/skillhub/cache.py (currently async — uses await redis.get/setex)
- apps/api/tests/test_cache.py (currently uses AsyncMock, @pytest.mark.asyncio)

MODIFY: apps/api/tests/test_cache.py

Convert ALL tests to sync:

class TestCacheGet:
    - Remove @pytest.mark.asyncio from all 3 tests
    - Change `async def test_*` to `def test_*`
    - Remove `await` from cache_get() calls
    - Replace `AsyncMock()` with `MagicMock()`
    - Change `redis.get.assert_awaited_once_with(...)` to `redis.get.assert_called_once_with(...)`

class TestCacheSet:
    - Remove @pytest.mark.asyncio from all 2 tests
    - Change `async def test_*` to `def test_*`
    - Remove `await` from cache_set() calls
    - Replace `AsyncMock()` with `MagicMock()`
    - Change `redis.setex.assert_awaited_once_with(...)` to `redis.setex.assert_called_once_with(...)`

class TestTTLConstants:
    - No changes needed (already sync)

VERIFY tests FAIL:
  cd apps/api && python -m pytest tests/test_cache.py -x --tb=short
Expect: coroutine/async mismatch errors.
```

### Prompt 2.3.2: Convert cache.py to Sync (GREEN)

```
You are converting cache.py from async to sync.

READ:
- apps/api/skillhub/cache.py
- apps/api/tests/test_cache.py (updated in 2.3.1)

MODIFY: apps/api/skillhub/cache.py

Changes:
1. Remove `from fastapi import Request` (no longer needed for Flask version)
2. `async def get_redis(request: Request)` -> `def get_redis(request)` OR remove entirely (Flask version will get redis differently)
3. `async def cache_get(redis, key: str)` -> `def cache_get(redis, key: str)`
   - `raw = await redis.get(key)` -> `raw = redis.get(key)`
4. `async def cache_set(redis, key, value, ttl)` -> `def cache_set(redis, key, value, ttl)`
   - `await redis.setex(...)` -> `redis.setex(...)`

The function signatures and return types stay the same. Only async/await is removed.

VERIFY:
  cd apps/api && python -m pytest tests/test_cache.py -v
All tests must pass.

VERIFY no regressions:
  cd apps/api && python -m pytest --tb=short
```

### Prompt 2.3.3: Port Sync Cache to Flask App (GREEN continued)

```
You are porting the sync cache module to the Flask app.

READ:
- apps/api/skillhub/cache.py (now sync after 2.3.2)
- apps/api/skillhub/app.py (Flask app factory)

The Flask cache integration works via app extensions:

1. In create_app(), initialize Redis and store on app:
```python
import redis as redis_lib

def create_app(config=None):
    ...
    # Redis setup
    redis_url = config.redis_url if hasattr(config, 'redis_url') else None
    if redis_url:
        app.extensions["redis"] = redis_lib.from_url(redis_url)
    else:
        app.extensions["redis"] = None
    ...
```

2. Cache functions access redis via current_app:
```python
from flask import current_app

def get_redis():
    return current_app.extensions.get("redis")
```

3. cache_get and cache_set remain as-is (they accept redis as a parameter).

WRITE TESTS for Flask cache integration:
- test_cache_get_returns_none_when_redis_none
- test_cache_set_noop_when_redis_none
- test_cache_get_returns_parsed_json
- test_cache_set_calls_setex

VERIFY:
  cd apps/api && python -m pytest tests/test_cache.py -v
```

### Acceptance Criteria — Task 2.3

- [ ] `cache_get()` is `def` (not `async def`)
- [ ] `cache_set()` is `def` (not `async def`)
- [ ] `get_redis()` is `def` (not `async def`)
- [ ] No `await` anywhere in cache.py
- [ ] No `AsyncMock` in test_cache.py
- [ ] No `@pytest.mark.asyncio` in test_cache.py
- [ ] All cache tests pass
- [ ] Flask app initializes Redis in `create_app()`
- [ ] Full test suite passes with no regressions
- [ ] ruff clean on cache.py

---

## Phase 2 Completion Checklist

Run these commands to verify the phase is complete:

```bash
# All auth tests pass
cd apps/api && python -m pytest tests/test_auth_flask.py -v

# All async-converted tests pass
cd apps/api && python -m pytest tests/test_llm_judge.py tests/test_submission_pipeline_fixes.py tests/test_submissions_service.py tests/test_cache.py -v

# Security gates pass
cd apps/api && python -m pytest tests/test_security_migration_gate.py -k "TestAlgorithmConfusion or TestStubAuthContainment" -v

# No remaining async in converted files
grep -rn "async def" apps/api/skillhub/services/llm_judge.py apps/api/skillhub/cache.py
# Should return nothing

# No async test markers in converted test files
grep -rn "@pytest.mark.asyncio" apps/api/tests/test_llm_judge.py apps/api/tests/test_cache.py apps/api/tests/test_submission_pipeline_fixes.py apps/api/tests/test_submissions_service.py
# Should return nothing

# Worker still async (intentional)
grep -rn "async def" apps/api/skillhub/worker.py
# Should return 3 matches

# Lint clean
cd apps/api && ruff check skillhub/blueprints/ skillhub/services/llm_judge.py skillhub/cache.py
cd apps/api && ruff format --check skillhub/blueprints/ skillhub/services/llm_judge.py skillhub/cache.py

# Full test suite
cd apps/api && python -m pytest --tb=short
```

## Files Modified/Created Summary

| File | Action | Task |
|------|--------|------|
| `apps/api/skillhub/blueprints/__init__.py` | Create | 2.1 |
| `apps/api/skillhub/blueprints/auth.py` | Create | 2.1 |
| `apps/api/skillhub/blueprints/stub_auth.py` | Create | 2.1 |
| `apps/api/skillhub/app.py` | Modify | 2.1, 2.3 |
| `apps/api/tests/test_auth_flask.py` | Create | 2.1 |
| `apps/api/skillhub/services/llm_judge.py` | Modify | 2.2 |
| `apps/api/skillhub/services/submissions.py` | Modify | 2.2 |
| `apps/api/skillhub/routers/submissions.py` | Modify | 2.2 |
| `apps/api/tests/test_llm_judge.py` | Modify | 2.2 |
| `apps/api/tests/test_submission_pipeline_fixes.py` | Modify | 2.2 |
| `apps/api/tests/test_submissions_service.py` | Modify | 2.2 |
| `apps/api/skillhub/cache.py` | Modify | 2.3 |
| `apps/api/tests/test_cache.py` | Modify | 2.3 |

## Dependency Graph

```
Task 2.1 (auth blueprints) — independent, can start immediately
Task 2.2 (async sync) — independent, can start immediately
Task 2.3 (cache sync) — independent of 2.1, but follows same pattern as 2.2
```

All three tasks are parallelizable. However, if running sequentially, the recommended order is 2.2 -> 2.3 -> 2.1 (async conversion first simplifies later porting).
