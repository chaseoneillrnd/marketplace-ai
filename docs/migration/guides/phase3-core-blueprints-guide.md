# Phase 3: Core Domain Blueprints — Agent-Executable Implementation Guide

**Phase:** 3 of 5
**Prerequisite:** Phase 2 complete (auth working, async converted, cache sync)
**Outcome:** All 7 core domain blueprints ported from FastAPI routers to Flask blueprints
**Exit Gate:** Service tests green, security gate Classes 1-5/7/8 green, coverage >= 80%

---

## Conventions Used in This Guide

- **SEARCH** = read the referenced file to understand current implementation
- **CREATE** = write a new file
- **MODIFY** = edit an existing file
- **TEST RED** = run tests and confirm they fail (TDD red phase)
- **TEST GREEN** = run tests and confirm they pass (TDD green phase)
- **VERIFY** = run a command and check its output matches expectations

All file paths are relative to the repository root (`/Users/chase/wk/marketplace-ai`).

### Pattern Translation Reference

Every prompt in this phase applies the same mechanical translation. Memorize this table:

| FastAPI | Flask |
|---------|-------|
| `db: Annotated[Session, Depends(get_db)]` | `db = get_db()` (from `current_app.extensions["db"]()`) |
| `current_user: Annotated[dict, Depends(get_current_user)]` | `g.current_user` (set by `before_request`) |
| `_current_user: Annotated[dict, Depends(require_platform_team)]` | `g.current_user` (admin `before_request` already enforced) |
| `settings: Settings = Depends(get_settings)` | `current_app.extensions["settings"]` |
| `Query(ge=1, default=1)` | `validated_query(QueryParamsModel)` decorator |
| `response_model=Schema` | `Schema(**data).model_dump(mode="json")` + `jsonify()` |
| `HTTPException(status_code=403, detail=...)` | `abort(403, description=...)` or raise `DivisionRestrictedError` |
| `BackgroundTasks.add_task(fn, args)` | `Thread(target=fn, args=args, daemon=True).start()` |
| `TestClient(app)` | `app.test_client()` |
| `dependency_overrides[get_db] = lambda: mock_db` | `create_app(session_factory=lambda: mock_db)` |

### Blueprint File Template

Every blueprint file follows this skeleton:

```python
"""<Domain> endpoints — Flask blueprint."""
from __future__ import annotations

import logging
from flask import Blueprint, g, jsonify, abort, current_app
from skillhub.validation import validated_body, validated_query

logger = logging.getLogger(__name__)

bp = Blueprint("<name>", __name__)


def get_db():
    return current_app.extensions["db"]()


# Route definitions follow...
```

### Test File Template

Every test file follows this skeleton:

```python
"""Tests for <Domain> blueprint."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest

from tests.conftest_flask import create_test_app, make_token


@pytest.fixture()
def app():
    mock_db = MagicMock()
    return create_test_app(session_factory=lambda: mock_db)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers():
    token = make_token()
    return {"Authorization": f"Bearer {token}"}
```

### PUBLIC_ENDPOINTS Pattern

Public endpoints must be added to the `PUBLIC_ENDPOINTS` frozenset in the auth module. The frozenset uses `"blueprint_name.view_function_name"` strings. Every prompt that adds public endpoints must update this frozenset.

---

## Prompt 1: Skills Blueprint

### Context

Port `apps/api/skillhub/routers/skills.py` (6 route handlers) to a Flask blueprint. This is the largest public-facing surface: browse, categories, detail (with background view count), and version endpoints.

### Prerequisites

- SEARCH `apps/api/skillhub/routers/skills.py` — the FastAPI router being ported
- SEARCH `apps/api/tests/test_skills_router.py` — the FastAPI test file being ported
- SEARCH `apps/api/tests/test_skills_browse_comprehensive.py` — comprehensive browse tests
- SEARCH `apps/api/skillhub/schemas/skill.py` — Pydantic schemas (unchanged, reuse as-is)
- SEARCH `apps/api/skillhub/services/skills.py` — service layer (unchanged)

### Step 1: Create the query params model

CREATE `apps/api/skillhub/schemas/skill_query.py`:

```python
"""Query parameter models for skills endpoints."""
from __future__ import annotations
from pydantic import BaseModel, Field
from skillhub.schemas.skill import SortOption


class SkillsQueryParams(BaseModel):
    q: str | None = None
    category: str | None = None
    divisions: list[str] = []
    sort: SortOption = SortOption.TRENDING
    install_method: str | None = None
    verified: bool | None = None
    featured: bool | None = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
```

### Step 2: Create the skills blueprint

CREATE `apps/api/skillhub/blueprints/skills.py`:

Port each route from `routers/skills.py` following these translations:

1. **GET /api/v1/skills** (public, paginated, filtered)
   - Use `@validated_query(SkillsQueryParams)` decorator
   - Call `browse_skills(db, ...)` with query params
   - Return `jsonify(SkillBrowseResponse(...).model_dump(mode="json"))`

2. **GET /api/v1/skills/categories** (public)
   - Direct DB query on Category model
   - Return `jsonify([...])` list of dicts

3. **GET /api/v1/skills/{slug}** (public, background view count)
   - Call `get_skill_detail(db, slug, current_user_id=...)`
   - Background view count: use `threading.Thread` with a fresh `SessionLocal()` session
   - The thread function must create its own session, call `increment_view_count()`, then close the session in a `finally` block
   - Optional user extraction: check `g.get("current_user")` — may be None for public endpoint

4. **GET /api/v1/skills/{slug}/versions** (auth required)
   - `g.current_user` guaranteed by `before_request`
   - Direct DB queries unchanged

5. **GET /api/v1/skills/{slug}/versions/latest** (auth required)
   - Same pattern as versions list

6. **GET /api/v1/skills/{slug}/versions/{version}** (auth required)
   - Same pattern, with "latest" alias resolution

### Step 3: Register public endpoints

MODIFY `apps/api/skillhub/auth.py` (or wherever `PUBLIC_ENDPOINTS` is defined):

Add these entries to the `PUBLIC_ENDPOINTS` frozenset:
- `"skills.list_skills"`
- `"skills.list_categories"`
- `"skills.get_skill"`

### Step 4: Register the blueprint

MODIFY `apps/api/skillhub/app.py` (or the app factory):

```python
from skillhub.blueprints.skills import bp as skills_bp
app.register_blueprint(skills_bp)
```

### Step 5: Write tests (RED phase)

CREATE `apps/api/tests/test_skills_blueprint.py`:

Port all tests from `test_skills_router.py`, translating:
- `TestClient(app)` to `app.test_client()`
- `dependency_overrides[get_db]` to `create_test_app(session_factory=...)`
- `client.get(url)` stays the same (Flask test client has same API)
- Response assertions stay the same (`.status_code`, `.json`)

Test cases to port:
- Browse skills returns paginated results with correct shape
- Browse skills with filters (q, category, divisions, sort, verified, featured)
- Browse skills with invalid page returns 422
- Categories endpoint returns list
- Skill detail returns full detail dict
- Skill detail returns 404 for missing slug
- Skill detail increments view count in background
- Versions list requires auth (401 without token)
- Versions list returns versions for valid skill
- Latest version endpoint returns correct version
- Specific version endpoint returns correct version
- "latest" alias resolves to current_version

Also port relevant tests from `test_skills_browse_comprehensive.py`.

### Step 6: Implement until GREEN

TEST RED — run `pytest apps/api/tests/test_skills_blueprint.py` and confirm failures.

Implement the blueprint until all tests pass.

TEST GREEN — run `pytest apps/api/tests/test_skills_blueprint.py` and confirm all pass.

### Step 7: Security gate

VERIFY:
```bash
pytest apps/api/tests/test_security_migration_gate.py -v
```

Confirm skills endpoints appear in security gate results and pass Classes 1-5.

### Completion Criteria

- [ ] 6 route handlers in `blueprints/skills.py`
- [ ] 3 public endpoints added to `PUBLIC_ENDPOINTS`
- [ ] Background view count uses `threading.Thread` with fresh session
- [ ] All tests from `test_skills_router.py` ported and green
- [ ] All tests from `test_skills_browse_comprehensive.py` ported and green
- [ ] Security gate green for skills endpoints

---

## Prompt 2: Users Blueprint

### Context

Port `apps/api/skillhub/routers/users.py` (5 route handlers) to a Flask blueprint. All endpoints require authentication and return paginated collections.

### Prerequisites

- SEARCH `apps/api/skillhub/routers/users.py` — the FastAPI router
- SEARCH `apps/api/tests/test_users_router.py` — the test file
- SEARCH `apps/api/skillhub/schemas/user.py` — Pydantic schemas
- SEARCH `apps/api/skillhub/services/users.py` — service layer

### Step 1: Create the users blueprint

CREATE `apps/api/skillhub/blueprints/users.py`:

Port each route:

1. **GET /api/v1/users/me** (auth)
   - `g.current_user` provides user dict
   - Call `get_user_profile(db, g.current_user)`
   - Return `jsonify(UserProfile(**profile).model_dump(mode="json"))`

2. **GET /api/v1/users/me/installs** (auth, paginated)
   - Use `@validated_query(InstallsQueryParams)` for `include_uninstalled`, `page`, `per_page`
   - Call `get_user_installs(db, user_id, ...)`
   - Return paginated response

3. **GET /api/v1/users/me/favorites** (auth, paginated)
   - Use `@validated_query(PaginationParams)`
   - Call `get_user_favorites(db, user_id, ...)`

4. **GET /api/v1/users/me/forks** (auth, paginated)
   - Same pattern as favorites

5. **GET /api/v1/users/me/submissions** (auth, paginated)
   - Call `get_user_submissions(db, user_id, ...)`
   - Return `UserSubmissionsResponse`

### Step 2: Create query params model

CREATE or MODIFY `apps/api/skillhub/schemas/user_query.py`:

```python
class InstallsQueryParams(BaseModel):
    include_uninstalled: bool = False
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
```

Reuse `PaginationParams` from `skill_query.py` for the other three endpoints.

### Step 3: Register the blueprint

MODIFY app factory to register `users_bp`.

No public endpoints — all require auth. Do NOT add to `PUBLIC_ENDPOINTS`.

### Step 4: Write tests (RED phase)

CREATE `apps/api/tests/test_users_blueprint.py`:

Port all tests from `test_users_router.py`:
- `/me` returns user profile with stats
- `/me` returns 401 without token
- `/me/installs` returns paginated installs
- `/me/installs?include_uninstalled=true` includes uninstalled
- `/me/favorites` returns paginated favorites
- `/me/forks` returns paginated forks
- `/me/submissions` returns paginated submissions with status

### Step 5: Implement until GREEN

TEST RED then TEST GREEN.

### Completion Criteria

- [ ] 5 route handlers in `blueprints/users.py`
- [ ] No public endpoints (all auth-required)
- [ ] All tests from `test_users_router.py` ported and green
- [ ] Security gate green for users endpoints

---

## Prompt 3: Social Blueprint

### Context

Port `apps/api/skillhub/routers/social.py` (16 route decorators) to a Flask blueprint. This is the most complex blueprint by route count. Covers install, favorite, fork, follow, reviews, and comments.

### Prerequisites

- SEARCH `apps/api/skillhub/routers/social.py` — all 16 route handlers
- SEARCH `apps/api/tests/test_social_router.py` — router tests
- SEARCH `apps/api/tests/test_social_comprehensive.py` — comprehensive tests
- SEARCH `apps/api/skillhub/schemas/social.py` — all social schemas
- SEARCH `apps/api/skillhub/services/social.py` — install/favorite/fork/follow services
- SEARCH `apps/api/skillhub/services/reviews.py` — review/comment services

### Step 1: Create the social blueprint

CREATE `apps/api/skillhub/blueprints/social.py`:

All routes live under `/api/v1/skills/<slug>/...`. All require auth. Group by domain:

**Install (2 routes):**
1. **POST /{slug}/install** — 201 on success
   - Use `@validated_body(InstallRequest)`
   - Call `install_skill(db, slug, user_id, user_division, body.method, body.version)`
   - Catch `ValueError` -> 404, `PermissionError` -> 403 with `DivisionRestrictedError` response
   - The 403 response body must be `{"error": "division_restricted"}` (dict detail, not string)
2. **DELETE /{slug}/install** — 204 on success
   - Call `uninstall_skill(db, slug, user_id)`

**Favorite (2 routes):**
3. **POST /{slug}/favorite** — 200 (idempotent upsert)
   - Call `favorite_skill(db, slug, user_id)`
4. **DELETE /{slug}/favorite** — 204

**Fork (1 route):**
5. **POST /{slug}/fork** — 201

**Follow (2 routes):**
6. **POST /{slug}/follow** — 200 (idempotent)
7. **DELETE /{slug}/follow** — 204

**Reviews (4 routes):**
8. **GET /{slug}/reviews** — paginated, use `@validated_query(PaginationParams)`
9. **POST /{slug}/reviews** — 201, catch `DuplicateReviewError` -> 409
10. **PATCH /{slug}/reviews/{review_id}** — owner only, catch `PermissionError` -> 403
11. **POST /{slug}/reviews/{review_id}/vote** — 204

**Comments (5 routes):**
12. **GET /{slug}/comments** — paginated
13. **POST /{slug}/comments** — 201
14. **DELETE /{slug}/comments/{comment_id}** — 200 (soft delete, returns updated comment)
15. **POST /{slug}/comments/{comment_id}/replies** — 201
16. **POST /{slug}/comments/{comment_id}/vote** — 204

### Step 2: Handle DivisionRestrictedError

The install endpoint's 403 response uses a dict detail `{"error": "division_restricted"}`, not a string. In Flask, implement this as:

```python
class DivisionRestrictedError(Exception):
    """Raised when a user's division is not authorized for a skill."""
    pass

# In the route handler:
except PermissionError:
    return jsonify({"detail": {"error": "division_restricted"}}), 403
```

Or if `DivisionRestrictedError` is already defined (check `apps/api/skillhub/errors.py`), use the existing one with a registered error handler.

### Step 3: Register the blueprint

MODIFY app factory. No public endpoints.

### Step 4: Write tests (RED phase)

CREATE `apps/api/tests/test_social_blueprint.py`:

Port all tests from `test_social_router.py` and `test_social_comprehensive.py`:
- Install creates record and returns 201
- Install with wrong division returns 403 with `{"error": "division_restricted"}`
- Install nonexistent skill returns 404
- Uninstall returns 204
- Favorite returns 200 (idempotent)
- Unfavorite returns 204
- Fork returns 201
- Follow returns 200 (idempotent)
- Unfollow returns 204
- Reviews list returns paginated results
- Create review returns 201
- Duplicate review returns 409
- Update review by non-owner returns 403
- Review vote returns 204
- Comments list returns paginated results with nested replies
- Create comment returns 201
- Delete comment by owner returns 200
- Delete comment by non-owner non-admin returns 403
- Reply to comment returns 201
- Comment vote returns 204

### Step 5: Implement until GREEN

TEST RED then TEST GREEN.

### Completion Criteria

- [ ] 16 route handlers in `blueprints/social.py`
- [ ] DivisionRestrictedError returns `{"detail": {"error": "division_restricted"}}` with 403
- [ ] All tests from `test_social_router.py` ported and green
- [ ] All tests from `test_social_comprehensive.py` ported and green
- [ ] No public endpoints (all auth-required)
- [ ] Security gate green for social endpoints

---

## Prompt 4: Submissions Blueprint

### Context

Port `apps/api/skillhub/routers/submissions.py` (8 route handlers) to a Flask blueprint. This includes the Gate 2 LLM scan endpoint which was async in FastAPI and is now sync (per Phase 2 conversion). Mixed auth levels: some user-level, some platform-team-only.

### Prerequisites

- SEARCH `apps/api/skillhub/routers/submissions.py` — the router
- SEARCH `apps/api/tests/test_submissions_router.py` — router tests
- SEARCH `apps/api/tests/test_submission_pipeline_comprehensive.py` — comprehensive tests
- SEARCH `apps/api/skillhub/schemas/submission.py` — schemas
- SEARCH `apps/api/skillhub/services/submissions.py` — service layer (now sync after Phase 2)

### Step 1: Create the submissions blueprint

CREATE `apps/api/skillhub/blueprints/submissions.py`:

**User endpoints:**
1. **POST /api/v1/submissions** — 201, triggers gate pipeline
   - Use `@validated_body(SubmissionCreateRequest)`
   - Call `create_submission(db, ...)`
   - For background Gate 2: use `threading.Thread(target=_run_gate2_bg, args=(submission_id,), daemon=True).start()`
   - The background thread function must create its own `SessionLocal()`, call `run_gate2_scan(bg_db, sub_id)`, then close in `finally`
   - Note: the `background_tasks` parameter in the original FastAPI code passes `BackgroundTasks` into the service — in Flask, handle background dispatch at the blueprint level instead

2. **GET /api/v1/submissions/{submission_id}** — owner or platform team
   - Validate UUID format (400 for invalid)
   - Call `get_submission(db, sub_uuid, user_id=..., is_platform_team=...)`
   - Catch `PermissionError` -> 403

**Admin endpoints (platform team only):**
3. **POST /api/v1/admin/submissions/{submission_id}/scan** — trigger Gate 2 LLM scan
   - Now synchronous (Phase 2 converted `run_gate2_scan` from async to sync)
   - Call `run_gate2_scan(db, sub_uuid)` directly (no await)
   - Return result as JSON

4. **GET /api/v1/admin/submissions** — paginated list
   - Use `@validated_query(AdminSubmissionsQueryParams)` with `status_filter`, `page`, `per_page`

5. **POST /api/v1/admin/submissions/{submission_id}/review** — Gate 3 human review
   - Use `@validated_body(ReviewDecisionRequest)`

**Access request endpoints:**
6. **POST /api/v1/skills/{slug}/access-request** — 201, auth required
   - Use `@validated_body(AccessRequestCreateRequest)`
   - Different error handling: "not found" in message -> 404, otherwise -> 400

7. **GET /api/v1/admin/access-requests** — platform team, paginated

8. **POST /api/v1/admin/access-requests/{request_id}/review** — platform team

### Step 2: Handle admin route separation

Admin routes (`/api/v1/admin/...`) should either:
- Be in a separate admin blueprint with its own `before_request` enforcing platform team, OR
- Use a `@require_platform_team` decorator within the same blueprint

Check how Phase 2 structured admin auth. If there is already an admin blueprint with `before_request`, register the admin submission routes there. If not, use per-route enforcement via `g.current_user["is_platform_team"]` checks.

### Step 3: Background task session pattern

For the Gate 2 background scan triggered by submission creation:

```python
def _run_gate2_background(submission_id: UUID) -> None:
    """Run Gate 2 scan in background thread with its own session."""
    from skillhub_db.session import SessionLocal
    bg_db = SessionLocal()
    try:
        run_gate2_scan(bg_db, submission_id)
    except Exception:
        logger.exception("Gate 2 background scan failed for %s", submission_id)
    finally:
        bg_db.close()
```

NEVER use the scoped session proxy in a background thread. Always create a fresh `SessionLocal()`.

### Step 4: Write tests (RED phase)

CREATE `apps/api/tests/test_submissions_blueprint.py`:

Port all tests from `test_submissions_router.py` and `test_submission_pipeline_comprehensive.py`:
- Create submission returns 201
- Create submission triggers background gate scan
- Get submission as owner returns detail
- Get submission as non-owner non-admin returns 403
- Get submission with invalid UUID returns 400
- Admin scan runs synchronously and returns result
- Admin list submissions returns paginated
- Admin review submission returns result
- Create access request returns 201
- Create access request for nonexistent skill returns 404
- Admin list access requests returns paginated
- Admin review access request returns result

### Step 5: Implement until GREEN

TEST RED then TEST GREEN.

### Completion Criteria

- [ ] 8 route handlers in `blueprints/submissions.py`
- [ ] Gate 2 scan is synchronous (no async/await)
- [ ] Background task uses `threading.Thread` with fresh `SessionLocal()`
- [ ] Admin endpoints enforce platform team access
- [ ] All tests ported and green
- [ ] Security gate green

---

## Prompt 5: Flags Blueprint

### Context

Port `apps/api/skillhub/routers/flags.py` (4 route handlers) to a Flask blueprint. The GET endpoint is public (with optional user context for division overrides); CRUD operations are platform-team-only.

### Prerequisites

- SEARCH `apps/api/skillhub/routers/flags.py` — the router
- SEARCH `apps/api/tests/test_flags.py` — basic tests
- SEARCH `apps/api/tests/test_flags_comprehensive.py` — comprehensive tests
- SEARCH `apps/api/skillhub/schemas/flags.py` — schemas
- SEARCH `apps/api/skillhub/services/flags.py` — service layer

### Step 1: Create the flags blueprint

CREATE `apps/api/skillhub/blueprints/flags.py`:

1. **GET /api/v1/flags** (PUBLIC)
   - Extract optional user from `g.get("current_user")` for division context
   - Call `get_flags(db, user_division=division)`
   - Return `jsonify(FlagsListResponse(flags=flags).model_dump(mode="json"))`

2. **POST /api/v1/admin/flags** (platform team, 201)
   - Use `@validated_body(FlagCreateRequest)`
   - Call `create_flag(db, body.key, ...)`
   - Catch `ValueError` -> 409 (duplicate key)

3. **PATCH /api/v1/admin/flags/{key}** (platform team)
   - Use `@validated_body(FlagUpdateRequest)`
   - Call `update_flag(db, key, ...)`
   - Catch `ValueError` -> 404

4. **DELETE /api/v1/admin/flags/{key}** (platform team, 204)
   - Call `delete_flag(db, key)`
   - Catch `ValueError` -> 404
   - Return empty response with 204

### Step 2: Register public endpoint

MODIFY `PUBLIC_ENDPOINTS`:
- Add `"flags.list_flags"`

### Step 3: Register the blueprint

MODIFY app factory.

### Step 4: Write tests (RED phase)

CREATE `apps/api/tests/test_flags_blueprint.py`:

Port tests from `test_flags.py` and `test_flags_comprehensive.py`:
- GET /flags returns flags list (no auth required)
- GET /flags with auth includes division-specific overrides
- POST /admin/flags creates flag and returns 201
- POST /admin/flags with duplicate key returns 409
- POST /admin/flags without admin returns 401/403
- PATCH /admin/flags/{key} updates flag
- PATCH /admin/flags/{key} for nonexistent returns 404
- DELETE /admin/flags/{key} returns 204
- DELETE /admin/flags/{key} for nonexistent returns 404

### Step 5: Implement until GREEN

TEST RED then TEST GREEN.

### Completion Criteria

- [ ] 4 route handlers in `blueprints/flags.py`
- [ ] GET /flags is public (in `PUBLIC_ENDPOINTS`)
- [ ] Admin routes enforce platform team
- [ ] All tests ported and green
- [ ] Security gate green

---

## Prompt 6: Feedback Blueprint (BUG #5 FIX)

### Context

Port `apps/api/skillhub/routers/feedback.py` (4 route handlers) to a Flask blueprint. This prompt also fixes **Bug #5**: `list_feedback()` must JOIN to include `user_display_name` and `skill_name` in the response.

### Prerequisites

- SEARCH `apps/api/skillhub/routers/feedback.py` — the router
- SEARCH `apps/api/tests/test_feedback_service.py` — service tests
- SEARCH `apps/api/skillhub/schemas/feedback.py` — schemas
- SEARCH `apps/api/skillhub/services/feedback.py` — service layer (will be modified for bug fix)

### Step 1: Fix Bug #5 — Add joined fields to feedback

MODIFY `apps/api/skillhub/schemas/feedback.py`:

Add optional fields to `FeedbackResponse`:
```python
class FeedbackResponse(BaseModel):
    # ... existing fields ...
    user_display_name: str | None = None
    skill_name: str | None = None
```

MODIFY `apps/api/skillhub/services/feedback.py`:

Update `list_feedback()` to JOIN the User and Skill tables:
```python
# In list_feedback():
# Add outerjoin to User table for user_display_name
# Add outerjoin to Skill table for skill_name
# Include these fields in the returned dicts
```

The join should be:
- `outerjoin(User, SkillFeedback.user_id == User.id)` for `user_display_name`
- `outerjoin(Skill, SkillFeedback.skill_id == Skill.id)` for `skill_name`
- Add `.add_columns(User.display_name, Skill.name)` to the query

### Step 2: Create the feedback blueprint

CREATE `apps/api/skillhub/blueprints/feedback.py`:

1. **POST /api/v1/feedback** (auth, 201)
   - Use `@validated_body(FeedbackCreate)`
   - Call `create_feedback(db, user_id=..., ...)`
   - Return `FeedbackResponse(**result).model_dump(mode="json")` with 201

2. **GET /api/v1/admin/feedback** (platform team)
   - Use `@validated_query(FeedbackQueryParams)` — create model with: `category`, `sentiment`, `status`, `sort`, `page`, `per_page`
   - Note: FastAPI uses `alias="status"` for the `feedback_status` param — in Flask, the query param name should just be `status` in the Pydantic model
   - Call `list_feedback(db, ...)`
   - Return `FeedbackListResponse`

3. **POST /api/v1/feedback/{feedback_id}/upvote** (auth)
   - Call `upvote_feedback(db, feedback_id=..., user_id=...)`
   - Catch `ValueError` -> 404

4. **PATCH /api/v1/admin/feedback/{feedback_id}/status** (platform team)
   - Use `@validated_body` with a simple model: `class FeedbackStatusUpdate(BaseModel): status: str`
   - Call `update_feedback_status(db, ...)`
   - Catch `ValueError` -> 400

### Step 3: Register the blueprint

MODIFY app factory. No public endpoints.

### Step 4: Write tests (RED phase)

CREATE `apps/api/tests/test_feedback_blueprint.py`:

Port tests from `test_feedback_service.py` and add new tests for Bug #5:
- Submit feedback returns 201
- Submit feedback without auth returns 401
- List feedback (admin) returns paginated with filters
- **NEW: List feedback includes user_display_name and skill_name in response**
- **NEW: List feedback with no joined user/skill returns None for those fields**
- Upvote feedback returns updated count
- Upvote nonexistent feedback returns 404
- Update feedback status (admin) returns updated status
- Update feedback status with invalid value returns 400

### Step 5: Implement until GREEN

TEST RED then TEST GREEN.

### Step 6: Verify Bug #5 fix

Write a specific integration test that:
1. Creates a feedback entry with a known user and skill
2. Calls `list_feedback()`
3. Asserts `user_display_name` is the user's display name (not None)
4. Asserts `skill_name` is the skill's name (not None)

### Completion Criteria

- [ ] 4 route handlers in `blueprints/feedback.py`
- [ ] Bug #5 fixed: `list_feedback()` JOINs User and Skill tables
- [ ] `FeedbackResponse` schema has `user_display_name` and `skill_name` fields
- [ ] All tests ported and green, including new bug fix tests
- [ ] Security gate green

---

## Prompt 7: Roadmap/Changelog Blueprint (BUG #6 FIX)

### Context

Port `apps/api/skillhub/routers/roadmap.py` (6 route handlers) to a Flask blueprint. This prompt also fixes **Bug #6**: `PlatformUpdateResponse` is missing the `version_tag` field. The changelog endpoint is public.

### Prerequisites

- SEARCH `apps/api/skillhub/routers/roadmap.py` — the router
- SEARCH `apps/api/tests/test_roadmap_service.py` — service tests
- SEARCH `apps/api/skillhub/schemas/feedback.py` — schemas (roadmap schemas live here)
- SEARCH `apps/api/skillhub/services/roadmap.py` — service layer

### Step 1: Fix Bug #6 — Add version_tag to PlatformUpdateResponse

MODIFY `apps/api/skillhub/schemas/feedback.py` (or wherever `PlatformUpdateResponse` is defined):

```python
class PlatformUpdateResponse(BaseModel):
    # ... existing fields ...
    version_tag: str | None = None  # BUG #6 FIX: was missing
```

VERIFY that `ship_update()` in the service layer already returns `version_tag` in its result dict. If not, modify the service to include it.

### Step 2: Create the roadmap blueprint

CREATE `apps/api/skillhub/blueprints/roadmap.py`:

1. **GET /api/v1/admin/platform-updates** (platform team)
   - Use `@validated_query` with model: `status` (alias handling), `page`, `per_page`
   - Call `list_updates(db, ...)`
   - Return `PlatformUpdateListResponse`

2. **POST /api/v1/admin/platform-updates** (platform team, 201)
   - Use `@validated_body(PlatformUpdateCreate)`
   - Call `create_update(db, ...)`
   - Return `PlatformUpdateResponse` with 201

3. **PATCH /api/v1/admin/platform-updates/{update_id}** (platform team)
   - Use `@validated_body` with a simple status model
   - Call `update_status(db, ...)`
   - Catch `ValueError` -> 400

4. **POST /api/v1/admin/platform-updates/{update_id}/ship** (platform team)
   - Use `@validated_body(ShipRequest)`
   - Call `ship_update(db, ...)`
   - Catch `ValueError` -> 400

5. **DELETE /api/v1/admin/platform-updates/{update_id}** (SECURITY TEAM, not platform team)
   - This endpoint uses `require_security_team`, not `require_platform_team`
   - Enforce via a separate check: `g.current_user.get("is_security_team")` must be True
   - Call `delete_update(db, ...)`
   - Catch `ValueError` -> 404

6. **GET /api/v1/changelog** (PUBLIC)
   - Call `list_updates(db, status="shipped", ...)`
   - Map results to `ChangelogEntry` objects
   - **Bug #6 FIX**: include `version_tag` in `ChangelogEntry` from the result dict (was hardcoded to `None` in FastAPI version)
   - Return `ChangelogResponse`

### Step 3: Register public endpoint

MODIFY `PUBLIC_ENDPOINTS`:
- Add `"roadmap.get_changelog"`

### Step 4: Register the blueprint

MODIFY app factory.

### Step 5: Write tests (RED phase)

CREATE `apps/api/tests/test_roadmap_blueprint.py`:

Port tests from `test_roadmap_service.py` and add new tests:
- List platform updates (admin) returns paginated
- Create platform update returns 201
- Patch platform update status
- Ship platform update
- **NEW: Shipped update includes version_tag in response**
- Delete platform update requires security team (not just platform team)
- Delete by platform team (non-security) returns 403
- Get changelog is public (no auth required)
- **NEW: Changelog entries include version_tag**

### Step 6: Implement until GREEN

TEST RED then TEST GREEN.

### Step 7: Verify Bug #6 fix

Write a specific test that:
1. Creates a platform update
2. Ships it with a version_tag like `"v1.2.0"`
3. Calls the changelog endpoint
4. Asserts the `version_tag` field is `"v1.2.0"` (not None)

### Completion Criteria

- [ ] 6 route handlers in `blueprints/roadmap.py`
- [ ] Bug #6 fixed: `PlatformUpdateResponse` includes `version_tag`
- [ ] Bug #6 fixed: Changelog entries include `version_tag` from DB
- [ ] DELETE endpoint enforces security team (not platform team)
- [ ] GET /changelog is public (in `PUBLIC_ENDPOINTS`)
- [ ] All tests ported and green, including bug fix tests
- [ ] Security gate green

---

## Prompt 8: Integration Verification

### Context

All 7 blueprints are now ported. This prompt runs the full integration verification suite to confirm everything works together.

### Step 1: Full test suite

VERIFY:
```bash
pytest apps/api/tests/ -v --tb=short 2>&1 | tail -50
```

All tests must pass. If any fail, diagnose and fix before proceeding.

### Step 2: Coverage gate

VERIFY:
```bash
pytest apps/api/tests/ --cov=skillhub --cov-report=term-missing --cov-fail-under=80
```

Coverage must be >= 80%. If below, identify uncovered lines and add targeted tests.

### Step 3: Security gate

VERIFY:
```bash
pytest apps/api/tests/test_security_migration_gate.py -v
```

All security classes must pass:
- **Class 1:** Every non-public endpoint returns 401 without token
- **Class 2:** Expired tokens return 401
- **Class 3:** Invalid tokens return 401
- **Class 4:** Admin endpoints return 403 for non-admin users
- **Class 5:** Division-restricted endpoints return 403 for wrong division
- **Class 7:** All endpoints have `_auth_required = True` attribute (or are in `PUBLIC_ENDPOINTS`)
- **Class 8:** No new endpoints without test coverage

### Step 4: PUBLIC_ENDPOINTS audit

VERIFY that `PUBLIC_ENDPOINTS` contains exactly these entries (and no more):
- `"health.healthcheck"` (from Phase 1)
- `"auth.login"` / `"auth.callback"` (from Phase 2)
- `"skills.list_skills"`
- `"skills.list_categories"`
- `"skills.get_skill"`
- `"flags.list_flags"`
- `"roadmap.get_changelog"`

Any endpoint NOT in this list must return 401 without a token.

### Step 5: OpenAPI spec parity check

VERIFY that the Flask app generates an OpenAPI spec that covers all ported paths:

```bash
python -c "
from skillhub.app import create_app
app = create_app()
with app.app_context():
    spec = app.spec
    paths = sorted(spec['paths'].keys())
    for p in paths:
        methods = sorted(spec['paths'][p].keys())
        print(f'{p}: {methods}')
"
```

Compare output against the FastAPI baseline. All 40+ endpoints should be present with correct methods.

### Step 6: Blueprint registration audit

VERIFY all 7 blueprints are registered:

```bash
python -c "
from skillhub.app import create_app
app = create_app()
print('Registered blueprints:')
for name in sorted(app.blueprints.keys()):
    print(f'  - {name}')
"
```

Expected (at minimum): `skills`, `users`, `social`, `submissions`, `flags`, `feedback`, `roadmap` plus any Phase 1/2 blueprints (`health`, `auth`, `stub_auth`).

### Step 7: Bug fix verification

Run targeted tests confirming both bug fixes:

```bash
# Bug #5: Feedback joined fields
pytest apps/api/tests/test_feedback_blueprint.py -k "display_name or skill_name" -v

# Bug #6: Roadmap version_tag
pytest apps/api/tests/test_roadmap_blueprint.py -k "version_tag" -v
```

### Completion Criteria (Phase 3 Exit Gate)

- [ ] All tests pass (`pytest apps/api/tests/`)
- [ ] Coverage >= 80%
- [ ] Security gate Classes 1-5, 7, 8 all green
- [ ] `PUBLIC_ENDPOINTS` contains exactly the expected entries
- [ ] OpenAPI spec covers all ported paths
- [ ] All 7 blueprints registered
- [ ] Bug #5 (feedback joined fields) verified
- [ ] Bug #6 (roadmap version_tag) verified
- [ ] No async code remains in any blueprint or ported service
- [ ] No `dependency_overrides` usage in any Flask test file
- [ ] All background tasks use `threading.Thread` with fresh `SessionLocal()`

---

## Appendix A: Files Created/Modified in This Phase

### New Files

| File | Purpose |
|------|---------|
| `apps/api/skillhub/blueprints/skills.py` | Skills browse, detail, versions |
| `apps/api/skillhub/blueprints/users.py` | User profile and collections |
| `apps/api/skillhub/blueprints/social.py` | Install, favorite, fork, follow, reviews, comments |
| `apps/api/skillhub/blueprints/submissions.py` | Submission pipeline and access requests |
| `apps/api/skillhub/blueprints/flags.py` | Feature flags CRUD |
| `apps/api/skillhub/blueprints/feedback.py` | Feedback submission and triage |
| `apps/api/skillhub/blueprints/roadmap.py` | Platform updates and changelog |
| `apps/api/skillhub/schemas/skill_query.py` | Query param models for skills |
| `apps/api/skillhub/schemas/user_query.py` | Query param models for users |
| `apps/api/tests/test_skills_blueprint.py` | Skills blueprint tests |
| `apps/api/tests/test_users_blueprint.py` | Users blueprint tests |
| `apps/api/tests/test_social_blueprint.py` | Social blueprint tests |
| `apps/api/tests/test_submissions_blueprint.py` | Submissions blueprint tests |
| `apps/api/tests/test_flags_blueprint.py` | Flags blueprint tests |
| `apps/api/tests/test_feedback_blueprint.py` | Feedback blueprint tests |
| `apps/api/tests/test_roadmap_blueprint.py` | Roadmap blueprint tests |

### Modified Files

| File | Change |
|------|--------|
| `apps/api/skillhub/app.py` | Register 7 new blueprints |
| `apps/api/skillhub/auth.py` | Add 4 entries to `PUBLIC_ENDPOINTS` |
| `apps/api/skillhub/schemas/feedback.py` | Add `user_display_name`, `skill_name` to `FeedbackResponse`; add `version_tag` to `PlatformUpdateResponse` |
| `apps/api/skillhub/services/feedback.py` | JOIN User and Skill tables in `list_feedback()` |

## Appendix B: Route Count Summary

| Blueprint | Routes | Public | Auth | Admin | Security Team |
|-----------|--------|--------|------|-------|---------------|
| Skills | 6 | 3 | 3 | 0 | 0 |
| Users | 5 | 0 | 5 | 0 | 0 |
| Social | 16 | 0 | 16 | 0 | 0 |
| Submissions | 8 | 0 | 3 | 5 | 0 |
| Flags | 4 | 1 | 0 | 3 | 0 |
| Feedback | 4 | 0 | 2 | 2 | 0 |
| Roadmap | 6 | 1 | 0 | 4 | 1 |
| **Total** | **49** | **5** | **29** | **14** | **1** |
