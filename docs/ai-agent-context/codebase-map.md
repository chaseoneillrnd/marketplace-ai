# SkillHub Codebase Map

> Navigational index of architecturally significant files. Code is source of truth. Updated 2026-03-24.

## File Tree

```
marketplace-ai/
├── apps/
│   ├── api/                     # Flask/APIFlask backend (Python 3.12)
│   │   ├── skillhub/            # Business logic layer
│   │   │   ├── schemas/         # Pydantic v2 request/response models
│   │   │   └── services/        # Service functions (DB queries, business rules)
│   │   ├── skillhub_flask/      # Flask application layer
│   │   │   ├── blueprints/      # Route handlers (14 blueprint modules)
│   │   │   ├── app.py           # Flask app factory + middleware
│   │   │   ├── auth.py          # JWT decode, division enforcement
│   │   │   ├── config.py        # pydantic-settings configuration
│   │   │   ├── db.py            # SQLAlchemy session management
│   │   │   └── validation.py    # Request validation helpers
│   │   └── tests/               # pytest test suite
│   ├── web/                     # React 18 + Vite + TypeScript
│   │   └── src/
│   │       ├── components/      # Reusable UI (Nav, SkillCard, AuthModal, admin/, charts/, submit/)
│   │       ├── views/           # Page views (Browse, Search, Filtered, SkillDetail, Feedback)
│   │       │   ├── admin/       # Admin panel (Dashboard, Queue, Skills, Flags, Export, Roadmap, Feedback)
│   │       │   └── submit/      # Skill submission flow
│   │       ├── hooks/           # Custom hooks (useSkills, useAdminQueue, useAuth, useFeedback, ...)
│   │       ├── context/         # React contexts (Auth, Flags, Theme, Announcer)
│   │       └── lib/             # API client, auth helpers, theme utils
│   ├── mcp-server/              # MCP server for Claude Code integration
│   │   └── skillhub_mcp/
│   │       ├── tools/           # 10 MCP tools (search, install, submit, fork, ...)
│   │       ├── server.py        # FastMCP registration + shared API client
│   │       ├── api_client.py    # httpx async client with Bearer auth
│   │       └── config.py        # Server settings
│   └── docs/                    # VitePress documentation site
├── libs/
│   ├── db/                      # Database layer (shared across Python apps)
│   │   ├── skillhub_db/
│   │   │   ├── models/          # SQLAlchemy 2 ORM models (11 modules)
│   │   │   ├── base.py          # Declarative base + mixins (UUIDMixin, TimestampMixin)
│   │   │   └── session.py       # Engine + sessionmaker factory
│   │   ├── migrations/versions/ # Alembic migrations (6 versions)
│   │   └── scripts/seed.py      # Database seeding
│   ├── shared-types/            # TypeScript types generated from OpenAPI
│   │   └── src/index.ts         # Exported interfaces, enums, slug maps
│   ├── python-common/           # Shared Python utilities
│   └── ui/                      # Shared React component stubs
├── specs/
│   ├── openapi.json             # OpenAPI 3.0 spec (source of truth for types)
│   └── features/                # Feature specifications
├── design/                      # Design system (tokens.json, style-guide.md)
├── docs/                        # Project documentation
│   ├── ai-agent-context/        # This file lives here
│   ├── repo-master-docs/        # Governance docs (architecture, compliance, decisions)
│   └── superpowers/plans/       # Implementation plans
└── mise.toml                    # Task runner (dev, test, quality-gate, db commands)
```

---

## Skills Domain (Browse / Search / Filter)

Primary flow: **View → useSkillBrowse hook → API client → skills blueprint → skills service → Skill model**

### Frontend

```
apps/web/src/
├── views/
│   ├── BrowseView.tsx           # Category-based browsing with division filters
│   ├── FilteredView.tsx         # Advanced filtering sidebar (category, division, sort, verified, etc.)
│   ├── SearchView.tsx           # Text search results (reads ?q= from URL)
│   └── SkillDetailView.tsx      # Full skill detail + install/favorite actions
├── hooks/useSkills.ts           # useSkillBrowse(params) + useSkillDetail(slug)
├── components/
│   ├── SkillCard.tsx            # Skill tile for browse grids
│   └── Nav.tsx                  # Search input → navigate to /search?q=...
└── lib/api.ts                   # api.get('/api/v1/skills', params) with Bearer auth
```

**BrowseParams**: `q, category, divisions[], sort, install_method, verified, featured, favorited, page, per_page`
**SortOptions**: `trending | installs | rating | newest | updated`

### Backend

```
apps/api/
├── skillhub_flask/blueprints/skills.py    # GET /api/v1/skills (list), GET /api/v1/skills/<slug> (detail)
├── skillhub/services/skills.py            # browse_skills() — filter/sort/paginate, batch resolve authors & user annotations
└── skillhub/schemas/skill.py              # SkillSummary, SkillDetail, SkillBrowseResponse, SortOption
```

**Search**: ILIKE on `name`, `short_desc`, and `tags` (no full-text index)
**Division filter**: Subquery on `skill_divisions` join table
**Sort columns map**: `SORT_COLUMNS` dict → `trending_score`, `install_count`, `avg_rating`, `published_at`, `updated_at`
**Batch helpers**: `_batch_resolve_authors()`, `_batch_user_installed()`, `_batch_user_favorited()`

### Database

```
libs/db/skillhub_db/models/skill.py
├── Skill                # Core table: slug, name, category, status, counters (install_count, trending_score, avg_rating)
├── SkillVersion         # Version history: content, frontmatter, content_hash (indexed)
├── SkillDivision        # Many-to-many: (skill_id, division_slug)
├── SkillTag             # Many-to-many: (skill_id, tag)
└── TriggerPhrase        # Skill trigger phrases for MCP matching
```

**Relationships**: Skills → Versions, Divisions, Tags, TriggerPhrases (all eager-loaded in browse)

---

## MCP Install Flow

Primary flow: **MCP tool → API client → social blueprint → social service → Install model**

### MCP Server

```
apps/mcp-server/skillhub_mcp/
├── server.py                    # FastMCP app, _shared_client (APIClient singleton), tool registration
├── api_client.py                # httpx.AsyncClient wrapper: get/post/patch/delete with Bearer token
├── tools/
│   ├── install.py               # install_skill() — fetch version content, write SKILL.md locally, POST /install
│   ├── uninstall.py             # uninstall_skill() — remove local dir, DELETE /install
│   ├── list_installed.py        # list_installed() — scan filesystem, compare versions for staleness
│   ├── search.py                # search_skills() — proxy to GET /api/v1/skills with filters
│   ├── get_skill.py             # get_skill() — GET /api/v1/skills/<slug>
│   ├── submit.py                # submit_skill() — POST /api/v1/submissions
│   ├── fork.py                  # fork_skill() — POST /api/v1/skills/<slug>/fork
│   ├── update.py                # update installed skill to latest version
│   ├── status.py                # check submission status
│   └── login.py                 # authenticate via stub credentials
└── config.py                    # Settings: api_base_url, host, port
```

**Install flow**: Fetch skill content → check division access (JWT claims vs skill divisions) → write to filesystem → record via API
**Dual-state model**: Local filesystem (SKILL.md) + server-side Install record; uninstall is soft-delete (`uninstalled_at`)

### Backend (Install/Uninstall)

```
apps/api/
├── skillhub_flask/blueprints/social.py    # POST/DELETE /api/v1/skills/<slug>/install
├── skillhub/services/social.py            # install_skill(), uninstall_skill() + division auth check
└── skillhub/schemas/social.py             # InstallRequest, InstallResponse
```

**install_skill()**: Check division auth → check no active install → INSERT Install → increment `Skill.install_count` → audit log
**uninstall_skill()**: Soft-delete (SET `uninstalled_at`) → decrement with `GREATEST(count-1, 0)` → audit log

### Database

```
libs/db/skillhub_db/models/social.py
├── Install              # skill_id, user_id, version, method, installed_at, uninstalled_at (soft delete)
├── Favorite             # skill_id, user_id, created_at
├── Follow               # follower_id, following_id
└── Fork                 # source_skill_id, forked_skill_id, forked_by
```

---

## Admin Review Queue (3-Gate Submission Pipeline)

Primary flow: **Submit → Gate 1 (schema) → Gate 2 (LLM) → Queue → Gate 3 (human) → Publish**

### Frontend

```
apps/web/src/
├── views/admin/
│   ├── AdminQueueView.tsx       # Split-panel: queue list + detail (tabs: Details, Activity)
│   ├── AdminDashboardView.tsx   # Stat cards incl. "Pending Reviews" + submission funnel chart
│   └── AdminSkillsView.tsx      # Published skills management
├── hooks/
│   ├── useAdminQueue.ts         # fetchQueue(), claim(), decide() → review-queue endpoints
│   └── useAdminDashboard.ts     # Summary stats, funnel, time-series, top-skills
└── views/submit/
    └── SubmitSkillPage.tsx       # User-facing submission form
```

**Queue UI**: Keyboard shortcuts (j/k navigate, a approve, r reject, x request changes), self-approval prevention

### Backend

```
apps/api/
├── skillhub_flask/blueprints/
│   ├── review_queue.py          # GET /admin/review-queue, POST .../claim, POST .../decision
│   └── submissions.py           # POST /submissions (create), POST .../resubmit, POST .../scan
├── skillhub/services/
│   ├── review_queue.py          # get_review_queue(), claim_submission(), decide_submission()
│   ├── submissions.py           # create_submission(), resubmit_submission() + gate pipeline
│   └── llm_judge.py             # Gate 2: LLM-based content evaluation
└── skillhub/schemas/
    ├── review_queue.py          # ReviewQueueItem schema
    └── submission.py            # SubmissionCreate, SubmissionResponse schemas
```

**Auth**: All review-queue routes require `is_platform_team=True`
**Self-approval guard**: `submission.submitted_by != reviewer_id` enforced in `decide_submission()`

### Status Transitions

```
submitted → gate1_passed → gate2_passed ──→ approved → published
                         → gate2_flagged ──→ approved → published
                                          → rejected (end)
                                          → gate3_changes_requested → resubmit → gate1...
         → gate1_failed (end)
         → gate2_failed (end)
```

**Queue shows**: Only `gate2_passed` and `gate2_flagged` submissions, ordered oldest-first

### Database

```
libs/db/skillhub_db/models/
├── submission.py        # Submission: status (SubmissionStatus enum), gate3_* fields, revision tracking
│                        # SubmissionGateResult: gate (1/2/3), result, findings, score
└── audit.py             # AuditLog: append-only event trail (submission.created/claimed/approved/rejected/...)
```

---

## Auth & Division Enforcement

```
apps/api/skillhub_flask/
├── auth.py              # decode_token(), get_current_user(), division enforcement in before_request
├── blueprints/stub_auth.py  # Dev-only: POST /auth/stub-login → returns JWT with division claims
└── blueprints/divisions.py  # GET /api/v1/divisions → list available divisions
```

**Pattern**: JWT contains `division` claim → `before_request` extracts to `g.current_user` → services check against `SkillDivision` table

---

## Social & Feedback

```
apps/api/skillhub_flask/blueprints/social.py    # Favorites, follows, installs, forks, reviews
apps/api/skillhub_flask/blueprints/feedback.py  # Feature requests with upvoting
apps/api/skillhub/services/social.py            # All social actions + counter updates + audit
apps/api/skillhub/services/feedback.py          # Feedback CRUD + upvote/unvote
libs/db/skillhub_db/models/feedback.py          # Feedback, FeedbackUpvote models
```

---

## Analytics & Admin

```
apps/api/skillhub_flask/blueprints/
├── analytics.py         # GET /admin/analytics/* (summary, funnel, time-series, top-skills)
├── admin.py             # Admin skill management (feature, verify, deprecate, bulk ops)
├── exports.py           # CSV/JSON data export endpoints
├── flags.py             # Feature flag management
└── roadmap.py           # Public roadmap CRUD
```

---

## Architectural Relationships

```
User Request → React Views (apps/web)
  → Custom Hooks (useSkills, useAdminQueue, ...)
    → API Client (lib/api.ts, Bearer auth)
      → Flask Blueprints (apps/api/skillhub_flask/blueprints/)
        → Service Layer (apps/api/skillhub/services/)
          → SQLAlchemy Models (libs/db/skillhub_db/models/)
            → PostgreSQL

MCP Tool Invocation → MCP Server (apps/mcp-server)
  → API Client (skillhub_mcp/api_client.py)
    → Flask Blueprints (same backend)
      → Service Layer → Models → PostgreSQL
  → Local Filesystem (SKILL.md writes)
```

**Cross-cutting**:
- `libs/shared-types/` → consumed by `apps/web` (TypeScript interfaces, slug maps)
- `libs/db/` → consumed by `apps/api` and `apps/mcp-server` (via services)
- `specs/openapi.json` → source of truth for `libs/shared-types/` generation
- `libs/python-common/` → shared utilities for all Python apps

---

## Database Schema

**Models** (via SQLAlchemy 2 + Alembic):
- `Skill`, `SkillVersion`, `SkillDivision`, `SkillTag`, `TriggerPhrase` → Skill catalog
- `Submission`, `SubmissionGateResult` → 3-gate pipeline
- `Install`, `Favorite`, `Follow`, `Fork` → Social interactions
- `Review` → Skill reviews/ratings
- `Feedback`, `FeedbackUpvote` → Feature requests
- `User`, `OAuthSession` → Identity
- `Division` → Org unit for access control
- `FeatureFlag` → Runtime feature gates
- `AuditLog` → Append-only event trail
- `AnalyticsEvent`, `DailySkillMetric` → Usage analytics

6 migrations: initial schema → analytics → feedback/platform → review queue → submission enhancements → feedback upvotes

---

## Configuration

- **Task runner**: `mise.toml` — `dev:api`, `dev:web`, `test:api`, `test:web`, `quality-gate`, `db:migrate`, `db:seed`
- **Monorepo**: NX with `@nx/enforce-module-boundaries` for JS/TS import rules
- **Python config**: pydantic-settings (`skillhub_flask/config.py`, `skillhub_mcp/config.py`)
- **OpenAPI spec**: `specs/openapi.json` → generates `libs/shared-types/`
- **Design tokens**: `design/tokens.json` + `design/style-guide.md`
