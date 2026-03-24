# Phase 5: FastAPI Removal and Cleanup

**Project:** SkillHub FastAPI-to-Flask Migration
**Phase:** 5 of 5
**Audience:** Claude Code agents executing via subagent-driven-development
**Prerequisites:** Phase 4 complete (all endpoints ported, security tests green)
**Tasks:** 2 (5.1 Delete FastAPI and Update Configs, 5.2 Update Project Documentation)

This is a greenfield PoC with no live users. There is no canary ramp, traffic splitting, or rollback window. The Flask app is the only backend; FastAPI is dead code to be removed.

---

## How to Use This Guide

Each prompt below is designed to be copy-pasted into a Claude Code agent session.
Prompts are ordered and must be executed sequentially.
Each prompt includes verification steps that MUST pass before proceeding.

---

## Task 5.1: Delete FastAPI and Update Configs (Simple Swap)

### Prompt 5.1.1: Remove apps/fast-api and Update docker-compose

**Goal:** Remove the preserved FastAPI application directory and point docker-compose at the Flask app.

**Time estimate:** 5-10 minutes

#### Context

The original FastAPI application was preserved as `apps/fast-api/` during migration so the Flask port could claim `apps/api/`. The Flask port is complete. The FastAPI code is dead weight.

#### Files to Modify

| Action | Path |
|--------|------|
| Delete | `apps/fast-api/` (entire directory) |
| Edit | `docker-compose.yml` — api service targets Flask |
| Edit | `docker-compose.prod.yml` (if it exists) — same changes |

#### Step-by-Step Instructions

1. **Verify `apps/fast-api` exists.** If it does not, skip the deletion and note it.

2. **Delete the directory:**
   ```bash
   rm -rf apps/fast-api
   ```

3. **Update `docker-compose.yml`:**
   - The `api` service command must use gunicorn (not uvicorn):
     ```yaml
     command: gunicorn -w 4 -b 0.0.0.0:8000 "skillhub.main:create_app()"
     ```
   - Remove any service named `api-fastapi` or `fastapi` if present.
   - Remove any nginx upstream that references a FastAPI backend.
   - If there is traffic-splitting logic (FLASK_TRAFFIC_PCT or similar), remove it entirely.

4. **Update `docker-compose.prod.yml`** (if it exists) with the same changes.

5. **Clean up related artifacts:**
   - Remove `FLASK_TRAFFIC_PCT` from `.env` and `.env.example` if present.
   - Remove any canary/migration nginx templates if they exist.
   - Remove `scripts/migration/` directory if it exists and contains only migration-phase scripts.

#### Acceptance Criteria

- [ ] `ls apps/` shows: `api`, `mcp-server`, `web` (no `fast-api`)
- [ ] `grep -r "fast-api" docker-compose*.yml` returns nothing
- [ ] `grep -r "uvicorn" docker-compose*.yml` returns nothing
- [ ] `docker compose config` validates without errors
- [ ] `docker compose config` shows gunicorn command for the api service

#### DO NOT

- Do NOT remove `apps/api/` — that is the Flask application
- Do NOT remove any libs/ directories
- Do NOT modify any Python source files in `apps/api/`

---

### Prompt 5.1.2: Update mise.toml and Remove FastAPI Dependencies

**Goal:** Retarget bare mise task names to Flask, remove `:fastapi` aliases, and remove FastAPI-only Python dependencies.

**Time estimate:** 10-15 minutes

#### Context

Bare task names (`dev:api`, `test:api`, etc.) may still reference uvicorn or FastAPI paths. The `:fastapi` task aliases created during migration are no longer needed — there is no grace period for a PoC with no users. FastAPI-only packages (`fastapi`, `uvicorn`, `pytest-asyncio`) should be removed from dependencies.

#### Files to Modify

| Action | Path |
|--------|------|
| Edit | `mise.toml` — retarget tasks, remove `:fastapi` aliases |
| Edit | `apps/api/pyproject.toml` (or equivalent) — remove FastAPI deps |
| Edit | Any `requirements*.txt` referencing FastAPI deps |

#### Step-by-Step Instructions

**Part A: mise.toml task retargeting**

1. **`[tasks."dev:api"]`** — Change command from uvicorn to Flask dev server:
   ```
   run = "flask --app skillhub.main:create_app run --reload --host 0.0.0.0 --port 8000"
   ```
   Update env to include `FLASK_APP = "skillhub.main:create_app"`. Ensure PYTHONPATH includes `apps/api:libs/db:libs/python-common`.

2. **`[tasks."dev:all"]`** — If it references uvicorn, replace with the flask dev server command.

3. **`[tasks."smoke"]`** — If it starts uvicorn, replace with flask dev server. Health check endpoint should remain the same.

4. **`[tasks."gen:openapi"]`** — Update to use apiflask spec generation:
   ```
   run = """python -c "
   from skillhub.main import create_app
   import json
   app = create_app()
   with app.app_context():
       print(json.dumps(app.spec, indent=2))
   " > specs/openapi.json"""
   ```

5. **`[tasks."quality-gate"]`** — If it references FastAPI-specific paths, update to Flask paths.

6. **Remove all `:fastapi` task aliases** — Delete any task with `:fastapi` in the name (e.g., `dev:api:fastapi`, `test:api:fastapi`, `lint:api:fastapi`).

7. **Remove all `migration:*` tasks** — Delete `migration:gate-check`, `migration:ramp-status`, `migration:trace-compare`, and any other migration-specific tasks.

8. **Remove any Phase 2 / ADR-001 alias-preservation comments** from mise.toml.

**Part B: Remove FastAPI dependencies**

1. Check which of these packages are ONLY used by FastAPI (not by Flask, MCP server, or libs):
   - `fastapi`
   - `uvicorn`
   - `pytest-asyncio`
   - `httpx` (keep if used by tests or other code outside FastAPI)
   - `python-multipart` (keep if Flask/apiflask needs it)

2. For each confirmed FastAPI-only package, remove it from:
   - `apps/api/pyproject.toml` (or `setup.cfg` or `requirements.txt`)
   - Any `requirements*.txt` files
   - Dockerfile pip install lines

3. Do NOT remove: `pydantic`, `pydantic-settings`, `httpx` (if used elsewhere), or anything that `libs/` or `apps/mcp-server` depends on.

4. Run `pip install -e apps/api[dev]` to verify dependencies resolve.

#### Acceptance Criteria

- [ ] `mise run dev:api` starts Flask (not uvicorn)
- [ ] `mise tasks` shows no `:fastapi` aliases
- [ ] `mise tasks` shows no `migration:*` tasks
- [ ] `grep -r "uvicorn" mise.toml` returns nothing
- [ ] `pip show fastapi` returns "not found" (not installed in current env)
- [ ] `pip show uvicorn` returns "not found"
- [ ] `python -c "import skillhub.main"` succeeds
- [ ] `mise run test:api` passes

#### DO NOT

- Do NOT remove `pydantic` or `pydantic-settings` — the Flask app uses them
- Do NOT remove `httpx` without first confirming nothing else imports it
- Do NOT leave `:fastapi` aliases "for later" — remove them now

---

## Task 5.2: Update Project Documentation

### Prompt 5.2.1: Update CLAUDE.md, Remove OpenAPI Baseline, and Run Final Quality Gate

**Goal:** Update project documentation to reflect the Flask backend, remove the stale OpenAPI baseline, and verify everything passes.

**Time estimate:** 5-10 minutes

#### Context

CLAUDE.md still references FastAPI. The `specs/openapi-baseline.json` file was a snapshot of the FastAPI spec used for migration parity checks — Flask now generates its own spec as the source of truth. A final quality gate confirms the migration is clean.

#### Files to Modify

| Action | Path |
|--------|------|
| Edit | `CLAUDE.md` — FastAPI references become Flask/APIFlask |
| Delete | `specs/openapi-baseline.json` (if it exists) |

#### Step-by-Step Instructions

**Part A: Update CLAUDE.md**

Make these changes in `/Users/chase/wk/marketplace-ai/CLAUDE.md`:

1. Project Overview section:
   - OLD: "Built as an NX monorepo with FastAPI backend, React frontend, and MCP server."
   - NEW: "Built as an NX monorepo with Flask/APIFlask backend, React frontend, and MCP server."

2. Tech Stack section:
   - OLD: `**Backend:** FastAPI (Python 3.12) + SQLAlchemy 2 + Alembic`
   - NEW: `**Backend:** Flask/APIFlask (Python 3.12) + SQLAlchemy 2 + Alembic`

3. Security section:
   - OLD: "Division enforcement happens in FastAPI — never client-side"
   - NEW: "Division enforcement happens in Flask before_request — never client-side"

4. Add to Design Documents section:
   - `docs/migration/adr-001-fastapi-to-flask.md` — Migration ADR (FastAPI to Flask)

5. Do NOT remove any existing design document references.
6. Do NOT change sections that are already correct.

**Part B: Remove OpenAPI baseline**

1. If `specs/openapi-baseline.json` exists, delete it.
2. Check for scripts or tests that reference `openapi-baseline.json` and update them to use `specs/openapi.json` instead.

**Part C: Final quality gate**

1. Run:
   ```bash
   mise run quality-gate
   ```

2. If any failures occur, fix them (likely import path issues or stale references) and re-run.

3. Run additional checks:
   ```bash
   mise run gen:openapi    # verify OpenAPI generation works
   mise run smoke          # verify Flask app starts and serves /health
   docker compose config --quiet  # verify docker-compose is valid
   ```

4. Check for stale references:
   ```bash
   grep -rn "TODO.*fastapi\|FIXME.*fastapi\|TODO.*migration" apps/ libs/
   ```
   If any remain, resolve them or convert to tech-debt tickets.

#### Acceptance Criteria

- [ ] `grep -c "FastAPI" CLAUDE.md` returns 0 (the ADR filename reference `fastapi-to-flask` is acceptable as it is a proper noun in a path)
- [ ] `grep "Flask/APIFlask" CLAUDE.md` returns matches
- [ ] `grep "before_request" CLAUDE.md` returns a match
- [ ] `ls specs/openapi-baseline.json` returns "No such file" (or file was already absent)
- [ ] `grep -r "openapi-baseline" .` returns zero matches (excluding git history)
- [ ] `mise run quality-gate` exits 0
- [ ] `docker compose config --quiet` exits 0

#### DO NOT

- Do NOT rewrite CLAUDE.md from scratch — make targeted edits only
- Do NOT remove the `skillhub-design.md` or `skillhub-technical-guide.md` references
- Do NOT skip the quality gate — it is the final proof the migration is clean
