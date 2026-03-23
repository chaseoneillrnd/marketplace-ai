# SkillHub Codebase Map

> Navigational index. Code is source of truth. Updated 2026-03-21.

## File Tree

```
marketplace-ai/
├── apps/
│   ├── api/                # FastAPI backend (Python 3.12)
│   │   ├── skillhub/       # App source (29 files)
│   │   │   ├── routers/    # 8 route modules
│   │   │   ├── services/   # 8 service modules
│   │   │   └── schemas/    # Pydantic models per domain
│   │   └── tests/          # 20 test files
│   ├── web/                # React 18 + Vite + TS
│   │   └── src/
│   │       ├── components/ # Reusable UI components
│   │       ├── views/      # 5 page views
│   │       ├── hooks/      # Custom hooks (auth, flags, skills)
│   │       ├── lib/        # API client, auth, theme utils
│   │       └── context/    # Auth, Flags, Theme providers
│   └── mcp-server/         # Python MCP server (8 tools)
│       ├── skillhub_mcp/   # Server + tool implementations
│       └── tests/          # 11 test files
├── libs/
│   ├── db/                 # SQLAlchemy 2 models + Alembic
│   │   ├── skillhub_db/models/  # 9 model files, 23 tables
│   │   ├── alembic/        # Migration config
│   │   └── scripts/        # seed.py
│   ├── python-common/      # Shared Python utils (placeholder)
│   ├── shared-types/       # TS types (placeholder, for OpenAPI gen)
│   └── ui/                 # Shared React components (placeholder)
├── docs/                   # Documentation
├── specs/                  # OpenAPI, feature specs
├── design/                 # Design tokens, style guide
├── mise.toml               # 60+ task definitions
├── docker-compose.yml      # postgres, redis, api, mcp, web
├── nx.json                 # Monorepo task graph
└── .gitlab-ci.yml          # 5-stage CI pipeline
```

---

## Domain 1: Identity & Auth

```
apps/api/skillhub/routers/auth.py       → Stub auth + OAuth stubs
apps/api/skillhub/dependencies.py       → JWT validation, get_current_user
libs/db/skillhub_db/models/user.py      → User model
libs/db/skillhub_db/models/division.py  → Division model (8 seeded)
libs/db/skillhub_db/models/oauth_session.py → OAuth session tracking
apps/web/src/hooks/useAuth.ts           → Auth context hook
apps/web/src/lib/auth.ts                → JWT decode, token storage
apps/web/src/components/AuthModal.tsx    → Login modal UI
```

**Relationships**: Auth gates every protected route. Division extracted from JWT claims. Stub auth (dev) bypasses OAuth.

---

## Domain 2: Skills Core (Browse/Search/Filter)

```
apps/api/skillhub/routers/skills.py     → GET /skills, GET /skills/{slug}
apps/api/skillhub/services/skills.py    → Query builder, sorting, filtering
apps/api/skillhub/schemas/skill.py      → SkillSummary, SkillDetail, BrowseParams
libs/db/skillhub_db/models/skill.py     → Skill, SkillVersion, Category, Tags
apps/web/src/views/HomeView.tsx         → Featured + suggested rails
apps/web/src/views/BrowseView.tsx       → Category + division filter grid
apps/web/src/views/SearchView.tsx       → Full-text search
apps/web/src/views/FilteredView.tsx     → Sidebar facets
apps/web/src/views/SkillDetailView.tsx  → Tabs: Overview, How to Use, Install, Reviews
apps/web/src/hooks/useSkills.ts         → Skills data fetching
```

**Relationships**: Skills depend on categories, divisions, tags. Social layer writes counters. MCP server reads via API.

---

## Domain 3: Social Layer

```
apps/api/skillhub/routers/social.py     → Install, favorite, fork, follow
apps/api/skillhub/services/social.py    → Social action logic + audit logging
libs/db/skillhub_db/models/social.py    → Install, Favorite, Fork, Follow, Review, Comment, Reply, Vote models
apps/api/skillhub/routers/reviews.py    → Review CRUD + voting
apps/api/skillhub/services/reviews.py   → Bayesian avg_rating calculation
```

**Relationships**: Social writes denormalized counters on skills table. Division enforcement on install. Audit log on every action.

---

## Domain 4: Submission Pipeline

```
apps/api/skillhub/routers/submissions.py → POST /submissions, GET status
apps/api/skillhub/services/submission.py → 3-gate pipeline orchestration
apps/api/skillhub/services/llm_judge.py  → Gate 2 LLM evaluation (Bedrock)
libs/db/skillhub_db/models/submission.py → Submission, GateResult, AccessRequest
```

**Relationships**: Gate 1 = schema validation. Gate 2 = LLM judge (feature-flagged). Gate 3 = human review (admin). Published submissions become Skills.

---

## Domain 5: MCP Server

```
apps/mcp-server/skillhub_mcp/server.py     → MCP tool registration (8 tools)
apps/mcp-server/skillhub_mcp/api_client.py → HTTP client to FastAPI
apps/mcp-server/skillhub_mcp/tools/        → install, search, get_skill, update, list_installed, fork, submit, status
```

**Relationships**: Delegates all data ops to FastAPI. Division enforcement before local file writes. Powers Claude Code CLI integration.

---

## Domain 6: Feature Flags & Admin

```
apps/api/skillhub/routers/flags.py      → GET /flags (division-aware)
apps/api/skillhub/services/flags.py     → Flag resolution with overrides
apps/api/skillhub/routers/admin.py      → Review queue, emergency removal, audit log
apps/api/skillhub/services/admin.py     → Admin operations
apps/web/src/hooks/useFlag.ts           → useFlag(key) → boolean
libs/db/skillhub_db/models/flags.py     → FeatureFlag model
libs/db/skillhub_db/models/audit.py     → AuditLog (append-only)
```

**Relationships**: Flags gate features (LLM judge, MCP install, gamification). Admin routes require platform_team/security_team roles.

---

## Domain 7: Database & Migrations

```
libs/db/skillhub_db/base.py             → Base, UUIDMixin, TimestampMixin
libs/db/skillhub_db/session.py          → get_db session generator
libs/db/skillhub_db/models/             → 9 model files, 23 tables
libs/db/alembic/versions/001_initial_schema.py → Full schema migration
libs/db/scripts/seed.py                 → Divisions, categories, flags, test user
```

**Relationships**: All apps depend on db models. API uses session.py for DI. Alembic manages schema lifecycle.

---

## Domain 8: Frontend Infrastructure

```
apps/web/src/lib/api.ts                 → Typed fetch wrapper + auth injection
apps/web/src/lib/theme.ts               → Dark/light mode persistence
apps/web/src/context/                   → AuthContext, FlagsContext, ThemeContext
apps/web/src/components/SkillCard.tsx    → Skill grid card
apps/web/src/components/Nav.tsx          → Navigation bar
apps/web/src/components/DivisionChip.tsx → Division badge
```

**Relationships**: API client injects Bearer tokens. Theme persisted to localStorage. Flags context fetches on auth change.

---

## Domain 9: DevOps & Quality

```
docker-compose.yml                       → 5 services (pg, redis, api, mcp, web)
.gitlab-ci.yml                           → 5 stages: lint→test→typecheck→build→security
mise.toml                                → 60+ tasks
.pre-commit-config.yaml                  → ruff, eslint, prettier
.env.example                             → All env vars documented
```

**Relationships**: CI mirrors mise tasks. Docker Compose for local dev. Pre-commit enforces format on commit.

---

## Architectural Relationships

```
User Request → React SPA (apps/web)
  → FastAPI (apps/api) via REST /api/v1/*
    → SQLAlchemy ORM → PostgreSQL 16
    → Redis 7 (cache, sessions)

Claude Code → MCP Server (apps/mcp-server)
  → FastAPI (apps/api) via internal REST
    → PostgreSQL 16

Submission → Gate 1 (schema) → Gate 2 (LLM/Bedrock) → Gate 3 (human) → Published Skill

Auth: JWT (stub dev / OAuth prod) → get_current_user dependency → division enforcement
```

---

## Database Schema (23 tables, 5 domains)

| Domain | Tables |
|--------|--------|
| Identity | users, divisions, oauth_sessions |
| Skill Core | skills, skill_versions, categories, skill_divisions, skill_tags, trigger_phrases |
| Social | installs, favorites, forks, follows, reviews, review_votes, comments, replies, comment_votes |
| Submission | submissions, submission_gate_results, division_access_requests |
| Platform | feature_flags, audit_log |

---

## Top 25 Value Areas

Ranked by impact on marketplace success, user value, and technical leverage.

| # | Area | Domain | Why It Matters |
|---|------|--------|----------------|
| 1 | **Skills Browse/Search/Filter API** | Skills Core | Primary discovery UX — drives engagement |
| 2 | **Division-based Access Control** | Auth/Security | Core security model — wrong = data leak |
| 3 | **Submission Pipeline (3-gate)** | Submission | Quality gate — keeps marketplace trustworthy |
| 4 | **MCP Install Flow** | MCP Server | Developer UX — CLI install is the killer feature |
| 5 | **Skill Detail View (4 tabs)** | Frontend | Conversion page — where installs happen |
| 6 | **Review & Rating System** | Social | Social proof drives adoption |
| 7 | **JWT Auth + Stub Auth** | Auth | Foundation — every route depends on this |
| 8 | **Database Models (23 tables)** | Database | Schema correctness = data integrity |
| 9 | **Feature Flags (division-aware)** | Platform | Safe rollouts, A/B testing per division |
| 10 | **LLM Judge (Gate 2)** | Submission | Automated quality at scale |
| 11 | **Audit Log (append-only)** | Platform | Compliance, debugging, accountability |
| 12 | **Install/Uninstall with Counters** | Social | Tracks adoption, feeds trending |
| 13 | **Fork System (upstream-tracked)** | Social | Enables customization without fragmentation |
| 14 | **Trending/Sorting Signals** | Skills Core | Surfaces best content dynamically |
| 15 | **Comment/Reply Threading** | Social | Community engagement, support |
| 16 | **Admin Review Queue** | Admin | Platform Team workflow — approves/rejects |
| 17 | **Home View (featured + suggested)** | Frontend | First impression, personalization |
| 18 | **OAuth Integration** | Auth | Production auth — SSO required |
| 19 | **Alembic Migrations** | Database | Schema evolution without downtime |
| 20 | **API Client (typed fetch)** | Frontend | Type-safe frontend-backend contract |
| 21 | **Skill Versioning** | Skills Core | Safe updates, rollback capability |
| 22 | **Division Access Requests** | Submission | Cross-division collaboration |
| 23 | **Favorites/Follows** | Social | Personal curation, author notifications |
| 24 | **Docker Compose Stack** | DevOps | Developer onboarding in minutes |
| 25 | **CI/CD Pipeline (5 stages)** | DevOps | Automated quality enforcement |

---

## Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| DATABASE_URL | PostgreSQL connection | postgresql://skillhub:skillhub@localhost:5432/skillhub |
| REDIS_URL | Redis connection | redis://localhost:6379/0 |
| JWT_SECRET | Token signing key | change-me-in-production |
| STUB_AUTH_ENABLED | Dev auth bypass | true |
| LLM_ROUTER_URL | Bedrock LLM endpoint | (empty = disabled) |
| VITE_API_URL | Frontend API base | http://localhost:8000 |
| SKILLHUB_API_URL | MCP→API base | http://localhost:8000 |
