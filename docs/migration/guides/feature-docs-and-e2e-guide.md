# Feature Documentation & E2E Test Audit — Agent-Executable Implementation Guide

**Project:** SkillHub Feature Documentation and Playwright E2E Maintenance
**Branch:** `migration/flask-port`
**Prerequisite:** Phase 5 complete (Flask is the sole backend, FastAPI removed)
**Outcome:** Complete `docs/features/index.md` covering all 10 feature categories; all 16 E2E spec files passing against Flask backend; GIF placeholder infrastructure ready
**Exit Gate:** `docs/features/index.md` has 10 numbered sections; `npx playwright test` passes with 0 failures; `docs/features/assets/` contains placeholder entries

---

## Conventions Used in This Guide

- **SEARCH** = read the referenced file to understand current implementation
- **CREATE** = write a new file
- **MODIFY** = edit an existing file
- **RUN** = execute a command
- **VERIFY** = run a command and check its output matches expectations

All file paths are relative to the repository root (`/Users/chase/wk/marketplace-ai`).

---

## Table of Contents

1. [Stage 1 — Populate docs/features/index.md](#stage-1)
2. [Stage 2 — Audit and Fix E2E Playwright Tests](#stage-2)
3. [Stage 3 — Feature Demo GIF Infrastructure](#stage-3)
4. [Quick Reference — Prompt Sequence](#quick-reference)

---

## Global Standards

Apply to every prompt. Non-negotiable.

```yaml
Documentation:
  - Markdown lint clean (no trailing spaces, consistent heading levels)
  - Every feature section uses the exact template from this guide
  - GIF references use relative paths from docs/features/
  - No placeholder text left in committed docs (except GIF images, which are recorded separately)

Testing:
  - TDD: write tests FIRST, then implementation for any new E2E specs
  - All existing tests must pass before adding new ones
  - Playwright tests run from: apps/web/apps/web/e2e/
  - Config: apps/web/apps/web/e2e/playwright.config.ts
  - Base URL: http://localhost:5173 (Vite dev server)
  - API URL: http://localhost:8000 (Flask backend)

Code Quality:
  - TypeScript: eslint, prettier, tsc --noEmit clean
  - No console.log() in test fixtures — use Playwright's built-in logging
  - No commented-out test code committed
```

---

## Reference Material

Before starting, the agent should read these files:

| File | Purpose |
|------|---------|
| `docs/leadership/skillhub-poc-feature-list.md` | Authoritative feature list with descriptions and status |
| `docs/features/index.md` | Target file (currently just a header) |
| `.claude/skills/feature-demo-recorder/SKILL.md` | GIF recording skill reference |
| `apps/web/apps/web/e2e/playwright.config.ts` | Playwright configuration |
| `apps/web/apps/web/e2e/fixtures/test-data.ts` | Shared test constants (users, categories, divisions) |
| `apps/web/apps/web/e2e/fixtures/auth.ts` | Auth fixture for authenticated tests |
| `apps/web/apps/web/e2e/fixtures/api.ts` | Direct API helper functions |

### E2E Test Inventory (16 spec files, 1294 lines)

| Category | Spec File | Lines |
|----------|-----------|-------|
| auth | `login-flow.spec.ts` | 112 |
| auth | `protected-routes.spec.ts` | 96 |
| discovery | `browse-skills.spec.ts` | 74 |
| discovery | `division-filtering.spec.ts` | 90 |
| discovery | `search-skills.spec.ts` | 70 |
| discovery | `skill-detail.spec.ts` | 76 |
| admin | `export-flow.spec.ts` | 81 |
| admin | `queue-review.spec.ts` | 87 |
| admin | `user-management.spec.ts` | 71 |
| admin | `feedback-mgmt.spec.ts` | 83 |
| admin | `roadmap-mgmt.spec.ts` | 101 |
| social | `comments.spec.ts` | 47 |
| social | `install-flow.spec.ts` | 73 |
| social | `ratings-reviews.spec.ts` | 88 |
| social | `favorites.spec.ts` | 42 |
| theme | `dark-light-toggle.spec.ts` | 103 |

All spec files live under `apps/web/apps/web/e2e/tests/`.

---

<a id="stage-1"></a>
## Stage 1 — Populate docs/features/index.md

### Overview

Populate `docs/features/index.md` with all 10 PoC feature categories. Each category gets a numbered section with a description, GIF placeholder, and key capabilities list. The authoritative source is `docs/leadership/skillhub-poc-feature-list.md`.

### Feature Entry Template

Every feature section must follow this exact format:

```markdown
## N. Feature Category Name

![Feature Category Name](assets/<slug>.gif)

2-3 sentence description of what the feature does and why it matters. Written in present tense, from the user's perspective.

**Key capabilities:**
- Capability 1 with brief detail
- Capability 2 with brief detail
- Capability N with brief detail
```

### Table of Contents Template

After the file header and before the first feature section, include a TOC:

```markdown
- [1. Skill Discovery & Search](#1-skill-discovery--search)
- [2. Quality Assurance Pipeline](#2-quality-assurance-pipeline)
...
```

---

### Prompt 1.1: Feature Docs — Skill Discovery & Search + Quality Assurance Pipeline

**Goal:** Write sections 1-2 in `docs/features/index.md` with TOC stub.

**Time estimate:** 15 minutes

#### Context

SEARCH `docs/leadership/skillhub-poc-feature-list.md` sections 1-2 for authoritative descriptions.
SEARCH `docs/features/index.md` to see current state (header + blockquote only).

#### Instructions

MODIFY `docs/features/index.md`:

1. Keep the existing header and blockquote.
2. Add the full TOC (all 10 entries) immediately after the blockquote. This gets written once and stays for all subsequent prompts.
3. Add section 1 — Skill Discovery & Search:
   - Slug: `skill-discovery`
   - Description: Browse skills across 9 categories, search by name/description/tags, filter by division, sort by trending/installs/rating/newest/updated. The marketplace provides instant discovery with a card-based UI that works in both dark and light themes.
   - Key capabilities (7 items): Marketplace browse with card-based UI, Full-text search with instant results, Multi-division filtering, 5 sort modes (Trending, Most Installed, Highest Rated, Newest, Recently Updated), Featured/verified skill badges, Pagination with load-more, Dark/light theme with system-matched toggle
4. Add section 2 — Quality Assurance Pipeline:
   - Slug: `quality-pipeline`
   - Description: Every skill passes through a 3-gate pipeline before publication. Gate 1 validates schema and checks for duplicates. Gate 2 runs an AI evaluation scoring quality, security, and usefulness. Gate 3 requires human review from the platform team. Approved skills are auto-published.
   - Key capabilities (5 items): Gate 1 automated validation (schema, required fields, Jaccard similarity > 0.7 duplicate detection), Gate 2 AI-assisted evaluation (LLM judge with 0-100 scoring, feature-flag controlled), Gate 3 human review (approve/request changes/reject with mandatory notes), Auto-publication on approval, 9-state pipeline with full audit trail

#### Acceptance Criteria

- [ ] `docs/features/index.md` contains TOC with 10 entries
- [ ] Section 1 heading is `## 1. Skill Discovery & Search`
- [ ] Section 1 has GIF reference `![Skill Discovery & Search](assets/skill-discovery.gif)`
- [ ] Section 1 has 7 key capabilities
- [ ] Section 2 heading is `## 2. Quality Assurance Pipeline`
- [ ] Section 2 has GIF reference `![Quality Assurance Pipeline](assets/quality-pipeline.gif)`
- [ ] Section 2 has 5 key capabilities
- [ ] No trailing whitespace, consistent heading levels

#### DO NOT

- Do NOT delete the existing header or blockquote
- Do NOT add content for sections 3-10 yet (only the TOC links)
- Do NOT create the GIF files (those are recorded separately via the feature-demo-recorder skill)

---

### Prompt 1.2: Feature Docs — Governance & Access Control + Collaboration & Community

**Goal:** Write sections 3-4 in `docs/features/index.md`.

**Time estimate:** 15 minutes

#### Context

SEARCH `docs/leadership/skillhub-poc-feature-list.md` sections 3-4.
SEARCH `docs/features/index.md` to see current state (should have sections 1-2 from Prompt 1.1).

#### Instructions

MODIFY `docs/features/index.md` — append after section 2:

1. Section 3 — Governance & Access Control:
   - Slug: `governance-access`
   - Description: Division-scoped permissions enforced server-side ensure skills are only visible to authorized divisions. Role-based admin access separates platform team and security team capabilities. Every action is logged to an append-only, tamper-proof audit log with DB trigger protection.
   - Key capabilities (7 items): Division-based server-enforced permissions, Role-based admin access (Platform Team vs Security Team), Append-only audit log (DB trigger blocks modification), Feature flags with per-division overrides, Skill moderation (feature/deprecate/remove), User management with role and division assignment, Cross-division access request workflow

2. Section 4 — Collaboration & Community:
   - Slug: `collaboration-community`
   - Description: Users rate, review, and discuss skills to surface quality organically. Favorites and following create personalized feeds. Forking preserves lineage while enabling division-specific customization.
   - Key capabilities (6 items): 1-5 star ratings with Bayesian average calculation, Written reviews with edit and helpful/unhelpful voting, Threaded comments with upvoting and soft-delete, Personal favorites collection, Follow skill authors for updates, Fork skills with lineage tracking

#### Acceptance Criteria

- [ ] Section 3 heading is `## 3. Governance & Access Control`
- [ ] Section 3 has GIF reference `![Governance & Access Control](assets/governance-access.gif)`
- [ ] Section 3 has 7 key capabilities
- [ ] Section 4 heading is `## 4. Collaboration & Community`
- [ ] Section 4 has GIF reference `![Collaboration & Community](assets/collaboration-community.gif)`
- [ ] Section 4 has 6 key capabilities

#### DO NOT

- Do NOT modify sections 1-2 or the TOC
- Do NOT add content for sections 5-10 yet

---

### Prompt 1.3: Feature Docs — Developer Integration + Operational Readiness + Authentication

**Goal:** Write sections 5-7 in `docs/features/index.md`.

**Time estimate:** 20 minutes

#### Context

SEARCH `docs/leadership/skillhub-poc-feature-list.md` sections 5-7.
SEARCH `docs/features/index.md` to see current state (should have sections 1-4).

#### Instructions

MODIFY `docs/features/index.md` — append after section 4:

1. Section 5 — Developer Integration (Claude Code Native):
   - Slug: `developer-integration`
   - Description: 9 MCP tools provide the complete skill lifecycle from inside Claude Code. Developers search, install, update, fork, and submit skills without leaving the AI assistant. This is the key differentiator — no commercial tool offers native Claude Code CLI integration via MCP.
   - Key capabilities (8 items): Search skills from Claude Code, One-command install with division access check, Clean uninstall with API tracking, Detect and update stale installed skills, List installed skills with staleness indicator, Fork skills directly from CLI, Submit SKILL.md for review without leaving editor, Check submission pipeline status from CLI

2. Section 6 — Operational Readiness:
   - Slug: `operational-readiness`
   - Description: The platform runs as a Docker Compose stack with single-command startup for all services plus observability. Alembic manages database migrations with rollback. 61 seed skills across all categories provide a realistic starting dataset. OpenTelemetry tracing flows through API and MCP server to Jaeger.
   - Key capabilities (6 items): Docker Compose single-command startup (5 services + observability), Alembic database migrations with rollback, 61 realistic seed skills across 9 categories and 8 divisions, OpenTelemetry distributed tracing with Jaeger UI, 634+ automated tests (550 API / 84 MCP) with TDD enforcement, Canonical design system (tokens.json / style guide / component inventory)

3. Section 7 — Authentication:
   - Slug: `authentication`
   - Description: Development authentication provides 6 persona users across divisions with JWT tokens for the full user journey. Cryptographic JWT verification protects all endpoints. The auth architecture is designed for SSO integration — database model, JWT claim structure, and OAuth session table are in place.
   - Key capabilities (3 items): 6 dev persona users across 4 divisions (Engineering, Product, Data, Security), Cryptographic JWT verification on all protected endpoints, OAuth/SSO integration ready (Microsoft, Google, Okta, GitHub, Generic OIDC stubs)

#### Acceptance Criteria

- [ ] Section 5 has 8 key capabilities and GIF reference `![Developer Integration](assets/developer-integration.gif)`
- [ ] Section 6 has 6 key capabilities and GIF reference `![Operational Readiness](assets/operational-readiness.gif)`
- [ ] Section 7 has 3 key capabilities and GIF reference `![Authentication](assets/authentication.gif)`
- [ ] Sections are numbered 5, 6, 7 with correct headings

#### DO NOT

- Do NOT modify sections 1-4 or the TOC
- Do NOT add content for sections 8-10 yet

---

### Prompt 1.4: Feature Docs — Phase 6 Features (Admin HITL, Docs Portal, Submission UI)

**Goal:** Write sections 8-10 in `docs/features/index.md` for Phase 6 features currently being built.

**Time estimate:** 20 minutes

#### Context

SEARCH `docs/migration/guides/phase6-post-migration-guide.md` for Phase 6 feature details.
SEARCH `docs/features/index.md` to see current state (should have sections 1-7).

These features are in-progress. Mark them clearly with a status indicator.

#### Instructions

MODIFY `docs/features/index.md` — append after section 7:

1. Section 8 — Admin HITL Queue Enhancements:
   - Slug: `admin-hitl-enhancements`
   - Description: Enhanced human-in-the-loop review queue with revision tracking, change request flags, and rejection reasons. Reviewers can compare submission versions side-by-side and see the full audit log panel inline. Builds on the Gate 3 pipeline from Section 2.
   - Key capabilities (5 items): Revision tracking with diff view, Change request flags with structured reasons, Rejection reasons with mandatory notes, Inline audit log panel, Version selector with side-by-side comparison
   - Add status badge: `**Status: In Progress (Phase 6A)**`

2. Section 9 — User Documentation Portal:
   - Slug: `docs-portal`
   - Description: VitePress-powered documentation site for end-user guides, API reference, and skill authoring tutorials. Deployed alongside the main app with search and versioning.
   - Key capabilities (4 items): VitePress static site with full-text search, User guides for skill discovery and installation, API reference documentation, Skill authoring and submission tutorials
   - Add status badge: `**Status: Planned (Phase 6B)**`

3. Section 10 — User Skill Submission UI:
   - Slug: `skill-submission-ui`
   - Description: Browser-based skill submission with three input modes: form builder, SKILL.md file upload, and MCP-assisted drafting. Live LLM hints provide real-time feedback on submission quality before entering the review pipeline.
   - Key capabilities (5 items): Form-based skill builder with guided fields, SKILL.md file upload with validation, MCP-assisted drafting mode, Live LLM quality hints during authoring, Direct pipeline integration (submitted skills enter Gate 1 automatically)
   - Add status badge: `**Status: Planned (Phase 6C)**`

#### Acceptance Criteria

- [ ] Section 8 has `**Status: In Progress (Phase 6A)**` badge
- [ ] Section 9 has `**Status: Planned (Phase 6B)**` badge
- [ ] Section 10 has `**Status: Planned (Phase 6C)**` badge
- [ ] All 10 sections present in the file
- [ ] TOC links match all 10 section headings
- [ ] `grep -c "^## " docs/features/index.md` returns `10`

#### DO NOT

- Do NOT modify sections 1-7
- Do NOT create GIF files for in-progress features
- Do NOT add speculative implementation details beyond what is in the Phase 6 guide

---

<a id="stage-2"></a>
## Stage 2 — Audit and Fix E2E Playwright Tests

### Overview

The 16 Playwright E2E spec files were written when the backend was FastAPI. The Flask migration preserved the same API routes, response shapes, and auth flow. Most tests should pass without changes. This stage audits every spec file, identifies any Flask-specific incompatibilities, and fixes them.

### Key Flask vs FastAPI Differences for E2E

| Concern | FastAPI | Flask | E2E Impact |
|---------|---------|-------|------------|
| API base URL | `http://localhost:8000` | `http://localhost:8000` | None — same port |
| Auth endpoint | `POST /auth/token` | `POST /auth/token` | None — same route |
| Error format | `{"detail": "..."}` | `{"description": "..."}` via `abort()` | **Check any tests that assert on error response body** |
| 422 Validation | FastAPI auto-422 with `{"detail": [...]}` | Flask returns 400 with `{"error": "..."}` | **Check any tests that expect 422 status** |
| Content-Type | `application/json` | `application/json` | None |
| Response shape | Pydantic `.model_dump()` | Same Pydantic `.model_dump()` | None |
| CORS | FastAPI middleware | Flask-CORS | None — same headers |

### Nested Path Note

The E2E tests live at a nested path: `apps/web/apps/web/e2e/`. This is the actual test root. The Playwright config is at `apps/web/apps/web/e2e/playwright.config.ts` with `testDir: './tests'`. All Playwright commands must be run from `apps/web/apps/web/e2e/` or with the `--config` flag pointing there.

---

### Prompt 2.1: Audit Discovery & Auth Spec Files (6 files)

**Goal:** Read all 6 discovery + auth spec files, identify Flask incompatibilities, fix them.

**Time estimate:** 25 minutes

#### Prerequisites

Both servers must be running:
```bash
# Terminal 1: Flask API
mise run dev:api

# Terminal 2: Vite dev server
mise run dev:web
```

VERIFY servers are up:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/skills
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173
```

#### Instructions

1. SEARCH all 6 files:
   - `apps/web/apps/web/e2e/tests/auth/login-flow.spec.ts`
   - `apps/web/apps/web/e2e/tests/auth/protected-routes.spec.ts`
   - `apps/web/apps/web/e2e/tests/discovery/browse-skills.spec.ts`
   - `apps/web/apps/web/e2e/tests/discovery/division-filtering.spec.ts`
   - `apps/web/apps/web/e2e/tests/discovery/search-skills.spec.ts`
   - `apps/web/apps/web/e2e/tests/discovery/skill-detail.spec.ts`

2. For each file, check for these Flask-incompatible patterns:
   - **Status 422 assertions:** Flask does not return 422 for validation errors. Change to 400.
   - **Error body `{"detail": ...}`:** Flask uses `{"description": ..."}` from `abort()`. Check if any test asserts on the `detail` key in error responses.
   - **FastAPI-specific URL patterns:** Any test hitting `/docs`, `/openapi.json`, or `/redoc` will fail. Remove or skip those.
   - **Query parameter array format:** FastAPI accepts `?divisions=a&divisions=b`. Flask blueprint uses the same pattern via `request.args.getlist()`. Should be fine but verify.

3. For each incompatibility found:
   - MODIFY the spec file with the fix.
   - Add a comment `// Flask migration: <what changed>` on the changed line.

4. RUN the affected tests:
   ```bash
   cd apps/web/apps/web/e2e && npx playwright test tests/auth/ tests/discovery/ --reporter=list
   ```

5. If any test fails for a reason unrelated to Flask (e.g., UI change, timing), fix it separately and note the root cause.

#### Acceptance Criteria

- [ ] All 6 spec files reviewed
- [ ] Any `422` status assertions changed to `400` with comment
- [ ] Any `detail` key assertions changed to `description` with comment
- [ ] `npx playwright test tests/auth/ tests/discovery/` passes with 0 failures
- [ ] No changes made to files that were already Flask-compatible (do not modify working code)

#### DO NOT

- Do NOT rewrite tests that are already passing
- Do NOT change the test structure or fixtures
- Do NOT add new tests in this prompt (that comes later)

---

### Prompt 2.2: Audit Admin Spec Files (5 files)

**Goal:** Read all 5 admin spec files, identify Flask incompatibilities, fix them.

**Time estimate:** 25 minutes

#### Prerequisites

Servers running (same as 2.1). User `alice` must be available as admin persona.

#### Instructions

1. SEARCH all 5 files:
   - `apps/web/apps/web/e2e/tests/admin/export-flow.spec.ts`
   - `apps/web/apps/web/e2e/tests/admin/queue-review.spec.ts`
   - `apps/web/apps/web/e2e/tests/admin/user-management.spec.ts`
   - `apps/web/apps/web/e2e/tests/admin/feedback-mgmt.spec.ts`
   - `apps/web/apps/web/e2e/tests/admin/roadmap-mgmt.spec.ts`

2. Apply the same Flask compatibility checks from Prompt 2.1:
   - Status 422 -> 400
   - `detail` -> `description` in error assertions
   - FastAPI-specific endpoints
   - Admin-specific: check if any test calls admin endpoints that changed URL structure in Flask (all admin routes should be under `/api/v1/admin/` in both — verify)

3. Admin tests typically require authenticated admin user. Verify the auth fixture works:
   - The `loginAs('alice')` fixture calls the UI login flow
   - The `getToken('alice')` fixture calls `POST /auth/token` directly
   - Both should work against Flask without changes

4. MODIFY any incompatible assertions. Tag with `// Flask migration: <what changed>`.

5. RUN:
   ```bash
   cd apps/web/apps/web/e2e && npx playwright test tests/admin/ --reporter=list
   ```

#### Acceptance Criteria

- [ ] All 5 admin spec files reviewed
- [ ] Flask incompatibilities fixed with migration comments
- [ ] `npx playwright test tests/admin/` passes with 0 failures

#### DO NOT

- Do NOT change admin authorization logic in tests
- Do NOT modify the auth fixtures

---

### Prompt 2.3: Audit Social & Theme Spec Files (5 files)

**Goal:** Read all 5 social + theme spec files, identify Flask incompatibilities, fix them.

**Time estimate:** 20 minutes

#### Instructions

1. SEARCH all 5 files:
   - `apps/web/apps/web/e2e/tests/social/comments.spec.ts`
   - `apps/web/apps/web/e2e/tests/social/install-flow.spec.ts`
   - `apps/web/apps/web/e2e/tests/social/ratings-reviews.spec.ts`
   - `apps/web/apps/web/e2e/tests/social/favorites.spec.ts`
   - `apps/web/apps/web/e2e/tests/theme/dark-light-toggle.spec.ts`

2. Apply the same Flask compatibility checks.

3. Social tests may make direct API calls via the `apiPost`/`apiGet`/`apiDelete` helpers in `apps/web/apps/web/e2e/fixtures/api.ts`. These hit `http://localhost:8000` directly. Verify:
   - The API helper base URL matches Flask (`API_BASE = 'http://localhost:8000'` in test-data.ts — already correct)
   - Response shapes from social endpoints (ratings, comments, favorites) match between Flask and FastAPI

4. Theme tests should be entirely frontend — no API dependency. These should pass without changes.

5. MODIFY any incompatible assertions. Tag with `// Flask migration: <what changed>`.

6. RUN:
   ```bash
   cd apps/web/apps/web/e2e && npx playwright test tests/social/ tests/theme/ --reporter=list
   ```

#### Acceptance Criteria

- [ ] All 5 spec files reviewed
- [ ] Flask incompatibilities fixed with migration comments
- [ ] `npx playwright test tests/social/ tests/theme/` passes with 0 failures

#### DO NOT

- Do NOT modify the theme toggle implementation
- Do NOT change social endpoint URLs unless they actually differ in Flask

---

### Prompt 2.4: Full Suite Run and Regression Report

**Goal:** Run the complete E2E suite, produce a pass/fail report, fix any remaining failures.

**Time estimate:** 15 minutes

#### Prerequisites

Both servers running. Database seeded (`mise run db:seed`).

#### Instructions

1. RUN the full suite:
   ```bash
   cd apps/web/apps/web/e2e && npx playwright test --reporter=list 2>&1 | tee /tmp/e2e-full-run.txt
   ```

2. Parse the output:
   - Count total tests, passed, failed, skipped
   - For each failure: note the spec file, test name, and error message

3. If failures remain:
   - SEARCH the failing spec file
   - Determine if the failure is Flask-related, UI-related, or a flaky test
   - Fix Flask-related and UI-related failures
   - Mark genuinely flaky tests with `test.fixme()` and a comment explaining why

4. Re-run until 0 failures (excluding `fixme`-marked tests).

5. CREATE a summary file `docs/migration/e2e-audit-report.md` with:
   ```markdown
   # E2E Test Audit Report — Flask Migration

   **Date:** <today>
   **Branch:** migration/flask-port
   **Total specs:** 16
   **Total tests:** <count>
   **Passed:** <count>
   **Failed:** 0
   **Skipped/fixme:** <count with reasons>

   ## Changes Made
   | File | Change | Reason |
   |------|--------|--------|
   | ... | ... | ... |

   ## Flask Compatibility Notes
   - <any general notes about Flask vs FastAPI E2E behavior>
   ```

#### Acceptance Criteria

- [ ] `npx playwright test` exits with code 0
- [ ] `docs/migration/e2e-audit-report.md` exists with accurate counts
- [ ] Every change made in Stage 2 is tagged with `// Flask migration:` comment
- [ ] No tests silently skipped without documentation

#### DO NOT

- Do NOT mark passing tests as fixme
- Do NOT delete failing tests — fix them or mark fixme with explanation
- Do NOT commit test artifacts (screenshots, traces) to the repo

---

<a id="stage-3"></a>
## Stage 3 — Feature Demo GIF Infrastructure

### Overview

Set up the placeholder infrastructure for GIF recordings. The actual recordings require live servers and the `feature-demo-recorder` skill running interactively. This stage creates the directory structure and documents the recording process.

---

### Prompt 3.1: Create Asset Directory and Recording Guide

**Goal:** Create `docs/features/assets/` directory and a recording instructions file.

**Time estimate:** 10 minutes

#### Instructions

1. CREATE directory:
   ```bash
   mkdir -p docs/features/assets
   ```

2. CREATE `docs/features/assets/.gitkeep` (empty file to ensure directory is tracked).

3. CREATE `docs/features/RECORDING.md`:

   ```markdown
   # Feature Demo Recording Guide

   Feature demos are recorded as GIFs using the `feature-demo-recorder` skill.

   ## Prerequisites

   - Flask API running: `mise run dev:api`
   - Vite dev server running: `mise run dev:web`
   - Database seeded: `mise run db:seed`
   - ffmpeg installed: `brew install ffmpeg`

   ## Recording a Demo

   Use Claude Code with the trigger phrase:

   ```
   Demo and Document <Feature Name>
   ```

   This invokes the `feature-demo-recorder` skill which:
   1. Drives the browser via Playwright MCP tools
   2. Records the interaction as video
   3. Converts to optimized GIF (100MB limit with step-down fallback)
   4. Updates `docs/features/index.md` with the GIF reference

   ## Feature Slugs

   | Feature | Slug | Filename |
   |---------|------|----------|
   | Skill Discovery & Search | skill-discovery | skill-discovery.gif |
   | Quality Assurance Pipeline | quality-pipeline | quality-pipeline.gif |
   | Governance & Access Control | governance-access | governance-access.gif |
   | Collaboration & Community | collaboration-community | collaboration-community.gif |
   | Developer Integration | developer-integration | developer-integration.gif |
   | Operational Readiness | operational-readiness | operational-readiness.gif |
   | Authentication | authentication | authentication.gif |
   | Admin HITL Queue Enhancements | admin-hitl-enhancements | admin-hitl-enhancements.gif |
   | User Documentation Portal | docs-portal | docs-portal.gif |
   | User Skill Submission UI | skill-submission-ui | skill-submission-ui.gif |

   ## Recording Order (Recommended)

   Record in this order — each demo builds on the previous context:

   1. Authentication (shows login, sets up context)
   2. Skill Discovery & Search (browse/search after login)
   3. Collaboration & Community (rate/review/fork from discovery)
   4. Developer Integration (requires MCP server running too)
   5. Quality Assurance Pipeline (submit + walk through gates)
   6. Governance & Access Control (admin actions)
   7. Operational Readiness (Docker/infra — may need terminal recording instead)
   8-10. Phase 6 features (record as they are completed)
   ```

#### Acceptance Criteria

- [ ] `docs/features/assets/.gitkeep` exists
- [ ] `docs/features/RECORDING.md` exists with slug table and recording order
- [ ] `git status` shows the new files as untracked

#### DO NOT

- Do NOT create placeholder GIF files (they will be recorded live)
- Do NOT modify `docs/features/index.md` in this prompt

---

### Prompt 3.2: Add New E2E Tests for Phase 6 Features (Template)

**Goal:** Create stub test files for Phase 6 features so they are ready when the features are built.

**Time estimate:** 15 minutes

#### Context

Phase 6 features (Admin HITL Enhancements, Docs Portal, Submission UI) are being built. The E2E tests should be created as stubs now so they can be filled in as features land. This follows TDD — the test files exist before the implementation.

#### Instructions

1. CREATE `apps/web/apps/web/e2e/tests/admin/hitl-enhancements.spec.ts`:
   ```typescript
   import { test, expect } from '../../fixtures/auth';

   test.describe('Admin HITL Queue Enhancements', () => {
     test.fixme('displays revision history for a submission', async ({ page, loginAs }) => {
       // Phase 6A: revision tracking
     });

     test.fixme('shows change request flags on submissions', async ({ page, loginAs }) => {
       // Phase 6A: change request flags
     });

     test.fixme('displays rejection reasons', async ({ page, loginAs }) => {
       // Phase 6A: rejection reasons
     });

     test.fixme('shows inline audit log panel', async ({ page, loginAs }) => {
       // Phase 6A: audit log panel
     });

     test.fixme('allows version comparison via selector', async ({ page, loginAs }) => {
       // Phase 6A: version selector
     });
   });
   ```

2. CREATE `apps/web/apps/web/e2e/tests/submission/skill-submission.spec.ts`:
   ```typescript
   import { test, expect } from '../../fixtures/auth';

   test.describe('User Skill Submission UI', () => {
     test.fixme('submits a skill via form builder', async ({ page, loginAs }) => {
       // Phase 6C: form-based submission
     });

     test.fixme('submits a skill via SKILL.md upload', async ({ page, loginAs }) => {
       // Phase 6C: file upload mode
     });

     test.fixme('shows live LLM quality hints during authoring', async ({ page, loginAs }) => {
       // Phase 6C: LLM hint integration
     });

     test.fixme('submitted skill enters Gate 1 automatically', async ({ page, loginAs }) => {
       // Phase 6C: pipeline integration
     });
   });
   ```

3. Ensure the new test directory exists:
   ```bash
   mkdir -p apps/web/apps/web/e2e/tests/submission
   ```

4. RUN to verify stubs are recognized:
   ```bash
   cd apps/web/apps/web/e2e && npx playwright test --list 2>&1 | tail -20
   ```

#### Acceptance Criteria

- [ ] `hitl-enhancements.spec.ts` exists with 5 `test.fixme()` stubs
- [ ] `skill-submission.spec.ts` exists with 4 `test.fixme()` stubs
- [ ] `npx playwright test --list` shows the new test files
- [ ] `npx playwright test` still passes (fixme tests are skipped, not failed)
- [ ] New test count: 116 existing + 9 stubs = 125 total recognized

#### DO NOT

- Do NOT create stubs for the VitePress docs portal (that is a separate app, not E2E-testable via the main Playwright config)
- Do NOT implement any test bodies — these are stubs only
- Do NOT modify existing test files

---

<a id="quick-reference"></a>
## Quick Reference — Prompt Sequence

| # | Prompt | Stage | Time | Output |
|---|--------|-------|------|--------|
| 1.1 | Discovery + Quality Pipeline docs | 1 | 15 min | Sections 1-2 + full TOC in index.md |
| 1.2 | Governance + Community docs | 1 | 15 min | Sections 3-4 in index.md |
| 1.3 | DevInt + Ops + Auth docs | 1 | 20 min | Sections 5-7 in index.md |
| 1.4 | Phase 6 feature docs | 1 | 20 min | Sections 8-10 in index.md |
| 2.1 | Audit discovery + auth E2E | 2 | 25 min | 6 spec files Flask-compatible |
| 2.2 | Audit admin E2E | 2 | 25 min | 5 spec files Flask-compatible |
| 2.3 | Audit social + theme E2E | 2 | 20 min | 5 spec files Flask-compatible |
| 2.4 | Full suite run + report | 2 | 15 min | 0 failures, audit report |
| 3.1 | Asset directory + recording guide | 3 | 10 min | docs/features/assets/ + RECORDING.md |
| 3.2 | Phase 6 E2E stubs | 3 | 15 min | 2 new spec files, 9 test stubs |

**Total: 10 prompts, ~180 minutes**

### Execution Order

Stages can be executed in parallel by separate agents:
- **Stage 1** (Prompts 1.1-1.4) is documentation-only — no code dependencies
- **Stage 2** (Prompts 2.1-2.4) requires running servers — must be sequential
- **Stage 3** (Prompts 3.1-3.2) is file creation — no dependencies on Stage 1 or 2

Within each stage, prompts must be sequential.

### Verification Commands

```bash
# Stage 1: Check all 10 sections exist
grep -c "^## " docs/features/index.md
# Expected: 10

# Stage 2: Full E2E pass
cd apps/web/apps/web/e2e && npx playwright test --reporter=list
# Expected: 0 failures

# Stage 3: Asset directory exists
ls docs/features/assets/.gitkeep docs/features/RECORDING.md
# Expected: both files exist

# Stage 3: New stubs recognized
cd apps/web/apps/web/e2e && npx playwright test --list | wc -l
# Expected: >= 125
```
