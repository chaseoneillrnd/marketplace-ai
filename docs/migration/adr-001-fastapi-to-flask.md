# ADR-001: FastAPI to Flask Migration

**Date:** 2026-03-23
**Status:** Accepted
**Decision Makers:** Council of 6 Experts (3 rounds)

## Context

SkillHub's API is built on FastAPI. We are porting it to a 1:1 equivalent Flask application.
The FastAPI implementation will be preserved as `apps/fast-api` for reference during migration.
The Flask port will live in a fresh `apps/api` directory.

## Decisions

### 1. OpenAPI Generation: apiflask

**Decision:** Use `apiflask>=1.3` as the Flask application class.

**Rationale:** The `gen:openapi → gen:types → typecheck:web` pipeline is load-bearing.
FastAPI auto-generates OpenAPI from route annotations. Flask has no native equivalent.
apiflask restores this by providing `@app.input()` / `@app.output()` decorators and
`app.spec` for programmatic spec access.

**Alternatives rejected:**
- *spectree* — Less mature, known OpenAPI 3.1 divergences with nullable/anyOf
- *flask-openapi3* — Breaking API changes between minor versions
- *Static spec* — Drifts from implementation immediately; undetectable until runtime
- *Manual spec* — Same drift problem

**Constraints:**
- apiflask uses marshmallow internally — do NOT let marshmallow leak into service layer
- Pydantic v2 remains the validation layer for domain logic inside services

### 2. Async Strategy: Full Sync Conversion

**Decision:** Convert all async code to synchronous. No isolation wrappers.

**Rationale:** The async surface is exactly one function deep (`llm_judge.evaluate()` using
`httpx.AsyncClient`). Converting to `httpx.Client` is ~20 lines. An `asyncio.run()` wrapper
adds hidden runtime hazards in WSGI (deadlocks under load, event loop conflicts in tests).

**Conversion order:**
1. `llm_judge.py`: `httpx.AsyncClient` → `httpx.Client`
2. `submissions.py`: `run_gate2_scan()` removes `async`/`await`
3. `cache.py`: async redis → sync `redis-py`
4. `worker.py`: Leave as-is (ARQ manages own event loop)

### 3. Authentication: `before_request` with PUBLIC_ENDPOINTS Allowlist

**Decision:** Use a global `before_request` hook that authenticates every request by default.
Public endpoints must be explicitly listed in a `PUBLIC_ENDPOINTS` frozenset.

**Rationale:** Flask decorators fail open — forgetting `@require_auth` silently exposes
an endpoint. `before_request` fails closed — every new route is authenticated by default.
With 40+ protected endpoints, at least one decorator omission is statistically likely
during a mechanical port.

**Implementation:**
- `before_request` decodes JWT and stores in `g.current_user`
- `PUBLIC_ENDPOINTS` is a frozenset of `blueprint.view_function` strings
- Admin Blueprint has additional `before_request` enforcing platform_team
- `_auth_required = True` attribute on decorators serves as secondary CI audit
- CI test asserts every non-public endpoint returns 401 without token

### 4. Database Sessions: Raw `scoped_session`, NOT Flask-SQLAlchemy

**Decision:** Use SQLAlchemy's `scoped_session` with `@app.teardown_appcontext`.

**Rationale:** Flask-SQLAlchemy requires models to inherit from `db.Model`, which would
break the shared `libs/db` library used by both API and MCP server. Raw `scoped_session`
wraps the existing `SessionLocal` with zero model changes.

**Constraints:**
- Background threads must create their own `SessionLocal()`, never use scoped proxy
- Teardown must explicitly rollback on exception before `session.remove()`
- Services never call `SessionLocal()` — they receive `db: Session` as argument

### 5. Transaction Strategy: Service-Owns-Commit

**Decision:** Service functions call `db.commit()` internally. Routes do not commit.

**Rationale:** Several services use `db.flush()` mid-operation to get generated IDs
before continuing. Moving commit to the route layer would couple routes to internal
service sequencing.

**Rules:**
- Services commit at the end of successful write operations
- Read-only services never commit
- On unhandled exception, teardown closes session without commit (implicit rollback)
- Background threads must commit and close their own sessions

### 6. Test Injection: `session_factory` Parameter on `create_app()`

**Decision:** Replace FastAPI's `dependency_overrides[get_db]` with a `session_factory`
parameter on the Flask app factory.

**Rationale:** Flask has no DI override mechanism. Monkeypatching is fragile and leaks
between tests. Constructor injection is explicit, isolated per test, and requires no cleanup.

```python
def create_app(config: AppConfig | None = None) -> APIFlask:
    config = config or AppConfig()
    app.extensions["db"] = config.session_factory or build_scoped_session(...)
```

### 7. Stub Auth: Conditional Blueprint with Production Assertion

**Decision:** Stub auth is a separate Blueprint, only registered when
`settings.stub_auth_enabled is True`. A startup assertion prevents it in production.

**Rationale:** Runtime flag gating leaves stub code in the import path.
Conditional registration means the stub module is never imported in production.

### 8. Deployment: Simple Swap (Greenfield PoC)

**Decision:** Direct swap — delete FastAPI, update docker-compose to point at Flask/gunicorn.

**Rationale:** This is a greenfield PoC with no live users. Canary deployment, traffic splitting,
and rollback infrastructure are unnecessary overhead. The FastAPI reference is preserved via git
history if needed.

### 9. Pydantic v2: Keep Throughout

**Decision:** Keep all existing Pydantic v2 schemas unchanged.

**Constraints:**
- Always use `.model_dump(mode="json")` for Flask `jsonify()` (Decimal/UUID/datetime)
- `validated_body()` and `validated_query()` decorators centralize validation
- 422 for validation errors (not 400) to match FastAPI behavior
- `DivisionRestrictedError` as named exception for the dict-typed detail response

### 10. mise.toml Rename: 3-Phase Strategy

**Phase 0:** Add namespaced aliases (`dev:api:fastapi`, `test:api:fastapi`)
**Phase 1:** Add `:flask` variants alongside originals
**Phase 2:** Single atomic commit retargets bare task names to Flask
**Phase 3:** Remove `:fastapi` suffixed tasks after 30-day grace period

## Consequences

- Service layer ports unchanged (pure functions with `db: Session`)
- libs/db is framework-agnostic but has received model additions (PlatformUpdate, SkillFeedback, gate3_* columns) with corresponding migrations (004_review_queue_columns, 004_feedback_and_platform_updates). These are consumed by the Flask app automatically via the shared lib.
- ~20 lines to sync llm_judge.py eliminates all async
- 17 test files need scaffolding rewrite (dependency_overrides → session_factory)
- 7 service test files (~1,800 lines) are portable verbatim
- OpenAPI pipeline restored via apiflask
- Security enforcement is structural (before_request), not advisory (decorators)
- 6 known FastAPI contract bugs (exports params/field names, feedback joined fields, roadmap version_tag) will be fixed in the Flask port, not in FastAPI — see migration plan "Known FastAPI Contract Bugs" section
- event_type string bug in review_queue.py (`"submission.rejectd"`) will be fixed in Flask port
