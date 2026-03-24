# Phase 4: Admin, Analytics, Exports — Implementation Guide

**Phase:** 4 of 5
**Prerequisites:** Phase 3 complete (all core domain blueprints ported)
**Exit gate:** All 63 paths ported, 326 security tests green, OpenAPI QA verification, coverage >=80%
**Estimated prompts:** 7

---

## Prompt 1 — Admin Blueprint with Platform Team Gate

### Context

The admin blueprint contains 7 endpoints that manage skills (feature, deprecate, remove), trigger trending recalculation, query audit logs, and manage users. All endpoints require `platform_team` access except `DELETE /skills/{slug}` which requires `security_team`.

In FastAPI, each endpoint individually declares `Depends(require_platform_team)` or `Depends(require_security_team)`. In Flask, the admin blueprint gets its own `before_request` hook that enforces `platform_team` by default, with a per-endpoint override for the security team delete route.

### References

- **FastAPI source:** `apps/api/skillhub/routers/admin.py` (184 lines, 7 endpoints)
- **FastAPI dependencies:** `apps/api/skillhub/dependencies.py` (require_platform_team, require_security_team)
- **Service layer:** `apps/api/skillhub/services/admin.py` (feature_skill, deprecate_skill, remove_skill, query_audit_log, list_users, update_user)
- **Schemas:** `apps/api/skillhub/schemas/admin.py`
- **ADR:** `docs/migration/adr-001-fastapi-to-flask.md` (Decision 3: before_request with PUBLIC_ENDPOINTS)

### Tasks

1. Create `apps/api/skillhub/blueprints/admin.py` with a Blueprint named `"admin"` and prefix `/api/v1/admin`.

2. Register a `@admin_bp.before_request` hook that:
   - Reads `g.current_user` (already set by the app-level `before_request` in the auth layer)
   - Checks `g.current_user.get("is_platform_team")` is truthy
   - Returns `jsonify({"detail": "Platform team access required"}), 403` if not
   - Exception: for the `remove_skill_endpoint` view function, check `is_security_team` instead

3. Implement the `before_request` security team override using a set of view function names:
   ```python
   _SECURITY_TEAM_ENDPOINTS = frozenset({"remove_skill_endpoint"})

   @admin_bp.before_request
   def enforce_admin_access():
       user = g.current_user
       view_fn = request.endpoint.split(".")[-1] if request.endpoint else ""
       if view_fn in _SECURITY_TEAM_ENDPOINTS:
           if not user.get("is_security_team"):
               return jsonify({"detail": "Security team access required"}), 403
       else:
           if not user.get("is_platform_team"):
               return jsonify({"detail": "Platform team access required"}), 403
   ```

4. Port each endpoint, converting FastAPI patterns to Flask:
   - `HTTPException(status_code=404)` becomes `return jsonify({"detail": str(err)}), 404`
   - `Depends(get_db)` becomes `db = current_app.extensions["db"]()`
   - `Annotated[dict, Depends(require_platform_team)]` becomes `g.current_user` (pre-validated by `before_request`)
   - `request.client.host` becomes `request.remote_addr`
   - Response models: call `.model_dump(mode="json")` then `jsonify()`

5. Port the 7 endpoints:
   - `POST /skills/{slug}/feature` — `validated_body(FeatureSkillRequest)`, calls `feature_skill()`
   - `POST /skills/{slug}/deprecate` — no body, calls `deprecate_skill()`
   - `DELETE /skills/{slug}` — no body, calls `remove_skill()`, passes `request.remote_addr` as ip_address
   - `POST /recalculate-trending` — no body, calls `recalculate_trending_scores()`
   - `GET /audit-log` — `validated_query(AuditLogQueryParams)`, calls `query_audit_log()`
   - `GET /users` — `validated_query(AdminUserQueryParams)`, calls `list_users()`
   - `PATCH /users/{user_id}` — `validated_body(AdminUserUpdateRequest)`, calls `update_user()`

6. Create query param models for audit-log and users endpoints (if not already in schemas):
   ```python
   class AuditLogQueryParams(BaseModel):
       event_type: str | None = None
       actor_id: str | None = None
       target_id: str | None = None
       date_from: datetime | None = None
       date_to: datetime | None = None
       page: int = Field(default=1, ge=1)
       per_page: int = Field(default=20, ge=1, le=100)

   class AdminUserQueryParams(BaseModel):
       division: str | None = None
       role: str | None = None
       is_platform_team: bool | None = None
       is_security_team: bool | None = None
       page: int = Field(default=1, ge=1)
       per_page: int = Field(default=20, ge=1, le=100)
   ```

### Tests — Write FIRST (TDD)

Create `apps/api/tests/test_admin.py`:

1. **test_feature_skill_platform_team_ok** — platform_team token, mock service returns success, assert 200
2. **test_feature_skill_regular_user_403** — regular user token, assert 403 with "Platform team access required"
3. **test_feature_skill_not_found_404** — service raises ValueError, assert 404
4. **test_deprecate_skill_ok** — platform_team token, assert 200
5. **test_remove_skill_security_team_ok** — security_team token, assert 200
6. **test_remove_skill_platform_team_403** — platform_team (NOT security), assert 403 with "Security team access required"
7. **test_remove_skill_regular_user_403** — regular user, assert 403
8. **test_recalculate_trending_ok** — platform_team, assert 200 with `{"updated": N}`
9. **test_audit_log_filtered** — platform_team, query params event_type+date_from, assert 200
10. **test_list_users_filtered** — platform_team, query params division+is_platform_team, assert 200
11. **test_update_user_ok** — platform_team, JSON body, assert 200
12. **test_update_user_not_found** — service raises ValueError, assert 404
13. **test_no_token_401** — no auth header on admin endpoint, assert 401

### Verification

```bash
cd apps/api && python -m pytest tests/test_admin.py -v --tb=short
```

All 13 tests green. The `before_request` hook must reject non-platform/non-security users before any route logic executes.

---

## Prompt 2 — Analytics Blueprint

### Context

The analytics blueprint provides 4 read-only endpoints under `/api/v1/admin/analytics/`. All require `platform_team` access (inherited from the admin blueprint's `before_request` if nested, or enforced independently).

These endpoints are registered under the admin prefix in FastAPI. In Flask, you have two options:
1. Register as part of the admin blueprint (shares the `before_request` hook) — preferred
2. Register as a separate blueprint with its own platform_team gate

Decision: Register analytics routes directly on the admin blueprint since they share the `/api/v1/admin/` prefix and the same access control.

### References

- **FastAPI source:** `apps/api/skillhub/routers/analytics.py` (67 lines, 4 endpoints)
- **Schemas:** `apps/api/skillhub/schemas/analytics.py`
- **Service layer:** `apps/api/skillhub/services/analytics.py`
- **Query normalization:** `docs/migration/query-normalization-contract.md`

### Tasks

1. Add analytics routes to `apps/api/skillhub/blueprints/admin.py` (or a separate file imported and registered on the admin blueprint).

2. Create query param models:
   ```python
   class SummaryQueryParams(BaseModel):
       division: str = "__all__"

   class TimeSeriesQueryParams(BaseModel):
       days: int = Field(default=30, ge=1, le=365)
       division: str = "__all__"

   class FunnelQueryParams(BaseModel):
       days: int = Field(default=30, ge=1, le=365)
       division: str = "__all__"

   class TopSkillsQueryParams(BaseModel):
       limit: int = Field(default=10, ge=1, le=50)
   ```

3. Port each endpoint:
   - `GET /analytics/summary` — `validated_query(SummaryQueryParams)`, calls `get_summary(db, division=query.division)`
   - `GET /analytics/time-series` — `validated_query(TimeSeriesQueryParams)`, calls `get_time_series()`
   - `GET /analytics/submission-funnel` — `validated_query(FunnelQueryParams)`, calls `get_submission_funnel()`
   - `GET /analytics/top-skills` — `validated_query(TopSkillsQueryParams)`, calls `get_top_skills()`

4. All responses use `.model_dump(mode="json")` through the response schema, then `jsonify()`.

### Tests — Write FIRST (TDD)

Create `apps/api/tests/test_analytics.py`:

1. **test_summary_default_division** — platform_team, no params, assert 200, service called with `division="__all__"`
2. **test_summary_specific_division** — `?division=engineering`, assert service called with `division="engineering"`
3. **test_time_series_default** — no params, assert `days=30`, `division="__all__"` passed to service
4. **test_time_series_custom_days** — `?days=90`, assert service called with `days=90`
5. **test_time_series_invalid_days** — `?days=999`, assert 422 (le=365 violated)
6. **test_funnel_ok** — assert 200, response matches FunnelResponse shape
7. **test_top_skills_default_limit** — assert service called with `limit=10`
8. **test_top_skills_custom_limit** — `?limit=25`, assert service called with `limit=25`
9. **test_top_skills_invalid_limit** — `?limit=100`, assert 422 (le=50 violated)
10. **test_analytics_regular_user_403** — regular user token, assert 403

### Verification

```bash
cd apps/api && python -m pytest tests/test_analytics.py -v --tb=short
```

All 10 tests green.

---

## Prompt 3 — Exports Blueprint (3 Known Bug Fixes)

### Context

The exports blueprint has 2 endpoints and 3 known bugs that must be fixed in the Flask port. The FastAPI implementation already has partial fixes in the service layer, but the route layer has contract issues.

### Known Bugs to Fix

| Bug | FastAPI Behavior | Flask Fix |
|-----|-----------------|-----------|
| BUG #1 | ExportRequest only has `scope` and `format` | Add `start_date: str \| None = None` and `end_date: str \| None = None` to request body, wire into `filters` dict |
| BUG #2 | Service returns `download_url` (already fixed in service layer) | Verify Flask route passes through `download_url` not `file_path` |
| BUG #3 | Service returns `status: "pending"` (already fixed in service layer) | Verify Flask route passes through `status: "pending"` not `"queued"` |

### References

- **FastAPI source:** `apps/api/skillhub/routers/exports.py` (49 lines, 2 endpoints)
- **Service layer:** `apps/api/skillhub/services/exports.py` — already returns `download_url` and maps `queued` to `pending`
- **ADR known bugs section:** `docs/migration/adr-001-fastapi-to-flask.md` line 147

### Tasks

1. Create `apps/api/skillhub/blueprints/exports.py` with routes registered on the admin blueprint (prefix `/api/v1/admin/exports`).

2. Fix BUG #1 — update the request body schema:
   ```python
   class ExportRequest(BaseModel):
       scope: str = "installs"
       format: str = "csv"
       start_date: str | None = None
       end_date: str | None = None
   ```

3. Wire `start_date`/`end_date` into the `filters` dict passed to the service:
   ```python
   filters = {}
   if body.start_date:
       filters["start_date"] = body.start_date
   if body.end_date:
       filters["end_date"] = body.end_date

   result = request_export(
       db, user_id=UUID(user["user_id"]),
       scope=body.scope, format=body.format, filters=filters,
   )
   ```

4. Port `POST /exports` — `validated_body(ExportRequest)`, calls `request_export()`, rate limit 429 on ValueError.

5. Port `GET /exports/{job_id}` — calls `get_export_status()`, returns 404 if None.

6. Verify the service layer returns `download_url` (not `file_path`) and `status: "pending"` (not `"queued"`) — these are already fixed in `services/exports.py`. The Flask route just needs to pass through the dict as-is via `jsonify()`.

### Tests — Write FIRST (TDD)

Create `apps/api/tests/test_exports.py`:

1. **test_create_export_ok** — platform_team, JSON body `{"scope": "installs"}`, assert 200 with `status: "pending"`
2. **test_create_export_with_dates** — body includes `start_date` and `end_date`, verify `filters` dict passed to service contains both
3. **test_create_export_rate_limited** — service raises ValueError, assert 429
4. **test_create_export_regular_user_403** — regular user, assert 403
5. **test_export_status_ok** — mock service returns dict with `download_url`, assert 200 and response contains `download_url` (NOT `file_path`)
6. **test_export_status_pending** — mock service returns `status: "pending"`, assert response has `"pending"` (NOT `"queued"`)
7. **test_export_status_not_found** — service returns None, assert 404
8. **test_create_export_json_body_not_query_params** — send as query params, assert route ignores them (body validation)

### Verification

```bash
cd apps/api && python -m pytest tests/test_exports.py -v --tb=short
```

All 8 tests green. Specifically verify tests 2, 5, 6 which cover the 3 bug fixes.

---

## Prompt 4 — Review Queue Blueprint (event_type Bug Fix)

### Context

The review queue blueprint has 3 endpoints for the human-in-the-loop (HITL) approval workflow. The service layer already contains the fix for the `event_type` string bug (uses dict lookup instead of f-string), but you must verify this is correctly wired in the Flask port.

### Known Bug (Already Fixed in Service)

The original FastAPI service had `f"submission.{decision}d"` which produced `"submission.rejectd"` (missing 'e'). The current service uses a dict lookup:
```python
_event_map = {
    "approve": "submission.approved",
    "reject": "submission.rejected",
    "request_changes": "submission.changes_requested",
}
event_type = _event_map[decision]
```

This is already correct in `apps/api/skillhub/services/review_queue.py`. The Flask port reuses this service file, so the bug is fixed. But tests must explicitly verify the correct event_type strings.

### References

- **FastAPI source:** `apps/api/skillhub/routers/review_queue.py` (92 lines, 3 endpoints)
- **Service layer:** `apps/api/skillhub/services/review_queue.py` (184 lines)
- **Schemas:** `apps/api/skillhub/schemas/review_queue.py`
- **Security gate:** Class 8 (TestReviewQueueWorkflow)

### Tasks

1. Add review queue routes to `apps/api/skillhub/blueprints/admin.py` (or a dedicated file registered on the admin blueprint) with prefix `/review-queue`.

2. Port 3 endpoints:
   - `GET /review-queue` — `validated_query` with page/per_page, calls `get_review_queue()`
   - `POST /review-queue/{submission_id}/claim` — no body, calls `claim_submission()`
   - `POST /review-queue/{submission_id}/decision` — `validated_body(DecisionRequest)`, calls `decide_submission()`

3. Error mapping:
   - `ValueError` from service -> 404
   - `PermissionError` from service -> 403 (self-approval prevention)

4. Verify self-approval prevention: the service raises `PermissionError("Cannot review your own submission")` when `submission.submitted_by == reviewer_id`. The Flask route must catch this and return 403.

5. Verify claim writes `AuditLog` with `event_type="submission.claimed"` — this happens in the service layer, test must assert the audit log entry exists after claim.

### Tests — Write FIRST (TDD)

Create `apps/api/tests/test_review_queue.py`:

1. **test_list_review_queue_ok** — platform_team, assert 200 with paginated response
2. **test_list_review_queue_pagination** — `?page=2&per_page=5`, assert params forwarded to service
3. **test_claim_submission_ok** — assert 200, response includes `submission_id`, `reviewer_id`, `claimed_at`
4. **test_claim_not_found** — service raises ValueError, assert 404
5. **test_decide_approve_ok** — body `{"decision": "approve"}`, assert 200
6. **test_decide_reject_ok** — body `{"decision": "reject"}`, assert 200
7. **test_decide_request_changes_ok** — body `{"decision": "request_changes"}`, assert 200
8. **test_decide_self_approval_403** — service raises PermissionError, assert 403 with "Cannot review your own submission"
9. **test_decide_not_found** — service raises ValueError, assert 404
10. **test_event_type_reject_correct** — after a reject decision, verify audit log event_type is `"submission.rejected"` (not `"submission.rejectd"`)
11. **test_event_type_approve_correct** — verify `"submission.approved"`
12. **test_claim_writes_audit_log** — after claim, verify AuditLog with event_type `"submission.claimed"` exists
13. **test_review_queue_regular_user_403** — regular user token, assert 403

### Verification

```bash
cd apps/api && python -m pytest tests/test_review_queue.py -v --tb=short
```

All 13 tests green. Tests 10-12 are the critical security/correctness assertions.

---

## Prompt 5 — Port Remaining Test Files

### Context

Phase 3 ported the core domain test files. This prompt ports the remaining test files that exercise cross-cutting concerns: division enforcement, multi-identity auth, regression fixes, and seed data integrity. These tests are the backbone of the security migration gate.

### Priority Order

Port in this order (security-critical first):

1. **test_division_enforcement.py** (385 lines) — FIRST, security critical
2. **test_auth_multi_identity.py** — auth edge cases
3. **test_regression_fixes.py** — historical bug prevention
4. **test_reviews_router.py** — review endpoint integration
5. **test_reviews_comprehensive.py** — review edge cases
6. **test_fix_social_users_router.py** — social/user interaction fixes
7. **test_seed_data_integrity.py** — data consistency checks
8. **test_dependencies.py** — dependency injection tests

### Conversion Pattern (Apply to ALL files)

Every test file follows this conversion:

```python
# BEFORE (FastAPI)
from fastapi.testclient import TestClient
from skillhub.dependencies import get_db
from skillhub.main import create_app
app = create_app(settings=settings)
app.dependency_overrides[get_db] = lambda: db_mock
client = TestClient(app)

# AFTER (Flask)
from skillhub.app import create_app
app = create_app(config=AppConfig(session_factory=lambda: db_mock))
client = app.test_client()
```

### Tasks

1. For each file, create the Flask equivalent in `apps/api/tests/`:
   - Replace `TestClient` with `app.test_client()`
   - Replace `dependency_overrides[get_db]` with `session_factory` injection
   - Replace `response.status_code` usage (same API on Flask test client)
   - Replace `response.json()` with `response.get_json()`
   - Keep all assertions identical — these are behavioral parity tests

2. Verify portable service tests work without changes:
   - `test_skills_service.py` — pure service layer, no framework dependency
   - `test_social_service.py` — same
   - `test_reviews_service.py` — same
   - `test_users_service.py` — same
   - `test_skill_schemas.py` — Pydantic schema tests, framework-agnostic

3. Audit `PUBLIC_ENDPOINTS` against `TestPublicRoutesAccessible`:
   - Collect all endpoints that should be public (health, auth, OpenAPI spec)
   - Verify the `PUBLIC_ENDPOINTS` frozenset in the Flask app matches
   - Verify the test class asserts 401 for every non-public endpoint without a token

### Tests

No new tests to write — this prompt ports existing tests. The verification is that all ported tests pass.

### Verification

```bash
# Run all ported test files
cd apps/api && python -m pytest tests/test_division_enforcement.py tests/test_auth_multi_identity.py tests/test_regression_fixes.py tests/test_reviews_router.py tests/test_reviews_comprehensive.py tests/test_fix_social_users_router.py tests/test_seed_data_integrity.py tests/test_dependencies.py -v --tb=short

# Verify service tests still pass (should be unchanged)
cd apps/api && python -m pytest tests/test_skills_service.py tests/test_social_service.py tests/test_reviews_service.py tests/test_users_service.py tests/test_skill_schemas.py -v --tb=short
```

All tests green. Zero test failures.

---

## Prompt 6 — Full Security Migration Gate (326 Tests)

### Context

The security migration gate is a suite of 326 tests organized into 8 classes. All 8 classes must pass at 100% against the Flask app before any traffic can be routed to it. The test file `test_security_migration_gate.py` was written against FastAPI and must be ported to Flask.

### The 8 Security Gate Classes

| Class | Name | Tests | Focus |
|-------|------|-------|-------|
| 1 | TestAuthenticationEnforcement | ~40 | Every non-public endpoint returns 401 without token |
| 2 | TestJWTValidation | ~30 | Expired, malformed, wrong-secret tokens rejected |
| 3 | TestDivisionIsolation | ~60 | Cross-division data access blocked |
| 4 | TestRoleEscalation | ~25 | Regular users cannot access admin endpoints |
| 5 | TestAdminBoundary | ~35 | Platform team vs security team access separation |
| 6 | TestAuditLogIntegrity | ~20 | Audit log writes are append-only, correct event types |
| 7 | TestInputValidation | ~50 | Malformed inputs return 422, not 500 |
| 8 | TestReviewQueueWorkflow | ~66 | Full HITL workflow including self-approval prevention |

### Tasks

1. Port `apps/api/tests/test_security_migration_gate.py` to `apps/api/tests/test_security_migration_gate.py`:
   - Same conversion pattern as Prompt 5 (TestClient -> test_client, dependency_overrides -> session_factory)
   - All 326 test assertions must remain identical
   - Do NOT weaken any assertion

2. Focus on Classes 5 and 6 (AdminBoundary and AuditLogIntegrity) — these are the admin-specific security gates:
   - Class 5 must verify that `before_request` on the admin blueprint correctly separates platform_team from security_team access
   - Class 6 must verify audit log entries are written with correct event_type strings

3. Focus on Class 8 (TestReviewQueueWorkflow):
   - Self-approval prevention returns 403
   - Claim writes audit log with `event_type="submission.claimed"`
   - Decision writes audit log with correct event_type (dict lookup, not f-string)

4. Run all 326 tests. Target: 100% pass rate. Any failure blocks the migration.

### Verification

```bash
cd apps/api && python -m pytest tests/test_security_migration_gate.py -v --tb=short 2>&1 | tail -20
```

Expected output:
```
326 passed in X.XXs
```

If any tests fail:
1. Read the failure message carefully
2. Check if it is a Flask behavioral difference (response format, status code)
3. Fix the Flask implementation, NOT the test
4. Re-run until 326/326 pass

---

## Prompt 7 — OpenAPI Spec QA Verification

### Context

The OpenAPI spec pipeline (`gen:openapi -> gen:types -> typecheck:web`) is load-bearing for TypeScript type generation. The Flask app uses apiflask to generate OpenAPI specs. This prompt verifies the Flask-generated spec is correct and documents the 6 improvements over FastAPI behavior.

### The 6 Improvements Over FastAPI Behavior

These are intentional changes where the Flask implementation fixes known issues:

| # | Endpoint | Field | FastAPI (bug) | Flask (fix) |
|---|----------|-------|---------------|-------------|
| 1 | POST /exports | body | query params | JSON body with start_date/end_date |
| 2 | GET /exports/{job_id} | response | `file_path` | `download_url` |
| 3 | POST /exports | response | `status: "queued"` | `status: "pending"` |
| 4 | GET /feedback/{slug} | response | missing joined fields | includes author_name, author_avatar |
| 5 | GET /roadmap | response | `version_tag` | `release_tag` |
| 6 | POST /review-queue/{id}/decision | audit | `"submission.rejectd"` | `"submission.rejected"` |

### Tasks

1. Generate the Flask OpenAPI spec:
   ```bash
   mise run gen:openapi:flask
   ```
   This should output to `specs/openapi-flask.json`.

2. Diff against the baseline:
   ```bash
   diff <(jq --sort-keys . specs/openapi-baseline.json) <(jq --sort-keys . specs/openapi-flask.json)
   ```

3. Verify path count:
   ```bash
   jq '.paths | length' specs/openapi-flask.json
   # Expected: 63
   ```

4. For each difference found in the diff:
   - If it matches one of the 6 improvements above, mark as EXPECTED
   - If it does NOT match, investigate and fix the Flask implementation

5. Generate TypeScript types from the Flask spec:
   ```bash
   mise run gen:types
   ```

6. Run TypeScript type checking:
   ```bash
   cd apps/web && npx tsc --noEmit
   ```
   This must pass with zero errors. If types changed due to the 6 bug fixes, the frontend code may need updates to match the corrected contract.

7. Document any frontend changes required:
   - `download_url` instead of `file_path` in export status polling
   - `"pending"` instead of `"queued"` in export status checks
   - `start_date`/`end_date` in export request body

### Verification

```bash
# Full pipeline
mise run gen:openapi:flask && mise run gen:types && cd apps/web && npx tsc --noEmit
```

Zero errors. Path count = 63. Only the 6 documented improvements appear in the diff.

---

## Exit Gate Checklist

Before declaring Phase 4 complete, verify ALL of the following:

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 1 | All admin endpoints ported | `grep -c "def " apps/api/skillhub/blueprints/admin.py` | 7+ view functions |
| 2 | All analytics endpoints ported | count analytics routes | 4 endpoints |
| 3 | Exports bug fixes verified | `pytest tests/test_exports.py -k "dates or download_url or pending"` | 3 pass |
| 4 | Review queue event_type fix | `pytest tests/test_review_queue.py -k "event_type"` | 2 pass |
| 5 | Division enforcement tests | `pytest tests/test_division_enforcement.py` | All pass |
| 6 | Security migration gate | `pytest tests/test_security_migration_gate.py` | 326 pass |
| 7 | OpenAPI path count | `jq '.paths \| length' specs/openapi-flask.json` | 63 |
| 8 | TypeScript types compile | `cd apps/web && npx tsc --noEmit` | 0 errors |
| 9 | Coverage gate | `pytest --cov --cov-fail-under=80` | >=80% |

All 9 checks must pass. Any failure means Phase 4 is not complete.
