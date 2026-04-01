# SkillHub — Design Document

**Date:** 2026-03-20
**Status:** Approved
**Authors:** Chase O'Neill + Claude (brainstorming session)

---

## 1. What It Is

Internal AI skills marketplace. Org employees discover, install, review, and share Claude
skill files. Platform Team governs quality. Security Team governs safety.

---

## 2. Feature Catalogue

### Discovery & Browse
- Home: hero search, featured carousel, suggested-for-you rail (division-personalized)
- Browse: category pills + division multi-select + skill grid
- Search: semantic query, AI attribution, division refinement
- Filtered: sidebar facets — category, division (multi), sort, install method, verified

### Skill Detail
- Tabs: Overview, How to Use, Install, Reviews & Discussion
- Overview: description, when-to-use, trigger phrases, authorized divisions, tags
- How to Use: instructions, best prompts (copyable), notes callout
- Install: three install method cards; division access gate + request access
- Reviews & Discussion: star histogram; write review; threaded comments + replies; votes

### Social & Engagement
- Favorite, fork (upstream-tracked), follow author
- Install / uninstall (division-gated)
- Request access when division not authorized

### Submission Pipeline
- 3-step wizard: Basic Info → Division Declaration (required + justification) → Review
- Gates: schema validation → LLM judge (Bedrock) → Platform Team human review
- Status machine: submitted → gate1 → gate2 → gate3 → published / rejected

### Auth
- OAuth: Microsoft / Google / Okta / GitHub / Generic OIDC
- Stub: username=test / password=user → JWT (dev only, STUB_AUTH_ENABLED=true)
- JWT claims: user_id, email, name, division, role, is_platform_team, is_security_team

### Gamification & Metrics
- Counters: install_count, fork_count, favorite_count, view_count, review_count, avg_rating
- Sort signals: trending (install velocity), most installed, highest rated (Bayesian), newest, updated
- Featured: editorial boolean, Platform Team sets

### Feature Flags
- Table: key, enabled, division_overrides (JSONB), description
- GET /api/v1/flags — returns active flags for requesting user context
- Initial flags: llm_judge_enabled, featured_skills_v2, gamification_enabled, mcp_install_enabled

### Installation Surfaces
1. Claude Code CLI: `claude skill install pr-review-assistant`
2. SkillHub MCP Server: MCP tools via Claude Desktop or Claude Code MCP config
3. Manual: copy SKILL.md from detail page

### Admin
- Review queue (Gate 3), division access grants, emergency removal, audit log

### Theme
- Light / dark toggle. Smooth transition. React context.

---

## 3. Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | React 18 + Vite + TypeScript | Existing mockup, fast dev |
| Backend | Flask/APIFlask (Python 3.12) | Lightweight, APIFlask auto-OpenAPI, well-understood |
| MCP Server | Python + mcp SDK | Native Claude integration |
| Database | PostgreSQL 16 | JSON support, full-text search |
| Cache | Redis 7 | Sessions, rate limiting |
| ORM | SQLAlchemy 2 + Alembic | Type-safe, migration-first |
| LLM Judge | AWS Bedrock via LiteLLM router | OpenAI-spec compatible |
| Monorepo | NX + mise | Task runner + graph |
| Container | Docker + Compose | Reproducible local stack |
| CI/CD | GitLab CI | Quality gates, deploy |
| Testing | pytest + Vitest | Coverage gates ≥80% |
| Lint/Format | ruff + eslint + prettier | Enforced via pre-commit |

---

## 4. Data Models (15 tables across 5 domains)

### Identity
- `users`: id, email, username, name, division, role, oauth_provider, oauth_sub, is_platform_team, is_security_team
- `divisions`: slug (PK), name, color — seed table, 8 rows
- `oauth_sessions`: id, user_id, provider, access_token_hash, expires_at

### Skill Core
- `skills`: id, slug (UK), name, short_desc, category, author_id, current_version, install_method, data_sensitivity, external_calls, verified, featured, featured_order, status, + denormalized counters (install_count, fork_count, avg_rating, trending_score)
- `skill_versions`: id, skill_id, version, content, frontmatter (JSONB), changelog, content_hash, published_at
- `skill_divisions`: skill_id, division_slug — division authorization
- `skill_tags`: skill_id, tag
- `trigger_phrases`: id, skill_id, phrase
- `categories`: slug (PK), name, sort_order — seed table, 9 rows

### Social
- `installs`: id, skill_id, user_id, version, method, installed_at, uninstalled_at
- `forks`: id, original_skill_id, forked_skill_id, forked_by, upstream_version_at_fork
- `favorites`: user_id, skill_id (composite PK)
- `follows`: follower_id, followed_user_id (composite PK)
- `reviews`: id, skill_id, user_id, rating (1-5), body — UNIQUE(skill_id, user_id)
- `review_votes`: review_id, user_id, vote (enum: helpful/unhelpful)
- `comments`: id, skill_id, user_id, body, upvote_count, deleted_at (soft delete)
- `replies`: id, comment_id, user_id, body, deleted_at
- `comment_votes`: comment_id, user_id (composite PK)

### Submission
- `submissions`: id, display_id (UK), skill_id, submitted_by, name, short_desc, category, content, declared_divisions (JSONB), division_justification, status (state machine)
- `submission_gate_results`: id, submission_id, gate (1-3), result, findings (JSONB), score, reviewer_id
- `division_access_requests`: id, skill_id, requested_by, user_division, reason, status

### Platform
- `feature_flags`: key (PK), enabled, description, division_overrides (JSONB)
- `audit_log`: id, event_type, actor_id, target_type, target_id, metadata (JSONB), ip_address, created_at — append-only, trigger blocks UPDATE/DELETE

---

## 5. Monorepo Structure

```
skillhub/
├── apps/
│   ├── web/              React + Vite + TypeScript
│   ├── api/              Flask/APIFlask
│   └── mcp-server/       SkillHub MCP server
├── libs/
│   ├── ui/               Shared React components
│   ├── shared-types/     TypeScript types (auto-gen + manual)
│   ├── python-common/    Auth, config, logging, exceptions
│   └── db/               SQLAlchemy models + Alembic
├── docs/
│   ├── ai-agent/         Agent context docs (DOC-MAP.md + 9 docs)
│   ├── master-agent/     Stubbed
│   └── repo-master-docs/ Repo Master governance
├── specs/
│   ├── openapi.json      Generated by mise run gen:openapi
│   ├── schema.sql        Generated by mise run db:dump
│   └── features/         Spec-first feature docs
├── .claude/skills/repo-master/SKILL.md
├── mise.toml
├── nx.json
├── docker-compose.yml
├── .pre-commit-config.yaml
└── .gitlab-ci.yml
```

---

## 6. mise.toml Task Surface

| Namespace | Tasks |
|-----------|-------|
| `setup` / `install` | Full setup, npm install, uv sync |
| `dev:*` | web, api, mcp-server |
| `build:*` | web, docker, docker:api, docker:mcp |
| `test:*` | web, web:coverage, api, api:coverage, mcp, db |
| `lint:*` | web, api, mcp, fix |
| `format:*` | web, api, check |
| `typecheck:*` | web, api |
| `db:*` | up, down, migrate, rollback, make-migration, check, seed, reset, shell, dump |
| `gen:*` | openapi, types, migration |
| `docker:*` | up, down, logs, logs:api, reset, shell:api |
| `quality-gate` / `quality-gate:api` / `quality-gate:web` | Full CI gate locally |
| `ci` | Mirrors GitLab pipeline |
| `docs:*` | validate, map |
| `repo:*` | bootstrap, manifest, priorities |

---

## 7. Auth

### Stub (dev)
- POST /auth/token with form: username=test, password=user
- Returns JWT with Engineering Org / Senior Engineer claims
- STUB_AUTH_ENABLED=false in production

### Production
- GET /auth/oauth/{provider} → redirect URL
- GET /auth/oauth/{provider}/callback → exchange code → issue JWT
- Division + role extracted from OAuth token claims
- No separate profile table for these fields — identity is the source

---

## 8. LLM Judge

- Gate 2 of submission pipeline
- OpenAI-spec endpoint (LiteLLM router) → AWS Bedrock (Claude 3.5 Sonnet)
- Feature-flagged: llm_judge_enabled
- Prompt: structured JSON verdict — pass (bool), score (0-100), findings[], summary
- Auto-fail on any critical finding
- Score ≥ 70 required to pass gate

---

## 9. MCP Server

- Exposes 9 tools: search_skills, get_skill, install_skill, update_skill, uninstall_skill, list_installed, fork_skill, submit_skill, get_submission_status
- Delegates all data operations to the Flask API
- Division enforcement: validates JWT claims against skill.divisions before writing SKILL.md
- Local dev: http://localhost:8001/mcp
- Production: https://skillhub.acme.com/mcp (same config, different host)

---

## 10. Quality Gates

### Every Commit (pre-commit)
ruff lint + format, mypy, eslint, prettier, commitizen, openapi freshness check

### Every MR (GitLab CI)
lint → test (≥80% coverage) → typecheck → build → security (SAST + openapi freshness) → deploy

### Local
`mise run quality-gate` — mirrors CI exactly

---

## 11. Repo Master Integration

- Skill installed at `.claude/skills/repo-master/SKILL.md`
- Bootstrap: `invoke bootstrap repo master` → generates docs/repo-master-docs/
- MANIFEST.md: ≤50 lines, always current, enables instant GO/NO-GO/SUMMON
- All feature work requires MANIFEST.md entry before implementation
- Spec-first: specs/features/{feature}.md written before any code

---

## 12. Out of Scope (v1)

- Email / push notifications
- Public (external-facing) marketplace tier
- Skill dependency resolution
- Real-time collaboration
- Mobile native apps
- Billing / premium tiers
