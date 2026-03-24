# FastAPI → Flask Migration Plan

## Goal

Port the SkillHub API from FastAPI to a 1:1 equivalent Flask application. The FastAPI implementation remains untouched as reference at `apps/fast-api` until the port is complete, tested, and traffic is fully migrated. The Flask port lives in a fresh `apps/api` directory.

## Council of Experts Summary

A 6-expert, 3-round council analyzed the migration across architecture, database, security, API contracts, testing, and infrastructure. Key findings shaped every decision below.

### Expert Panel & Grades

| Expert | Focus | Grade | Top Risk Identified |
|--------|-------|-------|---------------------|
| Flask Migration Architect | Overall architecture, migration order | B+ | DI leakage degrading service layer |
| SQLAlchemy & Database Specialist | Session management, transaction patterns | B- | Background task session corruption |
| Authentication & Security Engineer | JWT auth, RBAC, division enforcement | C+ | Silent auth bypass via decorator omission |
| API Contract Enforcer | Request/response parity, schema validation | C+ | Query param coercion divergence |
| Testing & Quality Assurance Lead | Test strategy, migration verification | C+ | Silent type coercion breaks in JSON serialization |
| DevOps & Infrastructure Engineer | Deployment, Docker, CI/CD, tooling | C+ | Async/sync mismatch as silent correctness hazard |

**Consensus Grade: B+** — Feasible with manageable risk.

### Key Agreements (Unanimous)

| Decision | Rationale |
|----------|-----------|
| Keep Pydantic v2 throughout | Zero rewrite; `.model_dump(mode="json")` for serialization |
| Raw `scoped_session`, NOT Flask-SQLAlchemy | Preserves `libs/db` shared library; Flask-SQLAlchemy requires model rewrites |
| Service layer ports unchanged | Pure functions with `db: Session` — no framework coupling |
| `before_request` + PUBLIC_ENDPOINTS allowlist for auth | Fails closed (safe); decorators fail open |
| apiflask for OpenAPI generation | Restores `gen:openapi → gen:types → typecheck:web` pipeline |
| Sync conversion for `llm_judge.py` (httpx.Client) | One function deep; eliminates async contamination entirely |
| Simple swap deployment (greenfield PoC) | Delete FastAPI, update docker-compose to Flask, no canary needed |
| `session_factory` param on `create_app()` for test injection | Replaces `dependency_overrides`; safer (no global override dict) |
| Stub auth as conditional blueprint with production assertion | Cannot exist in production import path |
| Service-owns-commit transaction strategy | Routes don't commit; teardown closes session |

### Key Risks (Prioritized)

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| 1 | Silent auth bypass — forgetting decorator on new endpoint | CRITICAL | `before_request` allowlist + CI route audit test |
| 2 | Query param coercion divergence — Flask MultiDict vs FastAPI | HIGH | `validated_query()` decorator with normalization contract |
| 3 | Response serialization breaks — Decimal/UUID/datetime | HIGH | Centralized `json_response()` helper; contract snapshot tests |
| 4 | OpenAPI schema drift — apiflask vs FastAPI output differences | MEDIUM-HIGH | Lock baseline `openapi-baseline.json`; CI diff gate |
| 5 | Background task session corruption — scoped proxy in wrong thread | MEDIUM | Background threads use `SessionLocal()` directly |

Full decisions documented in: `docs/migration/adr-001-fastapi-to-flask.md`

## Architecture Overview

### Current State (FastAPI)

```
apps/api/skillhub/
├── main.py              # create_app() factory, CORS, OTel, router registration
├── config.py            # pydantic-settings (Settings class)
├── dependencies.py      # get_db, get_current_user, require_platform/security_team
├── cache.py             # Redis cache (async — to be converted)
├── tracing.py           # OpenTelemetry setup
├── worker.py            # ARQ background jobs
├── routers/             # 13 FastAPI APIRouters (63 paths, 79 schemas)
│   ├── health.py, auth.py, skills.py, users.py, social.py
│   ├── submissions.py, flags.py, admin.py, analytics.py
│   ├── exports.py, feedback.py, roadmap.py, review_queue.py
├── schemas/             # Pydantic v2 request/response models (reusable as-is)
│   ├── skill.py, social.py, submission.py, user.py
│   ├── admin.py, analytics.py, flags.py, feedback.py, review_queue.py
└── services/            # Pure business logic (reusable as-is)
    ├── skills.py, social.py, submissions.py, users.py
    ├── admin.py, analytics.py, exports.py, flags.py
    ├── reviews.py, llm_judge.py, feedback.py, roadmap.py, review_queue.py
```

### Target State (Flask)

```
apps/api/skillhub_flask/
├── app.py               # create_app() factory using APIFlask, scoped_session, before_request auth
├── config.py            # AppConfig wrapping pydantic-settings
├── auth.py              # before_request hook, PUBLIC_ENDPOINTS, role decorators
├── db.py                # scoped_session setup, teardown_appcontext
├── cache.py             # Sync Redis cache (redis-py)
├── tracing.py           # OTel setup (FlaskInstrumentor swap)
├── validation.py        # validated_query(), validated_body(), DivisionRestrictedError
├── worker.py            # ARQ jobs (unchanged, process-external)
├── blueprints/          # Flask Blueprints (1:1 from FastAPI routers)
│   ├── health.py, auth.py, skills.py, users.py, social.py
│   ├── submissions.py, flags.py, admin.py, analytics.py
│   ├── exports.py, feedback.py, roadmap.py, review_queue.py
│   └── stub_auth.py     # Conditional blueprint — only registered when stub_auth_enabled
├── schemas/             # Symlink or copy — Pydantic v2 models are framework-agnostic
└── services/            # Symlink or copy — pure functions with db: Session
```

### What Ports Unchanged

- **`libs/db/`** — Zero FastAPI imports. All models, session factory, Alembic migrations.
- **`libs/python-common/`** — Zero dependencies. Placeholder library.
- **`apps/api/skillhub/schemas/`** — Pure Pydantic v2. No FastAPI imports.
- **`apps/api/skillhub/services/`** — Pure functions accepting `db: Session`. No framework coupling.
- **`apps/api/skillhub/worker.py`** — ARQ is process-external. Manages own event loop.

### What Changes

| Component | FastAPI Pattern | Flask Equivalent |
|-----------|----------------|-----------------|
| App factory | `FastAPI(title=..., version=...)` | `APIFlask(__name__)` |
| Router | `APIRouter(prefix=..., tags=...)` | `Blueprint(name, __name__, url_prefix=...)` |
| DI: DB session | `Depends(get_db)` → generator | `scoped_session` + `teardown_appcontext` |
| DI: Auth | `Depends(get_current_user)` | `before_request` hook → `g.current_user` |
| DI: Settings | `request.app.state.settings` | `current_app.extensions["settings"]` |
| Request body | Auto from type hints | `validated_body()` decorator |
| Query params | Auto from type hints + `Query()` | `validated_query()` decorator |
| Response model | `response_model=Schema` | `.model_dump(mode="json")` + `jsonify()` |
| Background tasks | `BackgroundTasks.add_task()` | `threading.Thread(daemon=True)` or ARQ enqueue |
| CORS | `CORSMiddleware` | `flask-cors` |
| OTel | `FastAPIInstrumentor` | `FlaskInstrumentor` |
| OpenAPI | `app.openapi()` (auto) | `app.spec` via apiflask |
| Server | Uvicorn (ASGI) | Gunicorn (WSGI) |

## Tech Stack & Dependencies

### New Dependencies (Flask app)

```
apiflask>=1.3
flask-cors
gunicorn
redis>=5.0           # sync client (replaces async)
opentelemetry-instrumentation-flask
```

### Retained Dependencies

```
pydantic>=2.0
pydantic-settings
sqlalchemy>=2.0
alembic
psycopg2-binary
pyjwt
httpx                # now sync Client only
opentelemetry-api
opentelemetry-sdk
opentelemetry-exporter-otlp-proto-grpc
opentelemetry-instrumentation-sqlalchemy
opentelemetry-instrumentation-httpx
arq
```

### Removed Dependencies (at cutover)

```
fastapi
uvicorn[standard]
pytest-asyncio       # dev only
```

## Phase 0 — Prerequisites (COMPLETE)

All prerequisites identified by the council have been executed and verified.

| # | Prerequisite | Status | Deliverable |
|---|-------------|--------|-------------|
| 1 | Async callsite audit | DONE | `docs/migration/async-audit.md` |
| 2 | libs/db independence verification | DONE | Verified: zero FastAPI imports |
| 3 | OpenAPI baseline locked | DONE (regenerated) | `specs/openapi.json` — 63 paths, 79 schemas (regenerated 2026-03-23 after feedback/roadmap/review_queue routers registered) |
| 4 | Security test classes written | DONE (updated) | `apps/api/tests/test_security_migration_gate.py` — 8 classes, 326 tests (updated with new admin routes + Class 8 TestReviewQueueWorkflow) |
| 5 | Query normalization contract | DONE | `docs/migration/query-normalization-contract.md` |
| 6 | Migration ADR | DONE | `docs/migration/adr-001-fastapi-to-flask.md` |

### Async Audit Results

9 async functions in source, all sync-convertible. Dependency chain:
```
llm_judge.py:evaluate() → submissions.py:run_gate2_scan() → routers/submissions.py:scan_submission()
```
Convert `llm_judge.py` first (httpx.AsyncClient → httpx.Client, ~20 lines). Everything cascades.

### Security Test Baseline (8 Classes, 326 Tests)

| Class | Tests | What It Gates |
|-------|-------|---------------|
| TestUnauthenticatedRejection | 210+ | Every protected endpoint rejects: no token, expired, wrong secret, malformed, no Bearer |
| TestAlgorithmConfusion | 3 | alg:none rejected, wrong algorithm rejected, correct accepted |
| TestDivisionIsolation | 2 | Division-restricted install blocked, forged claim handled |
| TestStubAuthContainment | 4 | Stub disabled rejects login/dev-users, enabled allows, claims correct |
| TestAdminBoundary | 55+ | Regular users get 403 on all admin routes (incl. review-queue, feedback admin, roadmap admin) |
| TestAuditLogIntegrity | 7 | Audit log access control, claim writes audit entry, decide writes correct event_type |
| TestPublicRoutesAccessible | 10 | Public routes accessible without auth (incl. /changelog, /auth/dev-users) |
| TestReviewQueueWorkflow | 5 | Self-approval rejected (403), regular users blocked, invalid submission returns 404 |

### Known FastAPI Contract Bugs (Fix in Flask Port, Not FastAPI)

The council identified 6 pre-existing contract mismatches between the FastAPI API and the frontend. These are **not** being fixed in FastAPI — the FastAPI app remains as-is for reference. The Flask port will implement these correctly.

| # | Bug | FastAPI Behavior | Correct Flask Behavior |
|---|-----|-----------------|----------------------|
| 1 | Export POST params | `scope`/`format` as query params | Accept JSON body `{scope, format, start_date?, end_date?}` |
| 2 | Export response field | Returns `file_path` | Return `download_url` |
| 3 | Export status value | Returns `"queued"` | Return `"pending"` (matches frontend type union) |
| 4 | Feedback pagination | Returns `per_page` | Return `per_page` (fix frontend to match, or alias) |
| 5 | Feedback joined fields | Returns only `user_id`/`skill_id` | Include `user_display_name` and `skill_name` (JOINed) |
| 6 | Roadmap version_tag | No `version_tag` field on response | Add `version_tag` to `PlatformUpdateResponse` |

Additionally, an **event_type string bug** exists in `review_queue.py`: `f"submission.{decision}d"` produces `"submission.rejectd"` for reject. The Flask port will use an explicit lookup dict.

The OpenAPI baseline (`specs/openapi.json`) captures the FastAPI behavior as-is (including bugs). The Flask port's OpenAPI spec will intentionally diverge on these 6 points. The parity gate in Task 4.7 should verify path coverage matches, but allow schema/field differences where documented above.

### Future-Proofing: Schema Columns to Add During Migration

The post-migration roadmap (Phase 6) includes HITL revision tracking, post-approval skill versioning, and multi-mode submission. A council of 6 experts analyzed these features and identified 3 nullable columns that are **cheapest to add during the Flask migration** rather than retrofitting onto a live table afterward. These columns have zero behavioral impact during migration — they are nullable with no logic wired up.

| Column | Table | Type | Why Add Now |
|--------|-------|------|-------------|
| `parent_submission_id` | `submissions` | `UUID FK → submissions.id, NULLABLE` | Self-referential FK for revision chains. Adding post-migration requires backfill (set existing rows to NULL). Adding now: free. |
| `revision_number` | `submissions` | `Integer, NOT NULL, default 1` | Tracks how many rounds without approval. Adding post-migration requires `UPDATE submissions SET revision_number = 1`. Adding now: free. |
| `submitted_via` | `submissions` | `VARCHAR(20), NOT NULL, default 'form'` | Tracks submission method (form/upload/mcp). Needed for user submission UX. Adding now: free. |

**These should be added in the Flask migration's Alembic migration, not in a separate post-migration migration.** No service code changes required — the columns exist but are unused until Phase 6 features are built.

### Additional Bug: Decision Vocabulary Inconsistency (Bug #7)

`ReviewDecisionRequest` in `schemas/submission.py` uses `approved|changes_requested|rejected` (past tense). `DecisionRequest` in `schemas/review_queue.py` uses `approve|reject|request_changes` (imperative). The Flask port should unify on **imperative** (`approve|reject|request_changes`) as the API contract, mapping internally as needed.

### Service Layer Prep: Extract `_write_audit()` to Shared Utility

Currently `_write_audit()` is a private function in `services/submissions.py`, reimplemented inline in `services/review_queue.py`. During the Flask migration, extract to `libs/python-common` as `audit_log_append(db, event_type, actor_id, target_type, target_id, metadata)`. Zero behavioral change; prevents drift when Phase 6 adds more audit events.

---

## Phase 1 — Flask Skeleton with Auth and Health

### Task 1.0: Verify OpenAPI baseline completeness (DONE)

The OpenAPI baseline was regenerated on 2026-03-23 after feedback, roadmap, and review_queue routers were registered in main.py. All 13 routers are now captured.

- [x] Baseline regenerated: 63 paths, 79 schemas (was 55/69 before admin enhancements)
- [x] Security gate updated: 326 tests covering all routes (was 209)
- [ ] After `git mv` in Task 1.1, verify baseline still loads: `python -c "import json; d=json.load(open('specs/openapi.json')); print(f'Paths: {len(d[\"paths\"])}')"` — expect 63

```bash
# Verification
python -c "import json; d=json.load(open('specs/openapi.json')); print(f'Baseline paths: {len(d[\"paths\"])}')"  # 63
```

### Task 1.1: Rename `apps/api` → `apps/fast-api`

- [ ] `git mv apps/api apps/fast-api` to preserve history
- [ ] Update `mise.toml`: add `dev:api:fastapi` and `test:api:fastapi` aliases pointing to `apps/fast-api`
- [ ] Update `mise.toml`: add `dev:api:flask` and `test:api:flask` stubs pointing to `apps/api` (ADR-001 Phase 1 of rename strategy)
- [ ] Update `docker-compose.yml`: change build context and volume mounts to `apps/fast-api`
- [ ] Update `.gitlab-ci.yml`: paths to `apps/fast-api`
- [ ] Copy `specs/openapi.json` to `specs/openapi-baseline.json` (locked contract target — never overwritten)
- [ ] Verify: `mise run test:api:fastapi` passes (all existing tests green)

```bash
# Verification
git mv apps/api apps/fast-api
cp specs/openapi.json specs/openapi-baseline.json
mise run test:api:fastapi  # all tests pass
```

### Task 1.2: Scaffold Flask app directory

- [ ] Create `apps/api/` directory structure
- [ ] Create `apps/api/pyproject.toml` with Flask dependencies
- [ ] Create `apps/api/skillhub_flask/__init__.py`
- [ ] Create `apps/api/skillhub_flask/app.py` — `create_app()` factory using APIFlask

**File: `apps/api/pyproject.toml`**
```toml
[project]
name = "skillhub-api"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "apiflask>=1.3",
    "flask-cors",
    "gunicorn",
    "pydantic>=2.0",
    "pydantic-settings",
    "sqlalchemy>=2.0",
    "alembic",
    "psycopg2-binary",
    "pyjwt",
    "httpx",
    "redis>=5.0",
    "opentelemetry-api",
    "opentelemetry-sdk",
    "opentelemetry-exporter-otlp-proto-grpc",
    "opentelemetry-instrumentation-flask",
    "opentelemetry-instrumentation-sqlalchemy",
    "opentelemetry-instrumentation-httpx",
    "arq",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "pytest-flask",
]
```

```bash
# Verification
pip install -e apps/api[dev]
python -c "from skillhub_flask.app import create_app; app = create_app(); print('OK')"
```

### Task 1.3: Implement Flask app factory

- [ ] Create `apps/api/skillhub_flask/config.py` — AppConfig wrapping pydantic-settings
- [ ] Create `apps/api/skillhub_flask/db.py` — scoped_session + teardown
- [ ] Create `apps/api/skillhub_flask/app.py` — create_app() with APIFlask, CORS, OTel, session teardown
- [ ] Write test: app creates without error, health blueprint registered

**File: `apps/api/skillhub_flask/app.py`**
```python
from apiflask import APIFlask
from flask_cors import CORS

from .config import AppConfig
from .db import init_db, shutdown_session

def create_app(config: AppConfig | None = None) -> APIFlask:
    config = config or AppConfig()
    app = APIFlask(__name__, title=config.settings.app_name, version=config.settings.app_version)
    app.extensions["settings"] = config.settings
    app.extensions["db_session_factory"] = config.session_factory

    CORS(app, origins=config.settings.cors_origins, supports_credentials=True)
    init_db(app, config)

    @app.teardown_appcontext
    def _shutdown_session(exception=None):
        shutdown_session(exception)

    # Register blueprints
    from .blueprints.health import bp as health_bp
    app.register_blueprint(health_bp)

    return app
```

```bash
# Verification
python -m pytest apps/api/tests/test_health.py -v  # health endpoint returns 200
```

### Task 1.4: Implement `before_request` auth

- [ ] Create `apps/api/skillhub_flask/auth.py` — JWT decode, PUBLIC_ENDPOINTS, before_request hook
- [ ] Register `before_request` in app factory
- [ ] Write test: unauthenticated request to non-public endpoint returns 401
- [ ] Write test: authenticated request populates `g.current_user`

**File: `apps/api/skillhub_flask/auth.py`**

Note: PUBLIC_ENDPOINTS grows across phases. Each task that adds public routes must update this set. The final set is audited in Task 4.6.

```python
# Initial skeleton — grows as blueprints are registered
PUBLIC_ENDPOINTS: frozenset[str] = frozenset({
    "health.health_check",
    "static",
    # Phase 2 adds: auth.oauth_redirect, auth.oauth_callback
    #   + stub_auth.* (when registered)
    # Phase 3 adds: skills.browse_skills, skills.list_categories,
    #   skills.get_skill_detail, flags.list_flags,
    #   roadmap.changelog
})

def register_auth(app):
    @app.before_request
    def enforce_auth():
        if request.endpoint in PUBLIC_ENDPOINTS:
            return
        # JWT decode logic...
        g.current_user = decoded_payload
```

```bash
# Verification
python -m pytest apps/api/tests/ -k "test_unauthenticated" -v
```

### Task 1.5: Implement health blueprint

- [ ] Create `apps/api/skillhub_flask/blueprints/health.py`
- [ ] Match exact response shape from FastAPI: `{"status": "ok", "version": "..."}`
- [ ] Verify against OpenAPI baseline

```bash
# Verification
python -m pytest apps/api/tests/test_health.py -v
curl http://localhost:8001/health  # manual smoke test
```

### Task 1.6: Implement validation helpers

- [ ] Create `apps/api/skillhub_flask/validation.py` — validated_query(), validated_body(), DivisionRestrictedError
- [ ] Write tests for MultiDict normalization per query-normalization-contract.md
- [ ] Verify 422 error format matches FastAPI exactly
- [ ] Handle `list[X] | None` (optional list) fields — check UnionType args for list origin, not just `__origin__`
- [ ] Add parity test: `?divisions=a&divisions=b` with both required and optional list fields

```bash
# Verification
python -m pytest apps/api/tests/test_validation.py -v
```

### Task 1.7: Set up Flask test infrastructure

- [ ] Create `apps/api/tests/conftest.py` — FlaskTestResponse adapter, session_factory injection, make_token
- [ ] Write `FlaskTestResponse` wrapper (`.json()` method for parity with httpx)
- [ ] Verify test infrastructure works with health endpoint

```bash
# Verification
python -m pytest apps/api/tests/ -v --tb=short
```

**Phase 1 exit gate:** Health endpoint green, auth enforcement active, validation helpers tested, `gen:openapi` produces output matching baseline for `/health`.

---

## Phase 2 — Auth Endpoints + Async Sync Conversion

### Task 2.1: Port auth blueprint

- [ ] Create `apps/api/skillhub_flask/blueprints/auth.py` — /auth/me, /auth/oauth/{provider}, /auth/oauth/{provider}/callback
- [ ] Create `apps/api/skillhub_flask/blueprints/stub_auth.py` — POST /auth/token, GET /auth/dev-users (conditional blueprint)
- [ ] Port OAuth placeholder routes (GET /auth/oauth/{provider} → redirect URL, GET /auth/oauth/{provider}/callback → 501)
- [ ] Add stub_auth public routes to PUBLIC_ENDPOINTS when registered
- [ ] Add OAuth routes to PUBLIC_ENDPOINTS: `auth.oauth_redirect`, `auth.oauth_callback`
- [ ] Port `test_auth.py` tests to Flask test client
- [ ] Run security migration gate Class 2 (AlgorithmConfusion) and Class 4 (StubAuthContainment)

```bash
# Verification
python -m pytest apps/api/tests/test_auth.py apps/api/tests/test_security_migration_gate.py -k "TestAlgorithmConfusion or TestStubAuthContainment" -v
```

### Task 2.2: Convert llm_judge.py to sync

All changes in this task modify files under `apps/fast-api/` (the reference FastAPI app), not `apps/api/` (Flask under construction). `worker.py` async functions are NOT converted — ARQ requires async signatures per ADR-001 Decision 2.

- [ ] In `apps/fast-api/skillhub/services/llm_judge.py`: `httpx.AsyncClient` → `httpx.Client`
- [ ] Remove `async def evaluate()` → `def evaluate()`
- [ ] Update `apps/fast-api/skillhub/services/submissions.py`: `run_gate2_scan()` remove `async`/`await`
- [ ] Update `apps/fast-api/skillhub/routers/submissions.py`: `scan_submission()` remove `async def`
- [ ] Update `apps/fast-api/tests/test_llm_judge.py`: remove 5 `@pytest.mark.asyncio` tests
- [ ] Update `apps/fast-api/tests/test_submission_pipeline_fixes.py`: remove 8 async test markers
- [ ] Update `apps/fast-api/tests/test_submissions_service.py`: remove 2 async test markers
- [ ] Update `apps/fast-api/tests/test_worker.py`: replace `asyncio.run()` with direct calls (worker functions stay async for ARQ but tests can call sync wrappers)
- [ ] Remove `pytest-asyncio` from dev dependencies only after confirming `test_worker.py` does not require it

```bash
# Verification — all 20 previously-async tests now run as sync
PYTHONPATH="apps/fast-api:libs/db:libs/python-common" python -m pytest apps/fast-api/tests/test_llm_judge.py apps/fast-api/tests/test_submission_pipeline_fixes.py apps/fast-api/tests/test_submissions_service.py apps/fast-api/tests/test_cache.py -v
```

### Task 2.3: Convert cache.py to sync

- [ ] Replace async redis client with sync `redis-py` in cache module
- [ ] Remove `async def` from `get_redis()`, `cache_get()`, `cache_set()`
- [ ] Update `test_cache.py`: remove async markers
- [ ] Port sync cache to Flask app

```bash
# Verification
python -m pytest apps/api/tests/test_cache.py -v
```

**Phase 2 exit gate:** All auth endpoints ported, security gate Classes 1-4 green, async eliminated from source, cache sync.

---

## Phase 3 — Core Domain Blueprints

Port blueprints in dependency order. Each blueprint follows this workflow:

1. Create Flask blueprint file from FastAPI router
2. Wire to service layer (unchanged) and schemas (unchanged)
3. Port corresponding test file (swap TestClient, dependency_overrides → session_factory)
4. Run security migration gate for new endpoints
5. Verify OpenAPI spec matches baseline for ported paths

### Task 3.1: Port skills blueprint

- [ ] `blueprints/skills.py` — GET /api/v1/skills, /categories, /{slug}, /{slug}/versions/*
- [ ] Add public skill routes to PUBLIC_ENDPOINTS (browse, categories, detail)
- [ ] Port `test_skills_router.py` and `test_skills_browse_comprehensive.py`
- [ ] Verify: `validated_query()` handles page/per_page/sort/divisions/verified/featured

```bash
python -m pytest apps/api/tests/test_skills_router.py -v
```

### Task 3.2: Port users blueprint

- [ ] `blueprints/users.py` — GET /api/v1/users/me, /me/installs, /me/favorites, /me/forks, /me/submissions
- [ ] All endpoints require auth (none in PUBLIC_ENDPOINTS)
- [ ] Port `test_users_router.py`

```bash
python -m pytest apps/api/tests/test_users_router.py -v
```

### Task 3.3: Port social blueprint

- [ ] `blueprints/social.py` — install, favorite, fork, follow, reviews, comments (16 route decorators)
- [ ] Implement `DivisionRestrictedError` for install division enforcement
- [ ] Port `test_social_router.py`, `test_social_comprehensive.py`
- [ ] Run security gate Class 3 (DivisionIsolation)

```bash
python -m pytest apps/api/tests/test_social_router.py apps/api/tests/test_security_migration_gate.py::TestDivisionIsolation -v
```

### Task 3.4: Port submissions blueprint

- [ ] `blueprints/submissions.py` — create submission, get detail, admin scan/review, access requests
- [ ] Background task (Gate 2 scan) uses threading.Thread or ARQ enqueue (sync)
- [ ] Port `test_submissions_router.py`, `test_submission_pipeline_comprehensive.py`

```bash
python -m pytest apps/api/tests/test_submissions_router.py -v
```

### Task 3.5: Port flags blueprint

- [ ] `blueprints/flags.py` — GET /api/v1/flags (public), admin CRUD (platform team)
- [ ] Add flags list to PUBLIC_ENDPOINTS
- [ ] Port `test_flags.py`, `test_flags_comprehensive.py`

```bash
python -m pytest apps/api/tests/test_flags.py -v
```

### Task 3.6: Port feedback blueprint

4 endpoints:
- `POST /api/v1/feedback` — auth required, body: FeedbackCreate schema
- `GET /api/v1/admin/feedback` — platform team; query params: category, sentiment, status, page, per_page
- `POST /api/v1/feedback/{feedback_id}/upvote` — auth required
- `PATCH /api/v1/admin/feedback/{feedback_id}/status` — platform team

**Known FastAPI bugs to fix in Flask (see contract bugs table):**
- Bug #5: `list_feedback()` service returns only `user_id`/`skill_id`. Flask must JOIN to include `user_display_name` and `skill_name` in response.

- [ ] `blueprints/feedback.py` — implement all 4 routes
- [ ] Port `test_feedback_service.py`
- [ ] Implement `skill_name`/`user_display_name` JOINs in Flask service (fix FastAPI bug #5)
- [ ] Add `skill_name: str | None` and `user_display_name: str | None` to `FeedbackResponse` schema
- [ ] Verify all 4 endpoints covered in security gate (ADMIN_ROUTES + PROTECTED_ROUTES) — already done
- [ ] Add PUBLIC_ENDPOINTS entry for any public feedback endpoints (none currently)
- [ ] `AdminFeedbackView.tsx` exercises category/sentiment/status filtering — verify `validated_query()` handles enum fields

```bash
python -m pytest apps/api/tests/test_feedback_service.py -v
```

### Task 3.7: Port roadmap/changelog blueprint

6 endpoints:
- `GET /api/v1/admin/platform-updates` — platform team
- `POST /api/v1/admin/platform-updates` — platform team
- `PATCH /api/v1/admin/platform-updates/{update_id}` — platform team
- `POST /api/v1/admin/platform-updates/{update_id}/ship` — platform team
- `DELETE /api/v1/admin/platform-updates/{update_id}` — **security team only**
- `GET /api/v1/changelog` — **PUBLIC** (no auth)

**Known FastAPI bug to fix in Flask:** Bug #6 — `PlatformUpdateResponse` missing `version_tag` field.

- [ ] Confirm roadmap schemas exist in schemas/ — locate or create `schemas/roadmap.py`
- [ ] `blueprints/roadmap.py` — implement all 6 routes
- [ ] Add `version_tag: str | None` to `PlatformUpdateResponse` (fix FastAPI bug #6)
- [ ] `DELETE` uses `require_security_team`, NOT `require_platform_team`
- [ ] Add `roadmap.get_changelog` to PUBLIC_ENDPOINTS
- [ ] Port `test_roadmap_service.py`

```bash
python -m pytest apps/api/tests/test_roadmap_service.py -v
```

**Phase 3 exit gate:** All core domain blueprints ported, service tests green, security gate Classes 1-5, 7, and 8 green, ≥80% coverage on Flask app.

---

## Phase 4 — Admin, Analytics, Exports

### Task 4.1: Port admin blueprint

- [ ] `blueprints/admin.py` — feature/deprecate/remove skills, recalculate trending, audit log, user mgmt
- [ ] Admin blueprint gets its own `before_request` enforcing platform_team
- [ ] Port `test_admin.py`, `test_admin_users_submissions.py`
- [ ] Run security gate Class 5 (AdminBoundary) and Class 6 (AuditLogIntegrity)

```bash
python -m pytest apps/api/tests/test_admin.py apps/api/tests/test_security_migration_gate.py::TestAdminBoundary -v
```

### Task 4.2: Port analytics blueprint

- [ ] `blueprints/analytics.py` — summary, time-series, submission-funnel, top-skills (all platform team)
- [ ] Port `test_analytics.py`

```bash
python -m pytest apps/api/tests/test_analytics.py -v
```

### Task 4.3: Port exports blueprint

2 endpoints:
- `POST /api/v1/admin/exports` — platform team; creates export job
- `GET /api/v1/admin/exports/{job_id}` — platform team; polls status

**Known FastAPI bugs to fix in Flask (see contract bugs table):**
- Bug #1: FastAPI accepts `scope`/`format` as query params; frontend sends JSON body → Flask must accept JSON body
- Bug #2: Response returns `file_path` → Flask must return `download_url`
- Bug #3: Response returns `status: "queued"` → Flask must return `status: "pending"`

- [ ] `blueprints/exports.py` — accept JSON body `{scope, format, start_date?, end_date?}` (fix bug #1)
- [ ] Wire `start_date`/`end_date` into filters dict passed to `request_export()` service
- [ ] POST response uses `status: "pending"` not `"queued"` (fix bug #3)
- [ ] GET response uses `download_url` not `file_path` (fix bug #2)
- [ ] Port `test_exports.py`; add contract tests for JSON body and corrected field names

```bash
python -m pytest apps/api/tests/test_exports.py -v
```

### Task 4.4: Port review queue blueprint

3 endpoints:
- `GET /api/v1/admin/review-queue` — platform team; list queue with SLA info
- `POST /api/v1/admin/review-queue/{submission_id}/claim` — platform team
- `POST /api/v1/admin/review-queue/{submission_id}/decision` — platform team; body: `{decision, notes}`

**Known bug to fix in Flask:** event_type string `f"submission.{decision}d"` produces `"submission.rejectd"` → use explicit lookup dict.

- [ ] `blueprints/review_queue.py` — implement all 3 routes
- [ ] Fix event_type: use `{"approve": "submission.approved", "reject": "submission.rejected", ...}` dict
- [ ] Verify `decide_submission` PermissionError → 403 for self-approval
- [ ] Verify `claim_submission` writes AuditLog with `event_type="submission.claimed"`
- [ ] Port `test_review_queue.py`
- [ ] Run security gate Class 8 (TestReviewQueueWorkflow)

```bash
python -m pytest apps/api/tests/test_review_queue.py apps/api/tests/test_security_migration_gate.py::TestReviewQueueWorkflow -v
```

### Task 4.5: Port remaining test files

- [ ] Port `test_division_enforcement.py` (385 lines — security critical, port FIRST)
- [ ] Port `test_auth_multi_identity.py`
- [ ] Port `test_regression_fixes.py`
- [ ] Port `test_reviews_router.py`, `test_reviews_comprehensive.py`
- [ ] Port `test_fix_social_users_router.py`
- [ ] Port `test_seed_data_integrity.py` (runs against both apps)
- [ ] Port `test_dependencies.py` (tests Flask auth middleware directly)
- [ ] Verify service test files run against Flask app without FastAPI imports — these should be portable verbatim per ADR-001:
  - `test_skills_service.py`
  - `test_social_service.py`
  - `test_reviews_service.py`
  - `test_users_service.py`
  - `test_skill_schemas.py`
- [ ] Audit complete PUBLIC_ENDPOINTS set against TestPublicRoutesAccessible test class — update test if new public routes were added in Phases 3-4

```bash
python -m pytest apps/api/tests/ -v --cov=skillhub_flask --cov-fail-under=80
```

### Task 4.6: Full security migration gate

- [ ] Run ALL 326 security tests against Flask app
- [ ] All 7 classes must pass at 100%

```bash
python -m pytest apps/api/tests/test_security_migration_gate.py -v  # 326 passed, 0 failed
```

### Task 4.7: OpenAPI spec parity verification

`specs/openapi-baseline.json` is the locked FastAPI contract target (created in Task 1.1). `specs/openapi.json` is regenerated from the Flask app by `gen:openapi`.

- [ ] Run `gen:openapi:flask` to generate `specs/openapi.json` from Flask app
- [ ] Diff against baseline: `diff specs/openapi.json specs/openapi-baseline.json`
- [ ] Resolve any path, schema, or status code differences
- [ ] Run `gen:types` and verify `tsc --noEmit` passes
- [ ] Verify `api.generated.ts` contains type definitions for all 63 paths

```bash
mise run gen:openapi:flask  # generates specs/openapi.json from Flask
diff <(python -c "import json; d=json.load(open('specs/openapi.json')); print(json.dumps(sorted(d['paths'].keys()), indent=2))") \
     <(python -c "import json; d=json.load(open('specs/openapi-baseline.json')); print(json.dumps(sorted(d['paths'].keys()), indent=2))")
mise run gen:types
mise run typecheck:web
```

**Phase 4 exit gate:** All 63 paths ported (verified against regenerated baseline), all 326 security tests green, OpenAPI spec verified for TypeScript type generation, coverage ≥80%.

---

## Phase 5 — Traffic Ramp + Cutover

### Task 5.1: Delete FastAPI and Update Configs

- [ ] Delete `apps/fast-api/` directory
- [ ] Update `docker-compose.yml`: point api service at Flask app with gunicorn
- [ ] Retarget bare `mise.toml` task names to Flask (single commit)
- [ ] Remove `:fastapi` task aliases immediately (no grace period — greenfield PoC)
- [ ] Remove `fastapi`, `uvicorn`, `pytest-asyncio` from dependencies

### Task 5.2: Update Project Documentation

- [ ] Update CLAUDE.md: FastAPI → Flask/APIFlask, uvicorn → gunicorn
- [ ] Remove `specs/openapi-baseline.json` (Flask spec is now source of truth)
- [ ] Final `mise run quality-gate` run

```bash
mise run quality-gate  # full CI gate passes
```

**Phase 5 exit gate:** 100% traffic on Flask, FastAPI removed, all CI green, CLAUDE.md updated.

---

## File Structure — All Files Mapped

### New Files (Flask app)

```
apps/api/
├── pyproject.toml
├── Dockerfile
├── skillhub_flask/
│   ├── __init__.py
│   ├── app.py                    # create_app() factory
│   ├── config.py                 # AppConfig with session_factory
│   ├── auth.py                   # before_request, PUBLIC_ENDPOINTS, JWT decode
│   ├── db.py                     # scoped_session, teardown, init_db
│   ├── cache.py                  # Sync Redis (redis-py)
│   ├── tracing.py                # OTel with FlaskInstrumentor
│   ├── validation.py             # validated_query(), validated_body(), DivisionRestrictedError
│   ├── worker.py                 # ARQ jobs (copied, unchanged)
│   └── blueprints/
│       ├── __init__.py
│       ├── health.py             # GET /health
│       ├── auth.py               # GET /auth/me, GET /auth/oauth/{provider}, GET /auth/oauth/{provider}/callback
│       ├── stub_auth.py          # POST /auth/token, GET /auth/dev-users (conditional)
│       ├── skills.py             # /api/v1/skills/*
│       ├── users.py              # /api/v1/users/*
│       ├── social.py             # /api/v1/skills/{slug}/(install|favorite|fork|follow|reviews|comments)
│       ├── submissions.py        # /api/v1/submissions/*, /api/v1/admin/submissions/*
│       ├── flags.py              # /api/v1/flags, /api/v1/admin/flags/*
│       ├── admin.py              # /api/v1/admin/(skills|audit-log|users|recalculate-trending)
│       ├── analytics.py          # /api/v1/admin/analytics/*
│       ├── exports.py            # /api/v1/admin/exports/*
│       ├── feedback.py           # /api/v1/feedback, /api/v1/admin/feedback/*
│       ├── roadmap.py            # /api/v1/admin/platform-updates/*, /api/v1/changelog
│       └── review_queue.py       # /api/v1/admin/review-queue/*
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # FlaskTestResponse, session_factory, make_token
│   └── (ported test files — same names as FastAPI tests)
```

### Modified Files

```
mise.toml                          # Namespaced task aliases, Flask task variants
docker-compose.yml                 # Update api service to Flask/gunicorn
.gitlab-ci.yml                     # Flask CI jobs (conditional matrix)
specs/openapi.json                 # Baseline locked (Phase 0, already done)
```

### Infrastructure Files

No new infrastructure files needed (greenfield PoC — no canary deployment).

### Unchanged Files

```
libs/db/                           # Framework-agnostic but has received model additions:
                                   #   New: models/feedback.py (SkillFeedback, PlatformUpdate)
                                   #   Modified: models/submission.py (+gate3_reviewer_id, gate3_reviewed_at, gate3_notes)
                                   #   New migrations: 004_review_queue_columns, 004_feedback_and_platform_updates
                                   #   New: scripts/seed_data.py (admin seed data)
libs/python-common/                # Zero changes
libs/shared-types/                 # Regenerated via gen:types after Flask OpenAPI
libs/ui/                           # No API dependency
apps/web/                          # Points at nginx, framework-transparent
apps/mcp-server/                   # Independent of API framework
apps/api/skillhub/schemas/         # Pydantic v2 — reused directly
apps/api/skillhub/services/        # Pure functions — reused directly
```

---

## Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Migration ADR | `docs/migration/adr-001-fastapi-to-flask.md` | All 10 architectural decisions with rationale |
| Async Audit | `docs/migration/async-audit.md` | Complete inventory of 9 async functions, conversion plan |
| Query Normalization | `docs/migration/query-normalization-contract.md` | MultiDict→Pydantic rules, parity test matrix |
| OpenAPI Baseline | `specs/openapi-baseline.json` | 63 paths, 79 schemas — locked FastAPI contract target (created Task 1.1). Note: captures FastAPI behavior including 6 known contract bugs documented above. |
| OpenAPI Current | `specs/openapi.json` | Regenerated from Flask app by `gen:openapi:flask` — will intentionally diverge on 6 documented bug fixes. |
| Security Gate Tests | `apps/api/tests/test_security_migration_gate.py` | 8 classes, 326 tests — must stay green throughout |
| SkillHub Design | `skillhub-design.md` | Original approved design document |
| SkillHub Tech Guide | `skillhub-technical-guide.md` | Implementation guide (29 prompts) |

## Estimated Timeline

| Phase | Scope | Tasks |
|-------|-------|-------|
| Phase 0 | Prerequisites | COMPLETE |
| Phase 1 | Flask skeleton + auth + health | 8 tasks |
| Phase 2 | Auth endpoints + async sync | 3 tasks |
| Phase 3 | Core domain blueprints (7 routers) | 7 tasks |
| Phase 4 | Admin/analytics/exports | 7 tasks |
| Phase 5 | Delete FastAPI + update docs | 2 tasks |
| **Migration Total** | | **27 tasks** |
| Phase 6 | Post-migration enhancements (see appendix) | Design documented, not scoped to tasks yet |

---

## Phase 6 — Post-Migration Roadmap (Design Documentation)

> **Status:** Design analysis complete. Implementation begins AFTER Phase 5 cutover.
> **Council:** 6 experts analyzed these features across 3 rounds to ensure the migration
> plan accommodates them without over-engineering. Three nullable columns were moved to
> migration scope (see "Future-Proofing" section above).

### 6.1 — Admin HITL Queue Enhancements

#### 6.1.1 Enhanced Decision Modals

**Request Changes Modal:**
- Standard change request flag checkboxes: `missing_front_matter`, `security_concern`, `scope_too_broad`, `quality_insufficient`, `division_mismatch`, `needs_changelog`
- Free-text message box for specifics (required, min 20 chars)
- Previous round's unresolved flags pre-populated (admin must explicitly dismiss)
- Stored in `change_request_flags` JSON column on `submissions` + `submission_state_transitions` row

**Reject Modal:**
- Dropdown with common rejection reasons: `malicious_content`, `policy_violation`, `duplicate`, `low_quality`, `out_of_scope`, `other`
- When `other` selected: free-text becomes required
- Stored in `rejection_category` VARCHAR column on `submissions`

**Component Design:**
- Extract `ModalShell` from existing `AdminConfirmDialog` (shared backdrop, focus trap, aria-modal, gradient stripe)
- `RequestChangesModal` and `RejectModal` are separate components using `ModalShell`
- `AdminConfirmDialog` becomes `ModalShell` + two buttons (thin wrapper, existing tests preserved)

#### 6.1.2 Submission Card — "Requested By" + Revision Badge

- Add submitter user info (name, division, avatar) to `ReviewQueueItem` API response
- `RevisionBadge` component: shows "Round N" (not "N rejections" — language matters)
- Badge renders on both queue list cards and detail panel
- At 3+ rounds: surface soft escalation path ("Schedule a review call?")

#### 6.1.3 Revision Tracking & State Machine

**Status flow with revisions:**
```
SUBMITTED → GATE1_PASSED → GATE2_PASSED → [Gate 3 HITL]
                                              │
                    APPROVED ←── (approved)    │
                    REJECTED ←── (rejected)    │  ← terminal
                    CHANGES_REQUESTED ──┐      │
                                        ↓      │
                    REVISION_PENDING ← (author editing)
                                        ↓
                    SUBMITTED ─────────────────┘  (revision_number++)
```

**Data model approach:** Mutate existing `Submission` row on resubmit (increment `revision_number`, overwrite `content`). Store diffs in new `submission_state_transitions` table. This keeps the HITL queue simple (one row per skill-in-flight) while preserving full history.

**New table: `submission_state_transitions`** (append-only):

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `submission_id` | FK → submissions | CASCADE |
| `from_status` | VARCHAR(30) | SubmissionStatus enum |
| `to_status` | VARCHAR(30) | |
| `actor_id` | FK → users | Who triggered |
| `notes` | Text, nullable | Reviewer comment |
| `diff_snapshot` | JSON, nullable | Content diff for revisions |
| `change_flags_resolved` | JSON, nullable | Which flags author addressed |
| `created_at` | DateTime TZ | server_default |

**Gate re-run policy on revision:**
- Gate 1: Always re-run (cheap, catches slug/schema issues)
- Gate 2: Content-hash delta check. If only metadata changed (no content diff), reuse previous Gate 2 result. If content changed, re-run. Reviewer can set `gate2_disposition: waived` to skip.
- Gate 3: Always requires fresh human review

#### 6.1.4 Submission Audit Log with Diffs

- New endpoint: `GET /api/v1/submissions/{display_id}/audit-log`
- Returns structured timeline: `[{ action, actor, timestamp, state_before, state_after, notes, diff_hunks }]`
- Sources from `submission_state_transitions` (detailed) + `audit_log` (compliance)
- `AuditLogPanel` component in queue detail view
- Renders as conversation thread (GitHub PR review style), not raw event list

#### 6.1.5 Post-Approval Skill Versioning

**User flow:** Author of an approved/published skill can submit a new version. Goes through full 3-gate pipeline. On approval, creates new `SkillVersion` row and updates `Skill.current_version`.

**API:** `POST /api/v1/skills/{skill_id}/versions` (must be skill owner or platform_team)
- Request: `{ content, changelog, declared_divisions, division_justification }`
- Creates a `Submission` with `parent_submission_id` set and `target_skill_id` set
- Enters Gate 1 with inverted slug check (must match existing skill, not be unique)
- Version string must be semver-greater than `Skill.current_version`
- `changelog` field required (not optional like initial submissions)

**Authorization:** Only `skill.author_id == user_id` or `is_platform_team` can submit new versions.

**Schema note:** Existing `SkillVersion.submission_id` (nullable FK) links version to the submission that produced it. Add during post-migration Alembic migration.

#### 6.1.6 Skill Card Version Selector

- **Browse grid (SkillCard):** Display-only version badge ("v1.3 · 4 versions"). Click navigates to detail view.
- **Detail view (SkillDetailView):** `VersionSelector` dropdown in header. Selecting historical version switches content display, install command reflects that version, persistent "viewing historical version" banner.
- **Diff view:** "Compare with current" button when viewing historical version. Renders side-by-side diff.
- **Endpoint:** `GET /api/v1/skills/{slug}/versions` already exists. May need enrichment with `submission_id` link.

---

### 6.2 — User Documentation via VitePress

#### Architecture

- **Location:** `apps/docs/` in the NX monorepo (new app, alongside `apps/web` and `apps/api`)
- **Serving:** Same domain at `/docs` via nginx location block pointing at VitePress `dist/`
- **Navigation:** Plain `<a href="/docs/">` from React app nav bar (full page navigation, not React Router)
- **Return link:** VitePress nav includes "Back to SkillHub" linking to `/`
- **Build:** `nx run docs:build` produces static output. Mise task: `mise run dev:docs` / `mise run build:docs`
- **Docker:** Multi-stage — build VitePress in CI, copy `dist/` into nginx image alongside React build
- **Auth:** Inherits VPN/SSO from nginx (no separate auth layer)

#### VitePress Config

```
apps/docs/
├── .vitepress/
│   ├── config.ts       # site config, sidebar, nav, base: '/docs/'
│   └── theme/
│       └── custom.css  # color tokens matching React app
├── src/
│   ├── index.md                    # Landing page
│   ├── getting-started.md          # MCP Server install, CLI, Cline, manual
│   ├── introduction-to-skills.md   # What skills are, context window, workflows
│   ├── uses-for-skills.md          # Coding, presentations, email, analytics, mermaid
│   ├── skill-discovery.md          # Tags, divisions, categories, search
│   ├── social-features.md          # Reviews, ratings, comments, forking
│   ├── advanced-usage.md           # Skill chaining, composition
│   ├── submitting-a-skill.md       # Approval process, HITL, versioning
│   ├── feature-requests.md         # How to submit feedback
│   ├── faq.md                      # Common questions
│   └── resources.md                # Links, references
└── package.json
```

#### Branding Alignment

- Shared font (load same typeface as React app in VitePress `head` config)
- CSS custom properties matched to React app's theme tokens
- Logo/favicon consistent
- No attempt to import React components into VitePress (it's Vue-based internally)

---

### 6.3 — User Skill Submission UI/UX

#### 6.3.1 Multi-Mode Submission Page

New route: `/submit` in the React app.

**Architecture:**
```
SubmitSkillPage
  └─ ModeSelector (tabs: Form | Upload | MCP Sync)
  └─ [active mode component]
       FormBuilderMode     → guided wizard: name → description → content → preview
       FileUploadMode      → drag-and-drop .md, instant parse + validation
       MCPSyncMode         → URL input, introspect, confirm (Advanced/power-user)
  └─ FrontMatterValidator  (shared, always visible once artifact exists)
  └─ SkillPreviewPanel     (shared, renders assembled SKILL.md live)
  └─ SubmitButton + SubmissionStatusTracker
```

**Key design principle:** All three modes produce the same output artifact: `{ frontMatter: Record<string, unknown>; content: string }`. The validator and preview are mode-agnostic.

**Form Builder Mode:** Guided wizard for first-time authors. Name → description → content (with live preview) → division selection → submit. LLM Judge runs async with debounce during editing, showing tagging/category suggestions as live hints (not a gate at the end).

**File Upload Mode:** Drag-and-drop. Client-side YAML front matter parsing (`parseFrontMatter()` utility). Instant validation feedback. No wizard — fast path for experienced authors.

**MCP Sync Mode:** Under "Advanced" disclosure. User provides MCP server URL, app introspects available skills, confirmation step before import. Error handling for unreachable servers.

#### 6.3.2 Validation Pipeline

1. **Client-side front matter validation** (instant): required fields (name, description), length constraints, valid category enum
2. **Gate 1 — Server-side schema validation** (on submit): slug uniqueness, division validity, content minimum length
3. **Gate 2 — LLM Judge** (async): malicious intent detection, quality score, tagging suggestions, category recommendation, division recommendation
4. **Gate 3 — HITL Review**: Same queue as admin — claim/decide workflow

**LLM Judge as live assist (not just gate):** During form editing, Gate 2 runs in the background with debounce. Results appear as:
- Category suggestion badge ("Recommended: productivity")
- Division suggestion ("Recommended: engineering-org")
- Quality score indicator
- These are hints, not overrides — user retains control

#### 6.3.3 Admin Self-Submission Policy

Admin-submitted skills follow the identical 3-gate pipeline. The existing `decide_submission()` self-approval check (`submitted_by == reviewer_id → PermissionError`) prevents the submitter from approving their own skill. A different admin must approve.

**Visual indicator:** Admin submissions tagged in queue with a distinct badge so reviewers know they're reviewing a peer's work.

**Open design question (for future decision):** For teams with only 2-3 admins, should there be a dual-approval requirement? Or is single-other-admin approval sufficient? Decision depends on team size at deployment.

---

### 6.4 — New Component Summary

| Component | Location | Purpose |
|-----------|----------|---------|
| `ModalShell` | `components/admin/ModalShell.tsx` | Shared modal chrome (backdrop, focus trap, aria-modal) |
| `RequestChangesModal` | `components/admin/modals/RequestChangesModal.tsx` | Flag checkboxes + notes for change requests |
| `RejectModal` | `components/admin/modals/RejectModal.tsx` | Reason dropdown + details for rejections |
| `SubmissionCard` | `components/admin/queue/SubmissionCard.tsx` | Extracted from AdminQueueView list item |
| `SubmissionDetail` | `components/admin/queue/SubmissionDetail.tsx` | Extracted from AdminQueueView detail panel |
| `AuditLogPanel` | `components/admin/queue/AuditLogPanel.tsx` | Submission state transition timeline |
| `RevisionBadge` | `components/admin/queue/RevisionBadge.tsx` | "Round N" badge |
| `VersionSelector` | `components/skills/VersionSelector.tsx` | Dropdown for skill version history |
| `VersionDiffView` | `components/skills/VersionDiffView.tsx` | Side-by-side version comparison |
| `SubmitSkillPage` | `views/submit/SubmitSkillPage.tsx` | Top-level submission route |
| `ModeSelector` | `views/submit/ModeSelector.tsx` | Form/Upload/MCP tab switcher |
| `FormBuilderMode` | `views/submit/FormBuilderMode.tsx` | Guided wizard submission |
| `FileUploadMode` | `views/submit/FileUploadMode.tsx` | Drag-and-drop .md upload |
| `MCPSyncMode` | `views/submit/MCPSyncMode.tsx` | MCP server import (advanced) |
| `FrontMatterValidator` | `views/submit/FrontMatterValidator.tsx` | Shared inline validation display |
| `SkillPreviewPanel` | `views/submit/SkillPreviewPanel.tsx` | Live SKILL.md preview |
| `SubmissionStatusTracker` | `views/submit/SubmissionStatusTracker.tsx` | Post-submit pipeline progress |

### 6.5 — New API Endpoints Summary

| Method | Path | Auth | Phase 6 Feature |
|--------|------|------|-----------------|
| `POST` | `/api/v1/submissions/upload` | auth required | File upload submission |
| `POST` | `/api/v1/skills/{skill_id}/versions` | skill owner or platform_team | Post-approval versioning |
| `POST` | `/api/v1/submissions/{display_id}/resubmit` | submission owner | Revision after changes_requested |
| `GET` | `/api/v1/submissions/{display_id}/audit-log` | owner or platform_team | Submission audit timeline |
| `GET` | `/api/v1/submissions/{display_id}/diff` | platform_team | Content diff between revisions |

### 6.6 — New Database Objects Summary

| Object | Type | Phase 6 Feature |
|--------|------|-----------------|
| `submission_state_transitions` | New table | Revision audit trail with diffs |
| `rejection_category` | Column on `submissions` | Structured rejection reasons |
| `change_request_flags` | JSON column on `submissions` | Standard change request categories |
| `target_skill_id` | FK column on `submissions` | Post-approval version targeting |
| `submission_id` | FK column on `skill_versions` | Link version to submission that produced it |
| `content_hash` | VARCHAR on `submissions` | Gate 2 delta check optimization |

Note: `parent_submission_id`, `revision_number`, and `submitted_via` are added during migration (see Future-Proofing section) so they're ready when Phase 6 begins.

### 6.7 — Open Design Questions (For Future Decision)

| # | Question | Context | Options |
|---|----------|---------|---------|
| 1 | Max revision rounds before auto-reject? | Pipeline Specialist flagged indefinite cycles | Hard cap (3 rounds) vs soft escalation |
| 2 | Dual approval for admin submissions? | Depends on team size | Single-other-admin vs dual-approval |
| 3 | Should `REJECTED` be terminal or allow appeal? | Some moderation systems allow one appeal | Terminal vs one-appeal |
| 4 | VitePress content ownership and review process? | Docs Engineer flagged rot risk | Assigned owners per page vs community-maintained |
| 5 | Should MCP Sync mode introspect or just accept URL? | Frontend Architect raised this | Full introspection vs URL-only import |
| 6 | "Resubmit" as new row or mutate existing? | Council converged on mutate+diff | Confirmed: mutate + diff in transitions table |
