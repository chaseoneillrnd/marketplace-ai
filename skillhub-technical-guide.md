# SkillHub — Technical Implementation Guide

## For Claude Code — Complete Handoff Document

**Project:** SkillHub  
**Starting Point:** Empty directory + approved design doc  
**Approach:** TDD-first, vertical slices, spec-driven, NX monorepo + mise

---

## Supplementary Materials

┌─────────────────────────────────────────────────────────────────────────────┐
│ COMPANION DOCUMENT                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  📊 skillhub-diagrams.md                                                    │
│                                                                             │
│  Visual architecture companion with 20+ Mermaid diagrams covering:         │
│  • System topology and container diagram (Section 1)                        │
│  • Full data model ERDs (Section 2)                                         │
│  • Auth and MCP sequence diagrams (Section 3)                               │
│  • Submission pipeline state machine (Section 4)                            │
│  • LLM judge flow (Section 5)                                               │
│  • CI/CD pipeline flowchart (Section 6)                                     │
│                                                                             │
│  USAGE: Reference by section when executing prompts.                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

---

## Table of Contents

1. [Global Standards](#global-standards)
2. [Stage 0 — Monorepo Scaffold](#stage-0)
3. [Stage 1 — Database Foundation](#stage-1)
4. [Stage 2 — Flask/APIFlask Core](#stage-2)
5. [Stage 3 — Skills API](#stage-3)
6. [Stage 4 — Auth & Users](#stage-4)
7. [Stage 5 — Social Layer](#stage-5)
8. [Stage 6 — Submission Pipeline](#stage-6)
9. [Stage 7 — MCP Server](#stage-7)
10. [Stage 8 — React Frontend](#stage-8)
11. [Stage 9 — Feature Flags & Admin](#stage-9)
12. [Stage 10 — AI Docs, CI & Repo Master](#stage-10)
13. [Quick Reference: Prompt Sequence](#quick-reference)

---

## Global Standards

Apply to every prompt. Non-negotiable.

```yaml
Code Quality:
  - Python: ruff (lint + format), mypy --strict, no type: ignore without comment
  - TypeScript: eslint, prettier, tsc --noEmit clean
  - No commented-out code committed
  - No print() / console.log() in production paths — use structured logging

Testing:
  - TDD: write tests FIRST, then implementation
  - Python coverage gate: ≥80% (pytest-cov --cov-fail-under=80)
  - TypeScript coverage gate: ≥80% (vitest --coverage)
  - Test file lives adjacent to implementation: test_auth.py next to auth.py

Security:
  - No secrets in code — all via Settings (pydantic-settings)
  - JWT: decode before trusting, never trust raw claims without verification
  - Division enforcement happens in Flask (before_request) — never client-side
  - audit_log: append-only, no UPDATE/DELETE from application code

Definition of Done (every prompt):
  - [ ] Tests written first and passing
  - [ ] No type errors (mypy / tsc)
  - [ ] No lint warnings (ruff / eslint)
  - [ ] mise run quality-gate passes
  - [ ] Acceptance criteria verified
  - [ ] No secrets in committed code
```

---

## Stage 0 — Monorepo Scaffold

> 📊 See Section 1 of skillhub-diagrams.md for project structure diagram.

**Goal:** Working NX monorepo with all config files, empty app skeletons, Docker Compose up, mise tasks wired.

---

### Phase 0.1 — NX Workspace Init

#### Prompt 0.1.1 — Initialize NX monorepo

```
Create a new NX monorepo called "skillhub" from an empty directory.

Requirements:
- NX workspace with preset: ts (TypeScript)
- Node 20, Python 3.12
- Root package.json with workspaces: ["apps/*", "libs/*"]
- tsconfig.base.json with strict: true, paths for @skillhub/* libs
- nx.json: targetDefaults for build, test, lint with cache enabled
- .gitignore: node_modules, __pycache__, .env, dist, .nx/cache, .venv

File structure:
skillhub/
├── nx.json
├── package.json
├── tsconfig.base.json
├── .gitignore
└── .env.example     (copy from design doc section 4c)

Write tests FIRST for:
- nx graph --file=output.json exits 0 (project graph is valid)

Do NOT:
- Install any app-specific dependencies yet
- Create any apps or libs yet
- Use npx create-nx-workspace (do it manually for control)

Acceptance Criteria:
- [ ] npx nx graph generates without errors
- [ ] tsconfig.base.json has strict: true
- [ ] .env.example contains all variables from design doc
- [ ] .gitignore excludes .env, dist, __pycache__, .venv
```

---

#### Prompt 0.1.2 — Create app and lib skeletons

```
Scaffold empty app and lib directories with minimal package.json / pyproject.toml.

Requirements:
- apps/web/ — React + Vite + TypeScript (npm create vite@latest)
- apps/api/ — Python package (pyproject.toml, uv init)
- apps/mcp-server/ — Python package (pyproject.toml, uv init)
- libs/ui/ — TypeScript lib with package.json name: @skillhub/ui
- libs/shared-types/ — TypeScript lib with package.json name: @skillhub/shared-types
- libs/python-common/ — Python package name: skillhub-common
- libs/db/ — Python package name: skillhub-db
- Each Python package has: [project] name, version, dependencies = [], [tool.ruff]

File structure (show all pyproject.toml and package.json paths):
apps/web/package.json
apps/api/pyproject.toml
apps/mcp-server/pyproject.toml
libs/ui/package.json
libs/shared-types/package.json
libs/python-common/pyproject.toml
libs/db/pyproject.toml

Write tests FIRST for:
- All package.json files have name and version fields
- All pyproject.toml files have [project] with name and version

Do NOT:
- Install dependencies yet
- Write any application code
- Configure Vite or React beyond the init defaults

Acceptance Criteria:
- [ ] npm install succeeds from root
- [ ] uv sync --all-packages succeeds from root
- [ ] nx show projects lists: web, api, mcp-server
- [ ] All lib names follow @skillhub/* pattern
```

---

### Phase 0.2 — Configuration Files

#### Prompt 0.2.1 — mise.toml

```
Create the complete mise.toml from the design doc (Section 3b) verbatim.

Requirements:
- Copy every task from the approved mise.toml in the design doc
- Verify [env] section uses _.file = ".env"
- All Python tasks use "uv run" prefix
- All NX tasks use "npx nx" prefix

File: mise.toml (root)

Write tests FIRST for:
- mise tasks lists without errors
- mise run install exits 0

Do NOT:
- Add tasks not in the design doc
- Change task names
- Skip any task namespace

Acceptance Criteria:
- [ ] mise tasks shows all namespaces: dev, build, test, lint, format, db, gen, docker, quality-gate
- [ ] mise run install completes without errors
- [ ] mise run format:check exits 0 on empty project
```

---

#### Prompt 0.2.2 — Docker Compose and Dockerfiles

```
Create docker-compose.yml, docker-compose.prod.yml, and apps/api/Dockerfile
from the design doc (Sections 4a, 4b, 4d).

Requirements:
- docker-compose.yml: postgres, redis, api, mcp-server, web services
- Healthchecks on postgres and redis
- API mounts ./apps/api and ./libs as volumes for hot reload
- docker-compose.prod.yml overrides: no volume mounts, worker mode, nginx for web
- apps/api/Dockerfile: python:3.12-slim, uv, PYTHONPATH includes /libs

Files:
docker-compose.yml
docker-compose.prod.yml
apps/api/Dockerfile
apps/mcp-server/Dockerfile   (mirror API Dockerfile, different app path)

Write tests FIRST for:
- docker compose config --quiet exits 0 (valid compose file)

Do NOT:
- Expose production secrets in compose files
- Use root user in Dockerfiles

Acceptance Criteria:
- [ ] docker compose config --quiet exits 0
- [ ] mise run db:up starts postgres with healthcheck passing
- [ ] mise run docker:down stops all services cleanly
```

---

#### Prompt 0.2.3 — Pre-commit and GitLab CI

```
Create .pre-commit-config.yaml and .gitlab-ci.yml from design doc
(Sections 5f and 5g) verbatim.

Requirements:
- .pre-commit-config.yaml: all hooks from design doc exactly
- .gitlab-ci.yml: all 5 stages from design doc exactly
- ruff version pinned to v0.4.0
- prettier version pinned to v4.0.0-alpha.8

Files:
.pre-commit-config.yaml
.gitlab-ci.yml

Write tests FIRST for:
- pre-commit validate-config exits 0
- yamllint .gitlab-ci.yml exits 0

Do NOT:
- Add hooks not in the design doc
- Change CI stage names

Acceptance Criteria:
- [ ] pre-commit validate-config .pre-commit-config.yaml succeeds
- [ ] yamllint .gitlab-ci.yml produces no errors
- [ ] pre-commit run --all-files on empty project exits 0
```

---

## Stage 1 — Database Foundation

> 📊 See Section 2 of skillhub-diagrams.md for full ERD.

**Goal:** All 15 tables created via Alembic, seed data loadable, models importable.

---

### Phase 1.1 — SQLAlchemy Models

#### Prompt 1.1.1 — Base and Identity models

```
In libs/db/skillhub_db/, create SQLAlchemy 2.x models for the Identity domain.

Requirements:
- libs/db/skillhub_db/base.py: DeclarativeBase, UUID primary keys, created_at default
- libs/db/skillhub_db/models/user.py: User model (all fields from design doc section 4)
- libs/db/skillhub_db/models/division.py: Division model (slug PK)
- libs/db/skillhub_db/models/oauth_session.py: OAuthSession model
- libs/db/skillhub_db/session.py: engine, SessionLocal, get_db generator
- Use Mapped[] and mapped_column() (SQLAlchemy 2.x syntax)
- All string fields have explicit length limits
- Enums use Python Enum class + SQLAlchemy Enum type

File structure:
libs/db/skillhub_db/
├── __init__.py
├── base.py
├── session.py
└── models/
    ├── __init__.py
    ├── user.py
    ├── division.py
    └── oauth_session.py

Write tests FIRST for:
- User model instantiates with required fields
- Division model uses slug as primary key
- OAuthSession has user_id foreign key to users
- session.py get_db yields and closes session

Do NOT:
- Use legacy Column() syntax — use mapped_column()
- Store raw tokens in oauth_sessions — only hashes
- Use String without length on indexed columns

Acceptance Criteria:
- [ ] from skillhub_db.models.user import User imports without error
- [ ] mypy passes on all model files
- [ ] All tests pass
```

---

#### Prompt 1.1.2 — Skill Core models

```
Create SQLAlchemy models for the Skill Core domain.

Requirements:
- models/skill.py: Skill, SkillVersion, SkillDivision, SkillTag, TriggerPhrase, Category
- Skill.status: Enum ("draft","published","deprecated","removed")
- Skill.install_method: Enum ("claude-code","mcp","manual","all")
- Skill.data_sensitivity: Enum ("low","medium","high","phi")
- Skill.author_type: Enum ("official","community")
- SkillVersion.frontmatter: JSON column (stores parsed YAML as dict)
- SkillVersion.content_hash: VARCHAR(64) indexed
- All denormalized counters (install_count etc.) default to 0
- trending_score: Numeric(10,4) default 0
- avg_rating: Numeric(3,2) default 0
- Relationships: Skill.versions, Skill.divisions, Skill.tags, Skill.trigger_phrases

Write tests FIRST for:
- Skill instantiates with required fields, counters default to 0
- SkillVersion content_hash is stored correctly
- SkillDivision composite relationship works
- Category slug is the primary key

Do NOT:
- Store SKILL.md content in the Skill table — only in SkillVersion
- Use nullable=False without a default on counter columns

Acceptance Criteria:
- [ ] All Skill domain models import cleanly
- [ ] Relationship lazy loading does not trigger N+1 in tests
- [ ] mypy passes
- [ ] All tests pass
```

---

#### Prompt 1.1.3 — Social, Submission, and Platform models

```
Create remaining SQLAlchemy models: Social, Submission, Platform domains.

Requirements (Social):
- models/social.py: Install, Fork, Favorite, Follow, Review, ReviewVote,
  Comment, Reply, CommentVote
- Review: UNIQUE constraint on (skill_id, user_id)
- Favorite: composite PK (user_id, skill_id)
- Follow: composite PK (follower_id, followed_user_id)
- Comment.deleted_at: nullable timestamp (soft delete)

Requirements (Submission):
- models/submission.py: Submission, SubmissionGateResult, DivisionAccessRequest
- Submission.status: Enum of all state machine values from design doc
- Submission.declared_divisions: JSON column
- SubmissionGateResult.findings: JSON column

Requirements (Platform):
- models/flags.py: FeatureFlag (key PK, division_overrides JSON)
- models/audit.py: AuditLog — append-only enforced via __table_args__ check

Write tests FIRST for:
- Review UNIQUE constraint raises IntegrityError on duplicate
- Favorite composite PK works
- Submission status defaults to "submitted"
- AuditLog raises on attempted update (test with raw SQL)

Do NOT:
- Add UPDATE or DELETE capabilities to AuditLog model
- Use mutable defaults for JSON columns (use default_factory)

Acceptance Criteria:
- [ ] All models import cleanly from skillhub_db.models
- [ ] Review UNIQUE constraint test passes
- [ ] AuditLog append-only test passes
- [ ] mypy passes on all model files
```

---

### Phase 1.2 — Migrations and Seeds

#### Prompt 1.2.1 — Alembic setup and initial migration

```
Set up Alembic in libs/db/ and generate the initial migration from all models.

Requirements:
- libs/db/alembic.ini: script_location = migrations, sqlalchemy.url from env
- libs/db/migrations/env.py: import all models, use async-compatible target_metadata
- Generate migration: 001_initial_schema.py via alembic revision --autogenerate
- Migration includes all 15 tables with correct constraints
- Add DB-level CHECK constraints for enums where appropriate
- Add database trigger to block UPDATE/DELETE on audit_log table

File structure:
libs/db/
├── alembic.ini
└── migrations/
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── 001_initial_schema.py

Write tests FIRST for:
- alembic upgrade head completes on fresh test DB
- alembic downgrade base completes without errors
- alembic check exits 0 after upgrade
- AuditLog UPDATE trigger raises exception

Do NOT:
- Handwrite the migration — generate it from models
- Skip the audit_log trigger
- Use alembic's synchronous engine if the app uses async

Acceptance Criteria:
- [ ] mise run db:migrate succeeds on fresh database
- [ ] mise run db:rollback:all leaves empty schema
- [ ] mise run db:check exits 0 after migrate
- [ ] AuditLog trigger test passes
- [ ] All 15 tables present after migration
```

---

#### Prompt 1.2.2 — Seed script

```
Create libs/db/scripts/seed.py to populate all seed tables.

Requirements:
Seed data (idempotent — safe to run multiple times):
- divisions: 8 rows (Engineering Org, Product Org, Finance & Legal,
  People & HR, Operations, Executive Office, Sales & Marketing, Customer Success)
- categories: 9 rows (Engineering, Product, Data, Security, Finance,
  General, HR, Research) with sort_order
- feature_flags: 4 rows:
    llm_judge_enabled: false
    featured_skills_v2: false
    gamification_enabled: false
    mcp_install_enabled: true
- stub user: id=00000000-0000-0000-0000-000000000001,
    email=test@acme.com, username=test, name=Test User,
    division=Engineering Org, role=Senior Engineer
- Use INSERT ... ON CONFLICT DO NOTHING for idempotency

Write tests FIRST for:
- Seed runs twice without error (idempotency)
- All 8 divisions present after seed
- All 4 feature flags present after seed
- Stub user present with correct division

Do NOT:
- Hard-delete and re-insert (breaks idempotency)
- Seed application data beyond what's listed

Acceptance Criteria:
- [ ] mise run db:seed succeeds on fresh migrated DB
- [ ] mise run db:seed run twice exits 0 with no duplicate errors
- [ ] SELECT count(*) FROM divisions = 8
- [ ] SELECT count(*) FROM feature_flags = 4
- [ ] Stub user exists with id 00000000-0000-0000-0000-000000000001
```

---

## Stage 2 — Flask/APIFlask Core

> 📊 See Section 3 of skillhub-diagrams.md for API request flow diagram.

**Goal:** Flask/APIFlask app factory running, health endpoint live, stub auth working, Swagger at /docs.

---

### Phase 2.1 — App Factory

#### Prompt 2.1.1 — config, main, dependencies

```
Create the Flask/APIFlask application scaffold.

Requirements:
- apps/api/skillhub/config.py: Pydantic Settings — verbatim from design doc section 4e
- apps/api/skillhub/main.py: create_app() factory — verbatim from design doc section 4e
- apps/api/skillhub/dependencies.py: get_db, get_current_user,
  require_platform_team, require_security_team — verbatim from design doc section 4f
- apps/api/skillhub/routers/health.py: GET /health → {status, version}
- PYTHONPATH must include /libs so skillhub_db is importable
- apps/api/pyproject.toml dependencies:
    apiflask>=1.3, gunicorn, pydantic-settings,
    sqlalchemy>=2.0, pyjwt, psycopg2-binary, alembic

Write tests FIRST for:
- GET /health returns 200 {status: ok, version: 1.0.0}
- create_app() returns Flask/APIFlask instance
- get_current_user raises 401 on missing token
- get_current_user raises 401 on expired token
- get_current_user raises 401 on invalid token
- require_platform_team raises 403 for non-platform-team user

Do NOT:
- Import database models in main.py at module level (use routers)
- Put business logic in dependencies.py
- Use global state outside of Settings

Acceptance Criteria:
- [ ] mise run dev:api starts without errors
- [ ] GET http://localhost:8000/health returns 200
- [ ] GET http://localhost:8000/docs returns 200 (Swagger UI)
- [ ] GET http://localhost:8000/openapi.json is valid OpenAPI 3.1
- [ ] All tests pass
- [ ] mypy passes
```

---

### Phase 2.2 — Stub Auth

#### Prompt 2.2.1 — Auth router with stub login

```
Create the auth router with stub credentials and OAuth stubs.

Requirements:
- apps/api/skillhub/routers/auth.py: verbatim from design doc section 4f
- Stub credentials: username=test / password=user
- JWT contains all STUB_USER fields from design doc
- STUB_AUTH_ENABLED=false must block /auth/token with 403
- /auth/oauth/{provider}: returns redirect URL (stub, not real)
- /auth/oauth/{provider}/callback: returns 501 (not yet implemented)
- /auth/me: returns current user from JWT (uses get_current_user)
- Supported providers: microsoft, google, okta, github, oidc
- Unknown provider returns 404

Write tests FIRST for:
- POST /auth/token with test/user returns 200 with access_token
- POST /auth/token with wrong password returns 401
- POST /auth/token with STUB_AUTH_ENABLED=false returns 403
- GET /auth/me with valid JWT returns user payload
- GET /auth/me with no token returns 401
- GET /auth/oauth/microsoft returns redirect_url and state
- GET /auth/oauth/unknown returns 404
- Token contains correct division=Engineering Org claim

Do NOT:
- Return raw passwords anywhere
- Log tokens or credentials
- Hard-code JWT_SECRET — must come from Settings

Acceptance Criteria:
- [ ] POST /auth/token test/user returns JWT
- [ ] JWT decoded manually contains all expected claims
- [ ] GET /auth/me returns user with division=Engineering Org
- [ ] All auth tests pass (≥80% coverage on auth.py)
- [ ] mise run quality-gate passes
```

---

## Stage 3 — Skills API

> 📊 See Section 2 of skillhub-diagrams.md for Skill domain ERD.

**Goal:** Full skills CRUD + browse/search/filter with all sorting signals working.

---

### Phase 3.1 — Skills Router

#### Prompt 3.1.1 — Skill schemas (Pydantic)

```
Create Pydantic v2 schemas for the Skills domain.

Requirements:
- apps/api/skillhub/schemas/skill.py:
    SkillSummary (for browse/search tiles — all fields needed by SkillCard component)
    SkillDetail (full detail page data including triggers, best_prompts, notes)
    SkillVersionResponse (version content + frontmatter)
    SkillBrowseParams (query params: q, category, divisions, sort, install_method,
        verified, featured, page, per_page)
    SkillBrowseResponse (items: list[SkillSummary], total, page, per_page, has_more)
- Sort enum: trending, installs, rating, newest, updated
- All schemas use model_config = ConfigDict(from_attributes=True)
- SkillSummary includes: id, slug, name, short_desc, category, divisions[],
  tags[], author, author_type, version, install_method, verified, featured,
  install_count, fork_count, favorite_count, avg_rating, rating_count, days_ago

Write tests FIRST for:
- SkillSummary instantiates from ORM Skill object
- SkillBrowseParams validates sort enum values
- per_page max 100 enforced by validator
- divisions is list[str] and defaults to []

Do NOT:
- Return password, token, or internal fields from any schema
- Use orm_mode=True (deprecated) — use model_config

Acceptance Criteria:
- [ ] All schemas import cleanly
- [ ] SkillSummary.model_validate(skill_orm_object) works
- [ ] mypy passes on all schema files
```

---

#### Prompt 3.1.2 — Skills router (GET /skills, GET /skills/{slug})

```
Implement the skills browse and detail endpoints.

Requirements:
- GET /api/v1/skills: paginated browse with all filter/sort params from SkillBrowseParams
  - Filter by category, divisions (any match), install_method, verified, featured
  - Sort: trending (trending_score DESC), installs (install_count DESC),
    rating (avg_rating DESC), newest (published_at DESC), updated (updated_at DESC)
  - Auth optional: if authenticated, annotate user's installed/favorited skills
  - Full-text search on q: search name, short_desc, tags via PostgreSQL ILIKE
    (pgvector embedding search is future — use ILIKE for now)
  - Eager load: skill.divisions, skill.tags
- GET /api/v1/skills/{slug}: full detail + current version content
  - Increment view_count (fire-and-forget, don't block response)
  - If authenticated: include user_has_installed, user_has_favorited

File structure:
apps/api/skillhub/
├── routers/skills.py
├── schemas/skill.py
└── services/skills.py    (query logic lives here, not in router)

Write tests FIRST for:
- GET /skills returns 200 with items[] and pagination metadata
- GET /skills?category=Engineering filters correctly
- GET /skills?divisions=Engineering+Org,Product+Org returns multi-division match
- GET /skills?sort=rating orders by avg_rating DESC
- GET /skills?q=review returns skills matching name/desc/tags
- GET /skills/pr-review-assistant returns full detail with triggers
- GET /skills/nonexistent returns 404
- Unauthenticated request returns skills without user annotations
- Authenticated request includes user_has_installed boolean

Do NOT:
- Put SQL queries in the router — use services/skills.py
- N+1 query on divisions or tags — use joinedload()
- Block the response on view_count increment

Acceptance Criteria:
- [ ] GET /api/v1/skills returns paginated results
- [ ] All filter params work correctly in tests
- [ ] GET /api/v1/skills?sort=trending ordered by trending_score
- [ ] No N+1 queries (check with SQLAlchemy echo=True in tests)
- [ ] Coverage ≥80% on skills.py and services/skills.py
```

---

#### Prompt 3.1.3 — Skill version endpoints

```
Implement version history and content endpoints.

Requirements:
- GET /api/v1/skills/{slug}/versions: list all published versions for a skill
  - Returns: [{ version, published_at, changelog_summary }]
  - Auth required
- GET /api/v1/skills/{slug}/versions/{version}: full version content
  - Returns: SkillVersionResponse (content, frontmatter, version, published_at)
  - Auth required
  - "latest" as version resolves to skill.current_version
- GET /api/v1/skills/{slug}/versions/latest: shortcut → latest version content

Write tests FIRST for:
- GET /versions returns list ordered by published_at DESC
- GET /versions/latest returns current_version content
- GET /versions/2.3.0 returns specific version
- GET /versions/nonexistent returns 404
- Unauthenticated request returns 401

Do NOT:
- Return content_hash to clients
- Allow unauthenticated access to version content

Acceptance Criteria:
- [ ] Version list ordered newest first
- [ ] "latest" alias works
- [ ] 404 on unknown version
- [ ] 401 on unauthenticated access
```

---

## Stage 4 — Auth & Users

> 📊 See Section 3 of skillhub-diagrams.md for auth sequence diagram.

**Goal:** Full user profile, favorites, installs, forks, follows all persisted and queryable.

---

#### Prompt 4.1.1 — Users router

```
Implement /users/me and personal collections endpoints.

Requirements:
- GET /api/v1/users/me: full profile from JWT + stats from DB
  - Stats: skills_installed (active installs), skills_submitted,
    reviews_written, forks_made
- GET /api/v1/users/me/installs: paginated list of installed skills
  - Filter: include uninstalled=false by default
- GET /api/v1/users/me/favorites: paginated list of favorited skills
- GET /api/v1/users/me/forks: paginated list of forked skills
- GET /api/v1/users/me/submissions: paginated list of own submissions with status
- All routes: Auth required

Write tests FIRST for:
- GET /users/me returns name, division, role from JWT
- Stats counts are accurate (install 2 skills → skills_installed=2)
- GET /users/me/installs returns correct skills
- Uninstalled skills excluded by default
- GET /users/me/favorites returns favorited skills

Acceptance Criteria:
- [ ] Profile stats accurate after install/favorite actions
- [ ] All collection endpoints paginated correctly
- [ ] Auth required on all endpoints (401 without token)
```

---

## Stage 5 — Social Layer

> 📊 See Section 2 of skillhub-diagrams.md for Social domain ERD.

**Goal:** Install, favorite, fork, follow, review, comment, and all voting endpoints working and writing to audit_log.

---

#### Prompt 5.1.1 — Install and social action endpoints

```
Implement install, favorite, fork, follow endpoints.

Requirements:
- POST /api/v1/skills/{slug}/install:
  - Body: { method: "claude-code"|"mcp"|"manual", version: string }
  - Checks division authorization (skill.divisions includes user.division)
  - If not authorized: 403 with { error: "division_restricted" }
  - Creates Install row
  - Increments skills.install_count via UPDATE ... SET install_count = install_count + 1
  - Writes audit_log row: event_type=skill.installed
  - Returns 201
- DELETE /api/v1/skills/{slug}/install:
  - Sets Install.uninstalled_at = now()
  - Writes audit_log: skill.uninstalled
- POST /api/v1/skills/{slug}/favorite: upsert Favorite, write audit_log
- DELETE /api/v1/skills/{slug}/favorite: delete Favorite, decrement counter
- POST /api/v1/skills/{slug}/fork:
  - Creates new Skill row (status=draft, author=current_user)
  - Creates Fork row linking original → forked
  - Returns 201 with new skill slug
- POST /api/v1/skills/{slug}/follow: upsert Follow (author of skill)

Write tests FIRST for:
- Install authorized division → 201 + install_count incremented
- Install unauthorized division → 403 with division_restricted
- Install writes to audit_log
- Duplicate favorite → 200 (idempotent)
- Fork creates new skill with correct upstream reference
- Follow upserts (second follow = no error)

Do NOT:
- Use raw SQL for counter increments — use SQLAlchemy UPDATE
- Forget audit_log entry on every social action

Acceptance Criteria:
- [ ] Division enforcement blocks unauthorized installs
- [ ] All counter increments are atomic (no race condition in tests)
- [ ] audit_log has row for every action
- [ ] Fork creates valid new skill record
```

---

#### Prompt 5.1.2 — Reviews and comments

```
Implement reviews and discussion thread endpoints.

Requirements (Reviews):
- GET /api/v1/skills/{slug}/reviews: paginated, sorted by helpful_count DESC
- POST /api/v1/skills/{slug}/reviews:
  - Auth required
  - Body: { rating: 1-5, body: string }
  - UNIQUE constraint enforced → 409 if already reviewed
  - Updates skills.avg_rating (Bayesian: (C*m + sum_ratings) / (C + count) where C=5, m=3.0)
  - Writes audit_log: review.created
- PATCH /api/v1/skills/{slug}/reviews/{id}: owner only, updates body/rating, recalculates avg
- POST /api/v1/skills/{slug}/reviews/{id}/vote:
  - Body: { vote: "helpful"|"unhelpful" }
  - Upsert ReviewVote, update review.helpful_count / unhelpful_count

Requirements (Comments):
- GET /api/v1/skills/{slug}/comments: paginated, nested replies included
- POST /api/v1/skills/{slug}/comments: auth required, body: { body: string }
- DELETE /api/v1/skills/{slug}/comments/{id}: soft delete (owner or platform team)
  - Replaces body with "[deleted]", sets deleted_at
- POST /api/v1/skills/{slug}/comments/{id}/replies: auth required
- POST /api/v1/skills/{slug}/comments/{id}/vote: upsert CommentVote, increment count

Write tests FIRST for:
- Second review by same user returns 409
- avg_rating recalculates correctly after new review (test Bayesian formula)
- PATCH review by non-owner returns 403
- Soft delete replaces body with [deleted]
- Vote upsert is idempotent

Acceptance Criteria:
- [ ] Bayesian avg_rating formula correct in unit test
- [ ] UNIQUE review constraint returns 409
- [ ] Soft delete does not physically remove row
- [ ] Comment votes idempotent
- [ ] Coverage ≥80% on reviews.py and comments.py
```

---

## Stage 6 — Submission Pipeline

> 📊 See Section 4 of skillhub-diagrams.md for submission state machine.

**Goal:** 3-gate submission pipeline end-to-end. LLM judge behind feature flag.

---

#### Prompt 6.1.1 — Submission create and Gate 1

```
Implement skill submission and Gate 1 (schema validation).

Requirements:
- POST /api/v1/submissions:
  - Auth required
  - Body: { name, short_desc, category, content (SKILL.md text),
    declared_divisions: string[], division_justification: string }
  - declared_divisions must not be empty → 422
  - division_justification must not be empty → 422
  - Generates display_id: SKL-{6 random uppercase alphanum}
  - Creates Submission row with status=submitted
  - Triggers Gate 1 synchronously (fast validation):
      - Required frontmatter fields present
      - Slug globally unique
      - Min 3 trigger phrases
      - Short description ≤80 chars
      - Cosine similarity check vs existing skills (stub: always pass for now)
  - If Gate 1 passes: status=gate1_passed, creates SubmissionGateResult(gate=1, result=passed)
  - If Gate 1 fails: status=gate1_failed, creates SubmissionGateResult with findings
  - Writes audit_log: submission.created
  - Returns 201 with submission_id, display_id, status, gate1_result

- GET /api/v1/submissions/{id}: auth required, owner or platform team

Write tests FIRST for:
- Empty declared_divisions returns 422
- Empty division_justification returns 422
- Missing required frontmatter fails Gate 1
- Short description >80 chars fails Gate 1
- <3 trigger phrases fails Gate 1
- Valid submission returns 201 with gate1_passed status
- display_id format is SKL-XXXXXX

Do NOT:
- Call LLM judge in Gate 1 — Gate 1 is schema-only
- Block response on Gate 2 — Gate 2 is async

Acceptance Criteria:
- [ ] Invalid submissions fail Gate 1 with specific findings
- [ ] Valid submission returns display_id and gate1_passed
- [ ] SubmissionGateResult row created for Gate 1
- [ ] audit_log row written
- [ ] Coverage ≥80%
```

---

#### Prompt 6.1.2 — Gate 2 (LLM Judge)

```
Implement Gate 2 — LLM evaluation via Bedrock router.

Requirements:
- services/llm_judge.py:
  - LLMJudgeService class
  - evaluate(content: str) → JudgeVerdict
  - Calls LLM_ROUTER_URL/v1/chat/completions with system + user prompts from design doc
  - Parses JSON response into JudgeVerdict (Pydantic model)
  - If LLM_ROUTER_URL is empty or llm_judge_enabled flag is False:
    return JudgeVerdict(pass_=True, score=85, findings=[], summary="Skipped")
  - Timeout: 30s
  - On HTTP error: return JudgeVerdict(pass_=False, score=0,
    findings=[{severity:high, category:quality, description:"Judge unavailable"}])

- Background task triggered after Gate 1 passes:
  POST /api/v1/admin/submissions/{id}/scan (also callable manually by Security Team)
  - Checks llm_judge_enabled feature flag
  - Calls LLMJudgeService.evaluate()
  - Updates submission status: gate2_passed or gate2_flagged or gate2_failed
  - Creates SubmissionGateResult(gate=2, ...)

Write tests FIRST for:
- LLM disabled → verdict is pass with score=85
- Critical finding → pass_=False
- Score <70 → gate2_failed
- Score ≥70 no critical → gate2_passed
- HTTP timeout → returns safe failure verdict
- LLM_ROUTER_URL empty → skip and pass

Do NOT:
- Call real Bedrock in tests — mock the HTTP client
- Block submission creation on Gate 2

Acceptance Criteria:
- [ ] Feature flag disables LLM call
- [ ] Mocked judge responses produce correct status transitions
- [ ] Timeout handled gracefully
- [ ] SubmissionGateResult created for Gate 2
```

---

#### Prompt 6.1.3 — Gate 3 and division access requests

```
Implement Gate 3 (human review) and division access requests.

Requirements (Gate 3):
- POST /api/v1/admin/submissions/{id}/review: Platform Team only
  - Body: { decision: "approved"|"changes_requested"|"rejected", notes: string }
  - approved → creates Skill + SkillVersion from submission content
  - changes_requested → status=gate3_changes_requested (submitter can resubmit)
  - rejected → status=rejected
  - Creates SubmissionGateResult(gate=3, reviewer_id=current_user.id)
  - Writes audit_log: submission.approved or submission.rejected

- GET /api/v1/admin/submissions: Platform Team only
  - Filter by status, paginated
  - Returns submissions with gate results

Requirements (Division Access Requests):
- POST /api/v1/skills/{slug}/access-request:
  - Auth required, user.division NOT in skill.divisions
  - Body: { reason: string }
  - Creates DivisionAccessRequest
- GET /api/v1/admin/access-requests: Platform Team only
- POST /api/v1/admin/access-requests/{id}/review: Platform Team only
  - approved → adds user.division to skill_divisions
  - denied → status=denied

Write tests FIRST for:
- Non-platform-team user cannot call /admin/submissions → 403
- Approved submission creates Skill with published status
- Skill slug derived from submission name (slugified)
- Access request from authorized division returns 400
- Approved access request adds division to skill_divisions

Acceptance Criteria:
- [ ] Full submission pipeline test: submit → gate1 → gate2 (mocked) → gate3 → published
- [ ] Skill created with correct author and version after approval
- [ ] Access request approval adds division correctly
- [ ] Platform Team gate on all admin routes
```

---

## Stage 7 — MCP Server

> 📊 See Section 3 of skillhub-diagrams.md for MCP install sequence diagram.

**Goal:** All 8 MCP tools working, local dev config tested, division enforcement on install.

---

#### Prompt 7.1.1 — MCP server scaffold and install tool

```
Create the SkillHub MCP server.

Requirements:
- apps/mcp-server/skillhub_mcp/server.py: MCP app using Python mcp SDK
  - Registers all 8 tools
  - Auth: reads Bearer token from MCP connection metadata
  - Passes token to all Flask API calls as Authorization header
- apps/mcp-server/skillhub_mcp/tools/install.py:
  - install_skill(slug: str, version: str = "latest") → dict
  - Calls GET /api/v1/skills/{slug}/versions/{version}
  - Validates division access (checks skill.divisions vs user division from JWT)
  - If authorized: writes content to ~/.local/share/claude/skills/{slug}/SKILL.md
    (or SKILLHUB_SKILLS_DIR env var override for testability)
  - Calls POST /api/v1/skills/{slug}/install with method="mcp"
  - Returns { success, version, path }
  - If not authorized: returns { success: false, error: division_restricted }
- apps/mcp-server/Dockerfile: mirrors API Dockerfile

Write tests FIRST for:
- install_skill with valid division writes SKILL.md to correct path
- install_skill with invalid division returns division_restricted
- install_skill with unknown slug returns error
- install_skill "latest" resolves to current version

Do NOT:
- Write SKILL.md if division check fails
- Make direct DB calls — everything through Flask API

Acceptance Criteria:
- [ ] MCP server starts: mise run dev:mcp
- [ ] install_skill test passes with mocked Flask API
- [ ] Division enforcement blocks unauthorized installs
- [ ] SKILL.md written to correct path on success
```

---

#### Prompt 7.1.2 — Remaining MCP tools

```
Implement the remaining 7 MCP tools.

Requirements:
- tools/search.py: search_skills(query, category?, divisions?, sort?) → list[SkillSummary]
  Calls GET /api/v1/skills
- tools/get_skill.py: get_skill(slug, version?) → SkillDetail
  Calls GET /api/v1/skills/{slug}/versions/{version}
- tools/update.py: update_skill(slug) → { updated: bool, from_version?, to_version? }
  Reads installed SKILL.md frontmatter, compares to API current_version, updates if stale
- tools/list_installed.py: list_installed() → list of installed skills with stale flag
  Reads ~/.local/share/claude/skills/ directory (or override)
- tools/fork.py: fork_skill(slug) → { success, new_slug }
  Calls POST /api/v1/skills/{slug}/fork
- tools/submit.py: submit_skill(skill_md_path: str) → { submission_id, display_id, status }
  Reads local file, calls POST /api/v1/submissions
- tools/status.py: get_submission_status(submission_id: str) → Submission
  Calls GET /api/v1/submissions/{id}

Write tests FIRST for each tool:
- search_skills returns list with correct fields
- update_skill detects stale version correctly
- list_installed reads local filesystem correctly
- update_skill no-ops when already at latest

Acceptance Criteria:
- [ ] All 8 tools registered in server.py
- [ ] search_skills returns results
- [ ] update_skill correctly detects stale/current
- [ ] All tool tests pass with mocked HTTP
```

---

## Stage 8 — React Frontend

> 📊 See Section 1 of skillhub-diagrams.md for component architecture.

**Goal:** v4 mockup wired to real API. No more mock data. Auth state from JWT.

---

#### Prompt 8.1.1 — API client and auth integration

```
Replace mock data in apps/web with real API calls.

Requirements:
- apps/web/src/lib/api.ts:
  - Typed fetch wrapper using shared-types/api.generated.ts
  - Injects Authorization: Bearer {token} on all authenticated requests
  - Base URL from import.meta.env.VITE_API_URL
  - Generic error handling: 401 → clear token + redirect to login
- apps/web/src/lib/auth.ts:
  - getToken() / setToken() / clearToken() — memory only (no localStorage)
  - decodeToken(token) → UserClaims
  - isExpired(token) → bool
- apps/web/src/hooks/useAuth.ts:
  - { user, login, logout, isAuthenticated }
  - login() → opens OAuth provider selection modal
  - After stub login: POST /auth/token, store token
- Wire AuthModal: on provider select → POST /auth/token (stub)
  on success: store token, set auth state, close modal

Write tests FIRST for:
- api.ts injects token when authenticated
- api.ts clears token on 401 response
- decodeToken parses JWT claims correctly
- isExpired returns true for past exp
- useAuth.login sets isAuthenticated=true

Do NOT:
- Store token in localStorage or sessionStorage
- Store token in React state visible to devtools

Acceptance Criteria:
- [ ] Login with test/user works end-to-end
- [ ] Token injected on authenticated requests
- [ ] 401 response clears auth state
- [ ] User division displayed in nav after login
```

---

#### Prompt 8.1.2 — Wire all views to real API

```
Replace all mock SKILLS array references with API calls.

Requirements:
- HomeView: GET /api/v1/skills?featured=true and GET /api/v1/skills (suggested)
- BrowseView: GET /api/v1/skills with category + division params
- SearchView: GET /api/v1/skills?q={query}
- FilteredView: GET /api/v1/skills with all facet params
- SkillDetailView: GET /api/v1/skills/{slug}
- Loading states: skeleton cards during fetch
- Error states: "Failed to load skills. Try again." with retry button
- Empty states: "No skills found" with clear filters CTA
- Pagination: infinite scroll or load-more on Browse/Filtered views

Write tests FIRST for:
- HomeView renders skeleton during loading
- HomeView renders skill cards after successful fetch
- HomeView renders error state on API failure
- FilteredView passes division filter params to API

Do NOT:
- Import SKILLS mock array anywhere in view components
- Fetch data in deeply nested components — fetch in view-level only

Acceptance Criteria:
- [ ] All 5 views load data from API
- [ ] Loading, error, empty states all render correctly
- [ ] Division filter passes correct params to GET /skills
- [ ] No mock data remains in view components
```

---

## Stage 9 — Feature Flags & Admin

> 📊 See Section 5 of skillhub-diagrams.md for admin flow diagram.

**Goal:** Feature flag SDK working client + server side. Admin routes for Platform Team.

---

#### Prompt 9.1.1 — Feature flags

```
Implement the feature flag system end-to-end.

Requirements (API):
- GET /api/v1/flags: returns active flags for requesting user context
  - Applies division_overrides: if user.division in override keys, use that value
  - No auth required (returns public flags for unauthenticated)
  - Authenticated: applies division overrides

Requirements (React):
- apps/web/src/hooks/useFlag.ts:
  - useFlag(key: string) → boolean
  - Fetches /api/v1/flags once on mount, caches in context
  - FlagsProvider wraps App, fetches on auth state change
- apps/web/src/lib/flags.ts:
  - FlagsContext, FlagsProvider, useFlags
  - Refetches on login/logout

Write tests FIRST for:
- GET /flags returns correct enabled status
- Division override applies: Engineering Org gets different value
- useFlag returns false for disabled flag
- useFlag returns true for enabled flag
- FlagsProvider fetches on mount

Acceptance Criteria:
- [ ] Flags returned correctly with division overrides applied
- [ ] useFlag("mcp_install_enabled") returns true (seed data)
- [ ] useFlag("llm_judge_enabled") returns false (seed data)
- [ ] Flag changes in DB reflected after FlagsProvider refetch
```

---

#### Prompt 9.1.2 — Admin endpoints and audit log

```
Implement remaining admin routes and audit log query.

Requirements:
- POST /api/v1/admin/skills/{slug}/feature:
  Platform Team only. Body: { featured: bool, featured_order?: int }
  Updates skill.featured, skill.featured_order
- POST /api/v1/admin/skills/{slug}/deprecate:
  Platform Team only. Sets skill.status=deprecated, skill.deprecated_at=now()
- DELETE /api/v1/admin/skills/{slug}:
  Security Team only. Sets skill.status=removed. Writes audit_log: skill.removed.
  Does NOT physically delete.
- GET /api/v1/admin/audit-log:
  Platform Team only. Paginated. Filters: event_type, actor_id, target_id, date range.
  Returns log entries with actor name resolved.

Write tests FIRST for:
- Non-platform-team gets 403 on feature/deprecate
- Non-security-team gets 403 on delete
- Deprecate sets deprecated_at timestamp
- Delete sets status=removed, does not physically remove row
- Audit log query with event_type filter

Acceptance Criteria:
- [ ] Role gates enforced correctly
- [ ] Deprecated skill still appears in browse (with status badge)
- [ ] Removed skill excluded from browse
- [ ] Audit log query returns paginated results with filters
```

---

## Stage 10 — AI Docs, CI & Repo Master

> 📊 See Section 6 of skillhub-diagrams.md for CI pipeline diagram.

**Goal:** All ai-agent docs written, CI pipeline passing, Repo Master bootstrapped.

---

#### Prompt 10.1.1 — Remaining AI agent docs

```
Write the remaining docs/ai-agent/ documents.

Requirements — each doc: Spartan tone, Mermaid-first, precise.

AUTH-FLOW.md:
  - Sequence diagrams: stub auth flow, production OAuth flow
  - JWT claims table
  - Division enforcement decision flowchart

SUBMISSION-PIPELINE.md:
  - State machine diagram (from design doc section 4)
  - Gate actors table (who runs each gate)
  - Timing/SLA table

FEATURE-FLAGS.md:
  - Flag keys table (key, default, description, division_override_capable)
  - Division override rule: how JSON overrides are evaluated
  - SDK usage: useFlag("key") pattern

MONOREPO-STRUCTURE.md:
  - NX project graph (Mermaid)
  - Lib dependency rules: who can import what
  - mise task reference table (all tasks one-liner)

DATA-MODELS.md:
  - Full ERD per domain (5 ERDs from design doc)
  - Constraint notes (UNIQUE, composite PK, append-only)
  - Counter update strategy (trigger vs application)

Write tests FIRST for:
- All Mermaid diagrams validate: npx @mermaid-js/mermaid-cli --validate

Do NOT:
- Exceed 500 lines per doc
- Use first person or passive voice
- Leave any Mermaid block unclosed

Acceptance Criteria:
- [ ] All 9 docs/ai-agent/ docs exist
- [ ] mise run docs:validate exits 0
- [ ] DOC-MAP.md links resolve to existing files
- [ ] No doc exceeds 500 lines
```

---

#### Prompt 10.1.2 — OpenAPI spec and TypeScript types

```
Generate and commit the OpenAPI spec and derived TypeScript types.

Requirements:
- mise run gen:openapi → writes specs/openapi.json
- mise run gen:types → writes libs/shared-types/src/api.generated.ts
- Verify openapi.json is valid OpenAPI 3.1
- Verify all routes from API-REFERENCE.md appear in spec
- Commit both files — they are source-of-truth for API contract
- Add openapi-freshness check to pre-commit (already in .pre-commit-config.yaml)
- Verify pre-commit openapi check catches a stale spec

Write tests FIRST for:
- specs/openapi.json parses as valid JSON
- All expected route paths present in spec
- api.generated.ts compiles without errors

Acceptance Criteria:
- [ ] specs/openapi.json committed and valid
- [ ] libs/shared-types/src/api.generated.ts compiles
- [ ] Modifying a route without running gen:openapi causes pre-commit failure
- [ ] GET http://localhost:8000/openapi.json matches committed spec
```

---

#### Prompt 10.1.3 — Repo Master bootstrap

```
Bootstrap Repo Master governance for the SkillHub repository.

Requirements:
- .claude/skills/repo-master/SKILL.md already present (from Stage 0)
- Invoke in Claude: "bootstrap repo master"
- Answer interview questions from the skill's bootstrap protocol:
    North star: Internal AI skills marketplace enabling org-wide Claude skill sharing
    Stakeholders: Platform Team, Security Team, all org employees
    Top 3 priorities: Core API complete, MCP install working, submission pipeline live
    Fragile areas: LLM judge Bedrock integration, division enforcement
    Compliance: Internal only, no HIPAA/PII
    Done this quarter: All Stage 1-9 prompts complete, first internal users onboarded
- Review generated MANIFEST.md — must be ≤50 lines
- Review generated VISION.md, ROADMAP.md, PRIORITIES.md

After bootstrap, add MANIFEST.md entry for each completed stage.

Write tests FIRST for:
- docs/repo-master-docs/MANIFEST.md exists
- MANIFEST.md is ≤50 lines
- docs/repo-master-docs/VISION.md exists
- docs/repo-master-docs/PRIORITIES.md exists

Do NOT:
- Write these files manually — let Repo Master generate them
- Exceed 50 lines in MANIFEST.md

Acceptance Criteria:
- [ ] docs/repo-master-docs/ fully populated
- [ ] MANIFEST.md ≤50 lines
- [ ] Each completed stage has a MANIFEST.md entry with confidence level
- [ ] mise run repo:manifest prints MANIFEST.md successfully
```

---

## Quick Reference: Prompt Sequence

| Stage | Phase | Prompt | Title | Est. Time |
|-------|-------|--------|-------|-----------|
| 0 | 0.1 | 0.1.1 | NX workspace init | 30m |
| 0 | 0.1 | 0.1.2 | App and lib skeletons | 30m |
| 0 | 0.2 | 0.2.1 | mise.toml | 20m |
| 0 | 0.2 | 0.2.2 | Docker Compose + Dockerfiles | 30m |
| 0 | 0.2 | 0.2.3 | Pre-commit + GitLab CI | 20m |
| 1 | 1.1 | 1.1.1 | Identity models | 45m |
| 1 | 1.1 | 1.1.2 | Skill Core models | 45m |
| 1 | 1.1 | 1.1.3 | Social + Submission + Platform models | 60m |
| 1 | 1.2 | 1.2.1 | Alembic setup + initial migration | 45m |
| 1 | 1.2 | 1.2.2 | Seed script | 30m |
| 2 | 2.1 | 2.1.1 | config, main, dependencies | 45m |
| 2 | 2.2 | 2.2.1 | Stub auth router | 45m |
| 3 | 3.1 | 3.1.1 | Skill schemas (Pydantic) | 30m |
| 3 | 3.1 | 3.1.2 | Skills router (browse + detail) | 60m |
| 3 | 3.1 | 3.1.3 | Version endpoints | 30m |
| 4 | 4.1 | 4.1.1 | Users router | 45m |
| 5 | 5.1 | 5.1.1 | Install + social actions | 60m |
| 5 | 5.1 | 5.1.2 | Reviews + comments | 60m |
| 6 | 6.1 | 6.1.1 | Submission + Gate 1 | 60m |
| 6 | 6.1 | 6.1.2 | Gate 2 (LLM Judge) | 60m |
| 6 | 6.1 | 6.1.3 | Gate 3 + access requests | 45m |
| 7 | 7.1 | 7.1.1 | MCP server + install tool | 60m |
| 7 | 7.1 | 7.1.2 | Remaining 7 MCP tools | 60m |
| 8 | 8.1 | 8.1.1 | API client + auth integration | 45m |
| 8 | 8.1 | 8.1.2 | Wire all views to API | 60m |
| 9 | 9.1 | 9.1.1 | Feature flags end-to-end | 45m |
| 9 | 9.1 | 9.1.2 | Admin endpoints + audit log | 45m |
| 10 | 10.1 | 10.1.1 | Remaining AI agent docs | 60m |
| 10 | 10.1 | 10.1.2 | OpenAPI spec + TypeScript types | 30m |
| 10 | 10.1 | 10.1.3 | Repo Master bootstrap | 30m |

**Total estimated time:** 18–22 hours across 29 prompts  
**Recommended session breaks:** After Stage 2 (auth working), Stage 5 (API complete), Stage 7 (MCP working)

---

## Appendices

### A. Dependency Graph

```
apps/web → libs/ui, libs/shared-types
apps/api → libs/db, libs/python-common
apps/mcp-server → libs/python-common
libs/ui → (no internal deps)
libs/shared-types → (no internal deps)
libs/db → libs/python-common
libs/python-common → (no internal deps)
```

**Rules:**
- No circular dependencies
- apps/* never import from other apps/*
- libs/* never import from apps/*

### B. Environment Variables by Service

| Variable | api | mcp-server | web |
|----------|-----|------------|-----|
| DATABASE_URL | ✓ | — | — |
| JWT_SECRET | ✓ | — | — |
| STUB_AUTH_ENABLED | ✓ | — | — |
| SKILLHUB_API_URL | — | ✓ | — |
| VITE_API_URL | — | — | ✓ |
| AWS_REGION | ✓ | — | — |
| LLM_ROUTER_URL | ✓ | — | — |

### C. Port Allocation

| Service | Port | Protocol |
|---------|------|----------|
| api | 8000 | HTTP |
| mcp-server | 8001 | HTTP (MCP) |
| web | 5173 | HTTP (dev) |
| postgres | 5432 | TCP |
| redis | 6379 | TCP |
