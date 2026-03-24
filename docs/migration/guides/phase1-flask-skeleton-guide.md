# Phase 1: Flask Skeleton with Auth and Health — Technical Implementation Guide

**Project:** SkillHub FastAPI-to-Flask Migration
**Phase:** 1 of N
**Audience:** Claude Code agents executing via subagent-driven-development
**Prerequisites:** Existing FastAPI app at `apps/api/`, shared libs at `libs/db/` and `libs/python-common/`
**Reference Documents:**
- `docs/migration/adr-001-fastapi-to-flask.md` (architectural decisions)
- `docs/migration/query-normalization-contract.md` (MultiDict handling)
- `docs/migration/async-audit.md` (async elimination plan)

---

## Prompt 0 — Verify OpenAPI Baseline (DONE)

**Status:** COMPLETE. Baseline recorded: 63 paths, 79 schemas.

This prompt was executed prior to guide creation. The OpenAPI spec from the FastAPI app has been captured for parity verification in later phases.

---

## Prompt 1 — Rename `apps/api` to `apps/fast-api`

**Goal:** Preserve the existing FastAPI application for side-by-side reference during migration. The FastAPI code stays intact and runnable under its new path.

**Time estimate:** 5-10 minutes

### Context

The existing FastAPI app lives at `apps/api/`. Per ADR-001, it will be preserved as `apps/fast-api` so the Flask port can claim the `apps/api` directory. This must be a `git mv` to preserve history.

### Files to Modify

| Action | Path |
|--------|------|
| `git mv` | `apps/api` -> `apps/fast-api` |
| Edit | `mise.toml` — update all `apps/api` references to `apps/fast-api` |
| Edit | `mise.toml` — add `:fastapi` suffixed task aliases per ADR-001 Section 10 |

### Step-by-Step Instructions

1. **Run `git mv`:**
   ```bash
   git mv apps/api apps/fast-api
   ```

2. **Update `mise.toml`** — every task referencing `apps/api` must now reference `apps/fast-api`. Specifically:
   - `tasks."dev:api"` run command: `--app-dir apps/api` -> `--app-dir apps/fast-api`
   - `tasks."dev:api"` env PYTHONPATH: replace `apps/api` segment
   - `tasks."test:api"` run: `apps/api/tests/` -> `apps/fast-api/tests/`
   - `tasks."test:api"` env PYTHONPATH: `apps/api:` -> `apps/fast-api:`
   - `tasks."test:api:coverage"` run + env: same pattern
   - `tasks."lint:api"` run: `apps/api/` -> `apps/fast-api/`

3. **Add namespaced aliases** (Phase 0 of ADR-001 Section 10):
   - `tasks."dev:api:fastapi"` = clone of `tasks."dev:api"` (pointing to fast-api)
   - `tasks."test:api:fastapi"` = clone of `tasks."test:api"` (pointing to fast-api)
   - `tasks."lint:api:fastapi"` = clone of `tasks."lint:api"` (pointing to fast-api)

4. **Verify** the existing FastAPI tests still pass:
   ```bash
   mise run test:api:fastapi
   ```

### Acceptance Criteria

- [ ] `apps/fast-api/` exists with full contents of the former `apps/api/`
- [ ] `apps/api/` does not exist
- [ ] `git log --follow apps/fast-api/skillhub/main.py` shows history
- [ ] `mise run test:api:fastapi` passes (all existing tests green)
- [ ] `mise run lint:api:fastapi` passes
- [ ] No references to `apps/api` remain in `mise.toml` (except as future Flask targets)

### DO NOT

- Do NOT delete any files — this is a rename, not a removal
- Do NOT modify any Python source files in the moved directory
- Do NOT update import paths — they use package names (`skillhub.*`), not filesystem paths
- Do NOT change `pyproject.toml` inside the moved directory
- Do NOT create `apps/api/` yet — that is Prompt 2

---

## Prompt 2 — Scaffold Flask App Directory + `pyproject.toml`

**Goal:** Create the empty Flask application directory structure and its `pyproject.toml` with all required dependencies.

**Time estimate:** 10 minutes

### Context

The new Flask app will live at `apps/api/` (the path freed by Prompt 1). It uses `skillhub_flask` as the Python package name to avoid import collisions with the FastAPI `skillhub` package.

### Target File Structure

```
apps/api/
├── pyproject.toml
├── skillhub_flask/
│   ├── __init__.py
│   ├── app.py              # (empty — Prompt 3)
│   ├── config.py            # (empty — Prompt 3)
│   ├── auth.py              # (empty — Prompt 4)
│   ├── db.py                # (empty — Prompt 3)
│   ├── tracing.py           # (empty — Prompt 3)
│   ├── validation.py        # (empty — Prompt 6)
│   └── blueprints/
│       ├── __init__.py
│       └── health.py        # (empty — Prompt 5)
├── tests/
│   ├── __init__.py
│   └── conftest.py          # (empty — Prompt 7)
```

### Step-by-Step Instructions

1. **Create the directory tree:**
   ```bash
   mkdir -p apps/api/skillhub_flask/blueprints
   mkdir -p apps/api/tests
   ```

2. **Create `apps/api/pyproject.toml`:**
   ```toml
   [project]
   name = "skillhub-flask-api"
   version = "1.0.0"
   description = "SkillHub Flask API backend"
   requires-python = ">=3.11"
   dependencies = [
     "apiflask>=1.3",
     "flask-cors",
     "sqlalchemy>=2.0",
     "pydantic>=2.0",
     "pydantic-settings",
     "pyjwt",
     "psycopg2-binary",
     "alembic",
     "httpx",
     "gunicorn",
     "opentelemetry-api",
     "opentelemetry-sdk",
     "opentelemetry-exporter-otlp-proto-grpc",
     "opentelemetry-instrumentation-flask",
     "opentelemetry-instrumentation-sqlalchemy",
   ]

   [project.optional-dependencies]
   dev = [
     "pytest",
     "pytest-cov",
     "pytest-flask",
     "mypy",
     "ruff",
   ]

   [tool.ruff]
   target-version = "py311"
   line-length = 120

   [tool.ruff.lint]
   select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]

   [tool.mypy]
   strict = true
   python_version = "3.11"
   ```

3. **Create stub files** — each file gets only a module docstring:
   - `apps/api/skillhub_flask/__init__.py`: `"""SkillHub Flask API package."""`
   - `apps/api/skillhub_flask/app.py`: `"""Flask application factory."""`
   - `apps/api/skillhub_flask/config.py`: `"""Flask application configuration."""`
   - `apps/api/skillhub_flask/auth.py`: `"""Authentication via before_request hook."""`
   - `apps/api/skillhub_flask/db.py`: `"""Database session management for Flask."""`
   - `apps/api/skillhub_flask/tracing.py`: `"""OpenTelemetry tracing setup."""`
   - `apps/api/skillhub_flask/validation.py`: `"""Request validation decorators using Pydantic v2."""`
   - `apps/api/skillhub_flask/blueprints/__init__.py`: `"""Flask blueprints package."""`
   - `apps/api/skillhub_flask/blueprints/health.py`: `"""Health check blueprint."""`
   - `apps/api/tests/__init__.py`: `"""Flask API test suite."""`
   - `apps/api/tests/conftest.py`: `"""Shared test fixtures for Flask API tests."""`

4. **Add Flask tasks to `mise.toml`** (Phase 1 of ADR-001 Section 10):
   ```toml
   [tasks."dev:api:flask"]
   description = "Start Flask API server"
   run = "gunicorn 'skillhub_flask.app:create_app()' --bind 0.0.0.0:8000 --reload"
   dir = "apps/api"
   env = { PYTHONPATH = "../../libs/db:../../libs/python-common" }

   [tasks."test:api:flask"]
   description = "Run Flask API tests"
   run = "python -m pytest apps/api/tests/ -v"
   env = { PYTHONPATH = "apps/api:libs/db:libs/python-common" }

   [tasks."test:api:flask:coverage"]
   description = "Run Flask API tests with coverage"
   run = "python -m pytest apps/api/tests/ -v --cov=apps/api/skillhub_flask --cov-fail-under=80"
   env = { PYTHONPATH = "apps/api:libs/db:libs/python-common" }

   [tasks."lint:api:flask"]
   description = "Lint Flask API"
   run = "ruff check apps/api/"
   ```

5. **Install the new package:**
   ```bash
   pip install -e apps/api[dev]
   ```

### Acceptance Criteria

- [ ] `apps/api/pyproject.toml` exists with all listed dependencies
- [ ] All stub files exist with docstrings
- [ ] `pip install -e apps/api[dev]` succeeds without errors
- [ ] `python -c "import skillhub_flask"` succeeds
- [ ] `ruff check apps/api/` passes
- [ ] `mise run test:api:flask` runs (may report "no tests collected" — that is fine)

### DO NOT

- Do NOT put implementation code in any stub file — only the module docstring
- Do NOT add Flask-SQLAlchemy as a dependency (ADR-001 Section 4)
- Do NOT add `pytest-asyncio` — Flask tests are fully synchronous
- Do NOT modify any files under `apps/fast-api/`
- Do NOT use `flask` directly as a dependency — `apiflask` depends on it transitively

---

## Prompt 3 — Implement Flask App Factory

**Goal:** Implement `create_app()`, `AppConfig`, database session lifecycle, and OTel tracing — the core skeleton that all subsequent prompts build upon.

**Time estimate:** 30-40 minutes

### Context

The app factory pattern from ADR-001 Section 6 uses an `AppConfig` dataclass wrapping `Settings` from pydantic-settings, with a `session_factory` parameter for test injection. The factory creates an `APIFlask` instance (not plain `Flask`), wires CORS, OTel, and database teardown.

### Files to Implement

| File | Purpose |
|------|---------|
| `apps/api/skillhub_flask/config.py` | `AppConfig` dataclass wrapping `Settings` |
| `apps/api/skillhub_flask/db.py` | `init_db()`, `scoped_session`, teardown |
| `apps/api/skillhub_flask/tracing.py` | `setup_tracing()`, `FlaskInstrumentor` |
| `apps/api/skillhub_flask/app.py` | `create_app()` factory |

### Test-First Instructions

**Write these tests BEFORE implementing:**

Create `apps/api/tests/test_app_factory.py`:

```python
"""Tests for the Flask app factory."""
from __future__ import annotations

from apiflask import APIFlask

from skillhub_flask.app import create_app
from skillhub_flask.config import AppConfig


class TestCreateApp:
    """Test create_app() factory function."""

    def test_returns_apiflask_instance(self) -> None:
        app = create_app()
        assert isinstance(app, APIFlask)

    def test_accepts_custom_config(self) -> None:
        config = AppConfig(app_name="TestApp", app_version="0.0.1-test")
        app = create_app(config=config)
        assert app.name == "skillhub_flask"  # Flask uses module name

    def test_cors_headers_present(self) -> None:
        app = create_app()
        with app.test_client() as client:
            resp = client.options("/health", headers={"Origin": "http://localhost:5173"})
            assert "access-control-allow-origin" in {k.lower() for k in resp.headers.keys()}

    def test_config_stored_on_app(self) -> None:
        config = AppConfig(app_name="TestApp")
        app = create_app(config=config)
        assert app.extensions["config"] is config

    def test_db_session_in_extensions(self) -> None:
        config = AppConfig()
        app = create_app(config=config)
        assert "db" in app.extensions

    def test_custom_session_factory_used(self) -> None:
        """Verify session_factory injection works for tests."""
        from unittest.mock import MagicMock
        mock_factory = MagicMock()
        config = AppConfig(session_factory=mock_factory)
        app = create_app(config=config)
        assert app.extensions["db"] is mock_factory
```

Run tests — they must all FAIL (RED phase):
```bash
mise run test:api:flask
```

### Implementation Specifications

#### `apps/api/skillhub_flask/config.py`

```python
"""Flask application configuration."""
from __future__ import annotations

import dataclasses
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SkillHub configuration — all values overridable via env vars."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "SkillHub"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://skillhub:skillhub@localhost:5433/skillhub"

    # Auth
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Stub auth
    stub_auth_enabled: bool = False

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]

    # LLM Judge
    llm_router_url: str = ""
    llm_judge_enabled: bool = False

    # Tracing
    otel_traces_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "skillhub-api"


@dataclasses.dataclass
class AppConfig:
    """Application configuration wrapper for the Flask app factory.

    Wraps Settings and adds the session_factory parameter for test injection.
    """

    app_name: str = "SkillHub"
    app_version: str = "1.0.0"
    debug: bool = False
    settings: Settings = dataclasses.field(default_factory=Settings)
    session_factory: Any = None  # Callable[[], Session] | None — for test injection
```

**Key points:**
- `Settings` is an exact copy of the FastAPI version at `apps/fast-api/skillhub/config.py` — retain field-for-field parity
- `AppConfig` is a plain dataclass (not pydantic) wrapping `Settings` plus `session_factory`
- `session_factory` defaults to `None` meaning "use real scoped_session"

#### `apps/api/skillhub_flask/db.py`

```python
"""Database session management for Flask."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import scoped_session

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)


def init_db(app: Flask, session_factory: Any | None = None) -> scoped_session:
    """Initialize database session management on the Flask app.

    If session_factory is provided (test injection), use it directly.
    Otherwise, import SessionLocal from libs/db and wrap in scoped_session.

    Registers teardown_appcontext to remove sessions after each request.
    """
    if session_factory is not None:
        db_session = session_factory
    else:
        from skillhub_db.session import SessionLocal
        db_session = scoped_session(SessionLocal)

    app.extensions["db"] = db_session

    @app.teardown_appcontext
    def shutdown_session(exception: BaseException | None = None) -> None:
        if exception is not None:
            try:
                db_session.rollback()
            except Exception:
                logger.warning("Failed to rollback session during teardown", exc_info=True)
        db_session.remove()

    return db_session
```

**Key points:**
- Uses `scoped_session(SessionLocal)` NOT Flask-SQLAlchemy (ADR-001 Section 4)
- Rollback on exception THEN remove (ADR-001 constraint)
- `session_factory` parameter enables test injection (ADR-001 Section 6)

#### `apps/api/skillhub_flask/tracing.py`

Port from `apps/fast-api/skillhub/tracing.py` with these changes:
- Replace `FastAPIInstrumentor` with `FlaskInstrumentor`
- Accept `Flask` app instance for `FlaskInstrumentor.instrument_app(app)`
- Keep `setup_tracing(settings)` for TracerProvider configuration
- Add `instrument_app(app, settings)` that calls `FlaskInstrumentor`
- Keep graceful degradation pattern (try/except, log warnings)

#### `apps/api/skillhub_flask/app.py`

```python
"""Flask application factory."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from apiflask import APIFlask
from flask_cors import CORS

from skillhub_flask.config import AppConfig
from skillhub_flask.db import init_db
from skillhub_flask.tracing import instrument_app, setup_tracing

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def create_app(config: AppConfig | None = None) -> APIFlask:
    """Create and configure the APIFlask application."""
    config = config or AppConfig()

    app = APIFlask(
        __name__,
        title=config.app_name,
        version=config.app_version,
    )
    app.debug = config.debug

    # Store config on app
    app.extensions["config"] = config

    # CORS
    CORS(
        app,
        origins=config.settings.cors_origins,
        supports_credentials=True,
    )

    # Database
    init_db(app, session_factory=config.session_factory)

    # Tracing
    setup_tracing(config.settings)
    instrument_app(app, config.settings)

    # Register blueprints
    from skillhub_flask.blueprints.health import bp as health_bp
    app.register_blueprint(health_bp)

    return app
```

### Acceptance Criteria

- [ ] All tests in `test_app_factory.py` pass (GREEN)
- [ ] `create_app()` returns an `APIFlask` instance
- [ ] `app.extensions["config"]` returns the `AppConfig`
- [ ] `app.extensions["db"]` returns the session (or mock)
- [ ] CORS headers present on responses to allowed origins
- [ ] Tracing setup logs info (not errors) when `otel_traces_enabled=False`
- [ ] `ruff check apps/api/` passes
- [ ] `mypy apps/api/skillhub_flask/ --strict` has no errors (type:ignore with comment only if unavoidable)

### DO NOT

- Do NOT import `Flask` — use `APIFlask` from `apiflask` everywhere
- Do NOT use `Flask-SQLAlchemy` or `db.Model`
- Do NOT register auth hooks yet — that is Prompt 4
- Do NOT register any blueprints other than health
- Do NOT call `app.run()` inside the factory
- Do NOT use `print()` — use `logging.getLogger(__name__)`

---

## Prompt 4 — Implement `before_request` Auth

**Goal:** Implement fail-closed authentication: every request is authenticated by default unless its endpoint is in `PUBLIC_ENDPOINTS`.

**Time estimate:** 30-40 minutes

### Context

Per ADR-001 Section 3, Flask decorators fail open (forgetting `@require_auth` silently exposes an endpoint). The `before_request` hook fails closed. Every new route is authenticated by default.

The existing FastAPI auth logic lives at `apps/fast-api/skillhub/dependencies.py` lines 34-69 (`get_current_user`). Port the JWT decode logic but restructure it as a `before_request` hook.

### Files to Implement

| File | Purpose |
|------|---------|
| `apps/api/skillhub_flask/auth.py` | `register_auth()`, `PUBLIC_ENDPOINTS`, JWT decode |
| `apps/api/tests/test_auth.py` | Auth hook tests |

### Test-First Instructions

**Write these tests BEFORE implementing:**

Create `apps/api/tests/test_auth.py`:

```python
"""Tests for before_request authentication hook."""
from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import jwt
import pytest
from flask import Flask, g

from skillhub_flask.app import create_app
from skillhub_flask.config import AppConfig, Settings

TEST_JWT_SECRET = "test-secret-for-unit-tests"
TEST_JWT_ALGORITHM = "HS256"


def _make_config(**overrides: Any) -> AppConfig:
    settings = Settings(
        jwt_secret=TEST_JWT_SECRET,
        jwt_algorithm=TEST_JWT_ALGORITHM,
        stub_auth_enabled=False,
        **{k: v for k, v in overrides.items() if k in Settings.model_fields},
    )
    return AppConfig(
        settings=settings,
        session_factory=MagicMock(),
        **{k: v for k, v in overrides.items() if k not in Settings.model_fields},
    )


def _make_token(
    payload: dict[str, Any] | None = None,
    secret: str = TEST_JWT_SECRET,
    algorithm: str = TEST_JWT_ALGORITHM,
    expired: bool = False,
) -> str:
    data: dict[str, Any] = payload or {
        "sub": "test-user",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "division": "engineering",
    }
    if expired:
        data["exp"] = int(time.time()) - 3600
    elif "exp" not in data:
        data["exp"] = int(time.time()) + 3600
    return jwt.encode(data, secret, algorithm=algorithm)


class TestPublicEndpoints:
    """Public endpoints should not require authentication."""

    def test_health_no_auth_required(self) -> None:
        app = create_app(config=_make_config())
        with app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_openapi_spec_no_auth_required(self) -> None:
        app = create_app(config=_make_config())
        with app.test_client() as client:
            resp = client.get("/openapi.json")
            assert resp.status_code == 200


class TestAuthenticatedEndpoints:
    """Non-public endpoints must require valid JWT."""

    def test_missing_auth_header_returns_401(self) -> None:
        app = create_app(config=_make_config())
        # Register a test-only protected route
        @app.route("/test-protected")
        def protected():
            return {"ok": True}

        with app.test_client() as client:
            resp = client.get("/test-protected")
            assert resp.status_code == 401

    def test_invalid_token_returns_401(self) -> None:
        app = create_app(config=_make_config())

        @app.route("/test-protected")
        def protected():
            return {"ok": True}

        with app.test_client() as client:
            resp = client.get(
                "/test-protected",
                headers={"Authorization": "Bearer invalid-garbage"},
            )
            assert resp.status_code == 401

    def test_expired_token_returns_401(self) -> None:
        app = create_app(config=_make_config())

        @app.route("/test-protected")
        def protected():
            return {"ok": True}

        with app.test_client() as client:
            token = _make_token(expired=True)
            resp = client.get(
                "/test-protected",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 401

    def test_valid_token_sets_g_current_user(self) -> None:
        app = create_app(config=_make_config())
        captured: dict[str, Any] = {}

        @app.route("/test-protected")
        def protected():
            captured["user"] = g.current_user
            return {"ok": True}

        with app.test_client() as client:
            token = _make_token({"sub": "alice", "user_id": "abc-123", "exp": int(time.time()) + 3600})
            resp = client.get(
                "/test-protected",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            assert captured["user"]["sub"] == "alice"
            assert captured["user"]["user_id"] == "abc-123"

    def test_bearer_prefix_required(self) -> None:
        app = create_app(config=_make_config())

        @app.route("/test-protected")
        def protected():
            return {"ok": True}

        with app.test_client() as client:
            token = _make_token()
            resp = client.get(
                "/test-protected",
                headers={"Authorization": f"Token {token}"},
            )
            assert resp.status_code == 401

    def test_wrong_secret_returns_401(self) -> None:
        app = create_app(config=_make_config())

        @app.route("/test-protected")
        def protected():
            return {"ok": True}

        with app.test_client() as client:
            token = _make_token(secret="wrong-secret")
            resp = client.get(
                "/test-protected",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 401
```

Run tests — they must all FAIL (RED phase).

### Implementation Specifications

#### `apps/api/skillhub_flask/auth.py`

```python
"""Authentication via before_request hook."""
from __future__ import annotations

import logging
from typing import Any

import jwt
from flask import Flask, g, jsonify, request

logger = logging.getLogger(__name__)

# Endpoints that do NOT require authentication.
# Format: "blueprint.view_function" or "view_function" for app-level routes.
# This is a frozenset — new public endpoints MUST be added here explicitly.
PUBLIC_ENDPOINTS: frozenset[str] = frozenset({
    "health.health_check",
    "openapi.spec",            # apiflask's built-in OpenAPI spec endpoint
    "static",                  # Flask static file serving
})


def register_auth(app: Flask) -> None:
    """Register the before_request authentication hook on the app.

    Fails closed: every endpoint requires authentication unless it is
    listed in PUBLIC_ENDPOINTS.
    """

    @app.before_request
    def authenticate_request() -> Any:
        # Allow public endpoints
        if request.endpoint in PUBLIC_ENDPOINTS:
            return None

        # OPTIONS requests for CORS preflight
        if request.method == "OPTIONS":
            return None

        config = app.extensions.get("config")
        if config is None:
            logger.error("AppConfig not found in app.extensions")
            return jsonify({"detail": "Server configuration error"}), 500

        settings = config.settings

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"detail": "Missing or invalid token"}), 401

        token = auth_header.removeprefix("Bearer ")
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"detail": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"detail": "Invalid token"}), 401

        g.current_user = payload
        return None
```

**Key points:**
- `PUBLIC_ENDPOINTS` is a frozenset checked by endpoint name (not URL path)
- `before_request` returns `None` to allow the request, or a tuple `(response, status)` to short-circuit
- JWT payload stored on `g.current_user` (replaces FastAPI's `Depends(get_current_user)`)
- OPTIONS always allowed (CORS preflight)

Then wire it in `app.py`:
```python
from skillhub_flask.auth import register_auth
# ... inside create_app(), after CORS setup:
register_auth(app)
```

### Acceptance Criteria

- [ ] All tests in `test_auth.py` pass
- [ ] `/health` returns 200 without any auth header
- [ ] Any unknown endpoint returns 401 without auth header
- [ ] Valid JWT sets `g.current_user` with full payload
- [ ] Expired token returns 401 with `{"detail": "Token expired"}`
- [ ] Invalid token returns 401 with `{"detail": "Invalid token"}`
- [ ] Missing `Bearer ` prefix returns 401
- [ ] `ruff check apps/api/` passes
- [ ] `mypy apps/api/skillhub_flask/ --strict` passes

### DO NOT

- Do NOT use decorator-based auth (`@login_required`) — use `before_request` only
- Do NOT add routes for login/token generation in this prompt — that is a later phase
- Do NOT store the raw token on `g` — store only the decoded payload
- Do NOT catch generic `Exception` in JWT decode — catch only `jwt.ExpiredSignatureError` and `jwt.InvalidTokenError`
- Do NOT hardcode the JWT secret — always read from `settings.jwt_secret`
- Do NOT log the token value or payload contents at INFO level (security)

---

## Prompt 5 — Implement Health Blueprint

**Goal:** Implement `GET /health` returning `{"status": "ok", "version": "..."}` — the first working endpoint.

**Time estimate:** 10-15 minutes

### Context

The existing FastAPI health endpoint is at `apps/fast-api/skillhub/routers/health.py`. The Flask version uses a Blueprint registered by the app factory.

### Files to Implement

| File | Purpose |
|------|---------|
| `apps/api/skillhub_flask/blueprints/health.py` | Health check blueprint |
| `apps/api/tests/test_health.py` | Health endpoint tests |

### Test-First Instructions

**Write these tests BEFORE implementing:**

Create `apps/api/tests/test_health.py`:

```python
"""Tests for the health check endpoint."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from skillhub_flask.app import create_app
from skillhub_flask.config import AppConfig, Settings


def _make_config(**overrides: Any) -> AppConfig:
    settings = Settings(
        jwt_secret="test-secret",
        **{k: v for k, v in overrides.items() if k in Settings.model_fields},
    )
    return AppConfig(
        settings=settings,
        session_factory=MagicMock(),
        **{k: v for k, v in overrides.items() if k not in Settings.model_fields},
    )


class TestHealthEndpoint:
    """GET /health returns status and version."""

    def test_returns_200(self) -> None:
        app = create_app(config=_make_config())
        with app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_returns_status_ok(self) -> None:
        app = create_app(config=_make_config())
        with app.test_client() as client:
            resp = client.get("/health")
            data = resp.get_json()
            assert data["status"] == "ok"

    def test_returns_version_from_config(self) -> None:
        app = create_app(config=_make_config(app_version="2.3.4"))
        with app.test_client() as client:
            resp = client.get("/health")
            data = resp.get_json()
            assert data["version"] == "2.3.4"

    def test_no_auth_required(self) -> None:
        """Health check is public — no Authorization header needed."""
        app = create_app(config=_make_config())
        with app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_response_content_type_json(self) -> None:
        app = create_app(config=_make_config())
        with app.test_client() as client:
            resp = client.get("/health")
            assert resp.content_type.startswith("application/json")
```

### Implementation Specifications

#### `apps/api/skillhub_flask/blueprints/health.py`

```python
"""Health check blueprint."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify

bp = Blueprint("health", __name__)


@bp.route("/health")
def health_check() -> tuple:
    """Return application health status and version."""
    config = current_app.extensions["config"]
    return jsonify({"status": "ok", "version": config.app_version})
```

**Key points:**
- Blueprint name is `"health"` — this must match the `PUBLIC_ENDPOINTS` entry `"health.health_check"`
- Read version from `current_app.extensions["config"]` (not `app.config`)
- Return `jsonify()` result (not a raw dict — Flask auto-converts dicts but `jsonify` is explicit)

### Acceptance Criteria

- [ ] All tests in `test_health.py` pass
- [ ] `GET /health` returns `{"status": "ok", "version": "1.0.0"}` (or configured version)
- [ ] No auth header required
- [ ] Response Content-Type is `application/json`
- [ ] `ruff check apps/api/` passes
- [ ] `mypy apps/api/skillhub_flask/ --strict` passes

### DO NOT

- Do NOT add database connectivity checks to health — keep it simple for Phase 1
- Do NOT add `/readyz` or `/livez` — just `/health`
- Do NOT return HTML or plaintext — always JSON
- Do NOT import `app` directly — use `current_app` proxy

---

## Prompt 6 — Implement Validation Helpers

**Goal:** Implement `validated_query()`, `validated_body()`, and `DivisionRestrictedError` — the validation decorators that replace FastAPI's automatic Pydantic integration.

**Time estimate:** 30-40 minutes

### Context

The full specification for query normalization is in `docs/migration/query-normalization-contract.md`. This prompt implements the decorators described there plus the body validator and the division enforcement exception.

### Files to Implement

| File | Purpose |
|------|---------|
| `apps/api/skillhub_flask/validation.py` | `validated_query()`, `validated_body()`, `DivisionRestrictedError` |
| `apps/api/tests/test_validation.py` | Validation decorator tests |

### Test-First Instructions

**Write these tests BEFORE implementing:**

Create `apps/api/tests/test_validation.py`:

```python
"""Tests for request validation decorators."""
from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import jwt
import pytest
from flask import Flask, g
from pydantic import BaseModel, Field

from skillhub_flask.app import create_app
from skillhub_flask.config import AppConfig, Settings
from skillhub_flask.validation import (
    DivisionRestrictedError,
    validated_body,
    validated_query,
)

TEST_JWT_SECRET = "test-secret"


def _make_app() -> Flask:
    settings = Settings(jwt_secret=TEST_JWT_SECRET)
    config = AppConfig(settings=settings, session_factory=MagicMock())
    return create_app(config=config)


def _make_token() -> str:
    return jwt.encode(
        {"sub": "test", "user_id": "u1", "exp": int(time.time()) + 3600},
        TEST_JWT_SECRET,
        algorithm="HS256",
    )


class SampleQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    q: str | None = None


class SampleBody(BaseModel):
    name: str
    value: int


class TestValidatedQuery:
    def test_valid_query_params(self) -> None:
        app = _make_app()

        @app.route("/test-query")
        @validated_query(SampleQuery)
        def handler(query: SampleQuery) -> dict:
            return {"page": query.page, "q": query.q}

        with app.test_client() as client:
            resp = client.get("/test-query?page=2&q=hello",
                              headers={"Authorization": f"Bearer {_make_token()}"})
            assert resp.status_code == 200
            assert resp.get_json()["page"] == 2

    def test_default_values_applied(self) -> None:
        app = _make_app()

        @app.route("/test-query")
        @validated_query(SampleQuery)
        def handler(query: SampleQuery) -> dict:
            return {"page": query.page, "per_page": query.per_page}

        with app.test_client() as client:
            resp = client.get("/test-query",
                              headers={"Authorization": f"Bearer {_make_token()}"})
            data = resp.get_json()
            assert data["page"] == 1
            assert data["per_page"] == 20

    def test_invalid_query_returns_422(self) -> None:
        app = _make_app()

        @app.route("/test-query")
        @validated_query(SampleQuery)
        def handler(query: SampleQuery) -> dict:
            return {"page": query.page}

        with app.test_client() as client:
            resp = client.get("/test-query?page=0",
                              headers={"Authorization": f"Bearer {_make_token()}"})
            assert resp.status_code == 422
            data = resp.get_json()
            assert "detail" in data

    def test_string_to_int_coercion(self) -> None:
        app = _make_app()

        @app.route("/test-query")
        @validated_query(SampleQuery)
        def handler(query: SampleQuery) -> dict:
            return {"page": query.page}

        with app.test_client() as client:
            resp = client.get("/test-query?page=5",
                              headers={"Authorization": f"Bearer {_make_token()}"})
            assert resp.status_code == 200
            assert resp.get_json()["page"] == 5


class TestValidatedBody:
    def test_valid_body(self) -> None:
        app = _make_app()

        @app.route("/test-body", methods=["POST"])
        @validated_body(SampleBody)
        def handler(body: SampleBody) -> dict:
            return {"name": body.name, "value": body.value}

        with app.test_client() as client:
            resp = client.post("/test-body",
                               json={"name": "test", "value": 42},
                               headers={"Authorization": f"Bearer {_make_token()}"})
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["name"] == "test"
            assert data["value"] == 42

    def test_missing_required_field_returns_422(self) -> None:
        app = _make_app()

        @app.route("/test-body", methods=["POST"])
        @validated_body(SampleBody)
        def handler(body: SampleBody) -> dict:
            return {"name": body.name}

        with app.test_client() as client:
            resp = client.post("/test-body",
                               json={"name": "test"},
                               headers={"Authorization": f"Bearer {_make_token()}"})
            assert resp.status_code == 422

    def test_no_json_body_returns_422(self) -> None:
        app = _make_app()

        @app.route("/test-body", methods=["POST"])
        @validated_body(SampleBody)
        def handler(body: SampleBody) -> dict:
            return {"name": body.name}

        with app.test_client() as client:
            resp = client.post("/test-body",
                               headers={"Authorization": f"Bearer {_make_token()}"})
            assert resp.status_code == 422


class TestDivisionRestrictedError:
    def test_is_exception(self) -> None:
        err = DivisionRestrictedError(
            user_division="engineering",
            required_divisions=["product"],
        )
        assert isinstance(err, Exception)

    def test_has_detail_dict(self) -> None:
        err = DivisionRestrictedError(
            user_division="engineering",
            required_divisions=["product", "design"],
        )
        detail = err.detail
        assert detail["user_division"] == "engineering"
        assert detail["required_divisions"] == ["product", "design"]

    def test_registered_error_handler_returns_403(self) -> None:
        app = _make_app()

        @app.route("/test-division")
        def handler():
            raise DivisionRestrictedError(
                user_division="eng",
                required_divisions=["product"],
            )

        with app.test_client() as client:
            resp = client.get("/test-division",
                              headers={"Authorization": f"Bearer {_make_token()}"})
            assert resp.status_code == 403
            data = resp.get_json()
            assert "detail" in data
```

### Implementation Specifications

#### `apps/api/skillhub_flask/validation.py`

Implement based on the contracts in `docs/migration/query-normalization-contract.md`:

1. **`validated_query(model_cls)`** — decorator that:
   - Reads `request.args.to_dict(flat=False)`
   - Unwraps single-element lists for non-list fields (checks `field.annotation.__origin__`)
   - Validates with `model_cls.model_validate(normalized)`
   - On `ValidationError`: returns `jsonify({"detail": exc.errors(include_url=False)}), 422`
   - On success: calls `fn(*args, query=params, **kwargs)`

2. **`validated_body(model_cls)`** — decorator that:
   - Reads `request.get_json(force=True)` (force=True handles missing Content-Type)
   - If body is None, validates against empty dict `{}`
   - Validates with `model_cls.model_validate(body_data)`
   - On `ValidationError`: returns `jsonify({"detail": exc.errors(include_url=False)}), 422`
   - On success: calls `fn(*args, body=body, **kwargs)`

3. **`DivisionRestrictedError`** — exception class:
   - Constructor takes `user_division: str`, `required_divisions: list[str]`
   - Property `detail` returns `{"user_division": ..., "required_divisions": ...}`
   - Must register error handler on the app (in `create_app` or via `init_app` pattern)

4. **`register_error_handlers(app)`** — function called from `create_app()`:
   - Registers handler for `DivisionRestrictedError` returning 403
   - Registers handler for generic `ValidationError` returning 422 (catch-all)

### Acceptance Criteria

- [ ] All tests in `test_validation.py` pass
- [ ] `validated_query` correctly coerces string query params to typed values
- [ ] `validated_query` returns 422 with `{"detail": [...]}` on validation failure
- [ ] `validated_body` validates JSON body and returns 422 on failure
- [ ] `DivisionRestrictedError` returns 403 with structured detail
- [ ] Error response format matches FastAPI's `{"detail": [{"type": ..., "loc": ..., "msg": ...}]}`
- [ ] `ruff check apps/api/` passes
- [ ] `mypy apps/api/skillhub_flask/ --strict` passes

### DO NOT

- Do NOT use marshmallow schemas — Pydantic v2 only (ADR-001 Section 1 constraint)
- Do NOT use apiflask's `@app.input()` / `@app.output()` for Pydantic models — those expect marshmallow
- Do NOT return 400 for validation errors — always 422 to match FastAPI
- Do NOT use `request.args.get()` for individual params — always `to_dict(flat=False)` per the contract
- Do NOT set `ConfigDict(strict=True)` on query param models (contract Rule 1)
- Do NOT silence ValidationError — always return the full error list

---

## Prompt 7 — Set Up Flask Test Infrastructure

**Goal:** Create the shared test fixtures (`conftest.py`) that all future test files will use: `FlaskTestResponse` adapter, `session_factory` injection, `make_token` helper.

**Time estimate:** 20-30 minutes

### Context

The existing FastAPI test infrastructure is at `apps/fast-api/tests/conftest.py`. The Flask version replaces `TestClient(app)` with Flask's `app.test_client()` and uses `session_factory` injection instead of `dependency_overrides`.

### Files to Implement

| File | Purpose |
|------|---------|
| `apps/api/tests/conftest.py` | Shared fixtures: `app`, `client`, `db_session`, `make_token`, `auth_headers` |

### Test-First Instructions

**Write these tests BEFORE implementing:**

Create `apps/api/tests/test_conftest.py` (tests that verify the fixtures themselves):

```python
"""Tests verifying conftest fixtures work correctly."""
from __future__ import annotations

from flask.testing import FlaskClient

from skillhub_flask.app import create_app
from skillhub_flask.config import AppConfig


class TestFixtures:
    """Verify that conftest fixtures produce correct types."""

    def test_app_fixture_returns_flask_app(self, app):
        from apiflask import APIFlask
        assert isinstance(app, APIFlask)

    def test_client_fixture_returns_flask_client(self, client):
        assert isinstance(client, FlaskClient)

    def test_client_can_hit_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_make_token_produces_valid_jwt(self, app, client):
        from tests.conftest import make_token
        token = make_token()
        resp = client.get("/health", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_auth_headers_fixture(self, auth_headers):
        assert "Authorization" in auth_headers
        assert auth_headers["Authorization"].startswith("Bearer ")

    def test_db_session_fixture_is_mock(self, db_session):
        """In test mode, db_session should be the mock session."""
        assert db_session is not None
```

### Implementation Specifications

#### `apps/api/tests/conftest.py`

```python
"""Shared test fixtures for Flask API tests."""
from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import jwt
import pytest
from flask import Flask
from flask.testing import FlaskClient

from skillhub_flask.app import create_app
from skillhub_flask.config import AppConfig, Settings

TEST_JWT_SECRET = "test-secret-for-unit-tests"
TEST_JWT_ALGORITHM = "HS256"


def make_token(
    payload: dict[str, Any] | None = None,
    secret: str = TEST_JWT_SECRET,
    algorithm: str = TEST_JWT_ALGORITHM,
    expired: bool = False,
) -> str:
    """Generate a JWT for testing purposes."""
    data: dict[str, Any] = payload or {
        "sub": "test-user",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "division": "engineering",
    }
    if expired:
        data["exp"] = int(time.time()) - 3600
    elif "exp" not in data:
        data["exp"] = int(time.time()) + 3600
    return jwt.encode(data, secret, algorithm=algorithm)


def _make_settings(**overrides: Any) -> Settings:
    """Create a Settings instance suitable for testing."""
    defaults: dict[str, Any] = {
        "app_name": "SkillHub-Test",
        "app_version": "0.0.1-test",
        "debug": True,
        "database_url": "sqlite:///:memory:",
        "jwt_secret": TEST_JWT_SECRET,
        "jwt_algorithm": TEST_JWT_ALGORITHM,
        "jwt_expire_minutes": 60,
        "stub_auth_enabled": False,
    }
    defaults.update(overrides)
    return Settings(**defaults)


@pytest.fixture()
def db_session() -> MagicMock:
    """Return a mock database session for unit tests."""
    return MagicMock()


@pytest.fixture()
def test_settings() -> Settings:
    """Return a test-oriented Settings object."""
    return _make_settings()


@pytest.fixture()
def app(db_session: MagicMock, test_settings: Settings) -> Flask:
    """Return a Flask application wired with test settings and mock DB."""
    config = AppConfig(
        app_name=test_settings.app_name,
        app_version=test_settings.app_version,
        debug=test_settings.debug,
        settings=test_settings,
        session_factory=db_session,
    )
    return create_app(config=config)


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Return a test client bound to the test app."""
    return app.test_client()


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Return Authorization headers with a valid test JWT."""
    token = make_token()
    return {"Authorization": f"Bearer {token}"}
```

**Key points:**
- `db_session` fixture returns a `MagicMock` — unit tests do not touch a real DB
- `session_factory` injection via `AppConfig` (ADR-001 Section 6)
- `make_token()` is a module-level function (not a fixture) so tests can call it with custom payloads
- `auth_headers` convenience fixture for tests that need authenticated requests

### Acceptance Criteria

- [ ] All tests in `test_conftest.py` pass
- [ ] `app` fixture returns an `APIFlask` instance
- [ ] `client` fixture returns a `FlaskClient`
- [ ] `make_token()` generates valid JWTs accepted by the auth hook
- [ ] `auth_headers` fixture produces headers that pass authentication
- [ ] `db_session` fixture returns a mock (no real DB connection)
- [ ] All previous test files (`test_app_factory.py`, `test_auth.py`, `test_health.py`, `test_validation.py`) still pass
- [ ] `ruff check apps/api/` passes
- [ ] Full test suite: `mise run test:api:flask` all green

### DO NOT

- Do NOT create a real database in test fixtures — mock only for Phase 1
- Do NOT use `pytest-asyncio` or any async fixtures
- Do NOT import from `apps/fast-api/` in test code
- Do NOT use `monkeypatch` for session injection — use constructor injection
- Do NOT make `make_token` a fixture — keep it as a plain function for flexibility

---

## Prompt 8 — Extract `audit_log_append()` to `libs/python-common`

**Goal:** Extract the `_write_audit()` function from `apps/fast-api/skillhub/services/submissions.py` into `libs/python-common/skillhub_common/audit.py` as `audit_log_append()`, making it available to both Flask and FastAPI apps.

**Time estimate:** 15-20 minutes

### Context

The `_write_audit()` helper at `apps/fast-api/skillhub/services/submissions.py:37-55` writes to the append-only `audit_log` table. Both the Flask port and the existing FastAPI app need this function. Extracting it to `libs/python-common` prevents duplication.

Current implementation:
```python
def _write_audit(
    db: Session,
    *,
    event_type: str,
    actor_id: UUID,
    target_type: str,
    target_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append a row to the audit log."""
    entry = AuditLog(
        id=uuid.uuid4(),
        event_type=event_type,
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
        metadata_=metadata,
    )
    db.add(entry)
```

### Files to Modify/Create

| Action | File | Purpose |
|--------|------|---------|
| Create | `libs/python-common/skillhub_common/audit.py` | `audit_log_append()` |
| Edit | `libs/python-common/skillhub_common/__init__.py` | Export `audit_log_append` |
| Edit | `apps/fast-api/skillhub/services/submissions.py` | Replace `_write_audit` with import |
| Create | `libs/python-common/tests/test_audit.py` | Tests for the extracted function |

### Test-First Instructions

**Write these tests BEFORE implementing:**

Create `libs/python-common/tests/test_audit.py`:

```python
"""Tests for audit_log_append utility."""
from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, call

import pytest

from skillhub_common.audit import audit_log_append


class TestAuditLogAppend:
    def test_adds_entry_to_session(self) -> None:
        db = MagicMock()
        audit_log_append(
            db,
            event_type="submission.created",
            actor_id=uuid.uuid4(),
            target_type="submission",
            target_id="sub-123",
        )
        db.add.assert_called_once()

    def test_entry_has_correct_event_type(self) -> None:
        db = MagicMock()
        audit_log_append(
            db,
            event_type="submission.approve",
            actor_id=uuid.uuid4(),
            target_type="submission",
            target_id="sub-456",
        )
        entry = db.add.call_args[0][0]
        assert entry.event_type == "submission.approve"

    def test_entry_has_uuid_id(self) -> None:
        db = MagicMock()
        audit_log_append(
            db,
            event_type="test.event",
            actor_id=uuid.uuid4(),
            target_type="test",
            target_id="t-1",
        )
        entry = db.add.call_args[0][0]
        assert isinstance(entry.id, uuid.UUID)

    def test_metadata_passed_through(self) -> None:
        db = MagicMock()
        meta = {"key": "value", "count": 42}
        audit_log_append(
            db,
            event_type="test.event",
            actor_id=uuid.uuid4(),
            target_type="test",
            target_id="t-1",
            metadata=meta,
        )
        entry = db.add.call_args[0][0]
        assert entry.metadata_ == meta

    def test_metadata_defaults_to_none(self) -> None:
        db = MagicMock()
        audit_log_append(
            db,
            event_type="test.event",
            actor_id=uuid.uuid4(),
            target_type="test",
            target_id="t-1",
        )
        entry = db.add.call_args[0][0]
        assert entry.metadata_ is None

    def test_does_not_commit(self) -> None:
        """audit_log_append must NOT commit — the caller owns the transaction."""
        db = MagicMock()
        audit_log_append(
            db,
            event_type="test.event",
            actor_id=uuid.uuid4(),
            target_type="test",
            target_id="t-1",
        )
        db.commit.assert_not_called()

    def test_uses_imperative_event_vocabulary(self) -> None:
        """Bug #7 fix: verify imperative verbs, not past tense."""
        # This test documents the contract — event_type should use
        # approve/reject/request_changes, NOT approved/rejected
        db = MagicMock()
        audit_log_append(
            db,
            event_type="submission.approve",  # imperative, not "approved"
            actor_id=uuid.uuid4(),
            target_type="submission",
            target_id="sub-1",
        )
        entry = db.add.call_args[0][0]
        assert entry.event_type == "submission.approve"
```

### Implementation Specifications

#### `libs/python-common/skillhub_common/audit.py`

```python
"""Audit log utilities — append-only audit trail.

This module is framework-agnostic. It receives a SQLAlchemy Session
and writes AuditLog entries. It does NOT commit — the caller owns
the transaction.
"""
from __future__ import annotations

import uuid as _uuid
from typing import Any
from uuid import UUID

from skillhub_db.models.audit import AuditLog
from sqlalchemy.orm import Session


def audit_log_append(
    db: Session,
    *,
    event_type: str,
    actor_id: UUID,
    target_type: str,
    target_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append a row to the audit log.

    Does NOT call db.commit() — the calling service owns the transaction.
    """
    entry = AuditLog(
        id=_uuid.uuid4(),
        event_type=event_type,
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
        metadata_=metadata,
    )
    db.add(entry)
```

#### Update `libs/python-common/skillhub_common/__init__.py`

Add the export:
```python
from skillhub_common.audit import audit_log_append

__all__ = ["audit_log_append"]
```

#### Update `apps/fast-api/skillhub/services/submissions.py`

Replace the local `_write_audit` function with an import:
```python
from skillhub_common.audit import audit_log_append
```

Then find-and-replace all calls from `_write_audit(db, ...)` to `audit_log_append(db, ...)`.

**Bug #7 fix:** While updating callsites, change any past-tense event types to imperative:
- `"submission.approved"` -> `"submission.approve"`
- `"submission.rejected"` -> `"submission.reject"`
- `"submission.rejectd"` -> `"submission.reject"` (typo fix from known bug list)

### Acceptance Criteria

- [ ] All tests in `test_audit.py` pass
- [ ] `audit_log_append` is importable from `skillhub_common`
- [ ] `audit_log_append` does NOT call `db.commit()`
- [ ] `_write_audit` no longer exists in `submissions.py`
- [ ] All existing FastAPI tests still pass: `mise run test:api:fastapi`
- [ ] `ruff check libs/python-common/` passes
- [ ] `mypy libs/python-common/ --strict` passes
- [ ] Event types use imperative vocabulary (Bug #7 resolved)

### DO NOT

- Do NOT add `db.commit()` to `audit_log_append` — services own their transactions
- Do NOT add UPDATE or DELETE operations on audit_log (append-only per CLAUDE.md security rules)
- Do NOT change the AuditLog model — only extract the writing helper
- Do NOT remove `_write_audit` from submissions.py without updating ALL callsites to use `audit_log_append`
- Do NOT leave any past-tense event types (`approved`, `rejected`, `rejectd`)

---

## Cross-Cutting Concerns

### Future-Proofing Columns (Alembic Migration)

During Phase 1, create an Alembic migration adding these columns to the `submissions` table:

```python
# In the Flask app's migration (or shared libs/db migration)
op.add_column("submissions", sa.Column("parent_submission_id", sa.UUID(), sa.ForeignKey("submissions.id"), nullable=True))
op.add_column("submissions", sa.Column("revision_number", sa.Integer(), nullable=False, server_default="1"))
op.add_column("submissions", sa.Column("submitted_via", sa.VARCHAR(20), nullable=False, server_default="form"))
```

This migration should be created after Prompt 2 (scaffold) and can be executed at any point during Phase 1. It does not block any other prompt.

### Dependency Graph Between Prompts

```
Prompt 1 (rename) ──► Prompt 2 (scaffold) ──► Prompt 3 (app factory)
                                                    │
                                          ┌─────────┼─────────┐
                                          ▼         ▼         ▼
                                    Prompt 4    Prompt 5   Prompt 6
                                    (auth)     (health)   (validation)
                                          │         │         │
                                          └─────────┼─────────┘
                                                    ▼
                                              Prompt 7
                                          (test infra)

Prompt 8 (audit extract) — independent, can run anytime after Prompt 1
```

### Verification Checklist (Run After All Prompts Complete)

```bash
# All Flask tests pass
mise run test:api:flask

# All FastAPI tests still pass (no regression)
mise run test:api:fastapi

# Lint clean
ruff check apps/api/
ruff check apps/fast-api/
ruff check libs/python-common/

# Type check clean
mypy apps/api/skillhub_flask/ --strict
mypy apps/fast-api/skillhub/ --strict

# Coverage gate
mise run test:api:flask:coverage
```
