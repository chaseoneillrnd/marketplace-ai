# Phase 6A: Admin HITL Queue Enhancements — Agent-Executable Implementation Guide

**Phase:** 6A (Post-Migration Enhancement)
**Branch:** `migration/flask-port`
**Prerequisite:** Phase 5 complete — Flask app running with 14 blueprints, 74 routes, 260 tests at 94% coverage. Migration 005 applied (SubmissionStateTransition, new Submission columns, new SubmissionStatus values, SkillVersion.submission_id).
**Outcome:** Revision tracking, enhanced decision modals, submission card improvements, audit log panel, and post-approval versioning.
**Exit Gate:** All new tests green, coverage >= 80%, no ruff/mypy/eslint errors.

---

## Conventions Used in This Guide

- **SEARCH** = read the referenced file to understand current implementation
- **CREATE** = write a new file
- **MODIFY** = edit an existing file
- **TEST RED** = run tests and confirm they fail (TDD red phase)
- **TEST GREEN** = run tests and confirm they pass (TDD green phase)
- **VERIFY** = run a command and check its output matches expectations

All file paths are relative to the repository root: `/Users/chase/wk/marketplace-ai`

### Key File Locations

| What | Path |
|------|------|
| ORM Models | `libs/db/skillhub_db/models/` |
| Services (shared) | `apps/fast-api/skillhub/services/` |
| Pydantic Schemas | `apps/fast-api/skillhub/schemas/` |
| Flask Blueprints | `apps/api/skillhub_flask/blueprints/` |
| Flask Auth | `apps/api/skillhub_flask/auth.py` |
| Backend Tests | `apps/api/tests/` |
| Test Conftest | `apps/api/tests/conftest.py` |
| React Components | `apps/web/src/components/` |
| React Views | `apps/web/src/views/` |
| React Hooks | `apps/web/src/hooks/` |
| Feature Index | `docs/features/index.md` |
| PYTHONPATH | `apps/api:apps/fast-api:libs/db:libs/python-common` |

### Pattern Reference

```python
# Flask blueprint route
@bp.route("/api/v1/some/path", methods=["POST"])
@require_platform_team  # from skillhub_flask.auth
def my_endpoint() -> tuple:
    db = get_db()
    current_user: dict[str, Any] = g.current_user
    user_id = uuid.UUID(current_user["user_id"])
    body = MyRequestSchema(**request.get_json(force=True))
    # ... call service ...
    return jsonify(ResponseSchema(**result).model_dump(mode="json")), 200
```

```python
# Test pattern
def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

def _platform_token(**extra: Any) -> str:
    payload = {
        "sub": "admin-user",
        "user_id": str(uuid.uuid4()),
        "division": "platform",
        "is_platform_team": True,
    }
    payload.update(extra)
    return make_token(payload=payload)
```

```typescript
// React test pattern (Vitest)
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../../../context/ThemeContext';

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>{children}</ThemeProvider>
    </MemoryRouter>
  );
}
```

### Existing State Machine

Current `SubmissionStatus` enum values (from `libs/db/skillhub_db/models/submission.py`):

```
SUBMITTED -> GATE1_PASSED | GATE1_FAILED
GATE1_PASSED -> GATE2_PASSED | GATE2_FLAGGED | GATE2_FAILED
GATE2_PASSED -> APPROVED | REJECTED | GATE3_CHANGES_REQUESTED
GATE2_FLAGGED -> APPROVED | REJECTED | GATE3_CHANGES_REQUESTED
GATE3_CHANGES_REQUESTED -> REVISION_PENDING (via resubmit)
CHANGES_REQUESTED -> REVISION_PENDING (via resubmit)
REVISION_PENDING -> GATE1_PASSED | GATE1_FAILED (re-run gates)
APPROVED -> PUBLISHED (via versioning)
```

### Existing Models Already in Place (DO NOT RECREATE)

These were added in Phase 6 DB prep (migration 005):

- `Submission.revision_number` (Integer, default=1)
- `Submission.content_hash` (String(64), nullable, indexed)
- `Submission.parent_submission_id` (FK to submissions.id, nullable)
- `Submission.target_skill_id` (FK to skills.id, nullable)
- `Submission.rejection_category` (String(50), nullable)
- `Submission.change_request_flags` (JSON, nullable)
- `Submission.submitted_via` (String(20), default="form")
- `SubmissionStateTransition` model (full table with submission_id, from_status, to_status, actor_id, notes, diff_snapshot, change_flags_resolved)
- `SkillVersion.submission_id` (FK to submissions.id, nullable)

---

## Prompt A.2.1 — Revision Tracking Service

**Time estimate:** 30-40 minutes
**What:** Create `resubmit_submission()` service function with state machine validation.

### DO NOT

- Create new migrations or modify ORM models — migration 005 already exists
- Touch `create_submission()` or `review_submission()` — those already work
- Import from `apps/api` in service code — services live in `apps/fast-api`
- Use `print()` — use `logger` from the `logging` module

### Steps

#### 1. TEST RED — Write service tests

**CREATE** `apps/api/tests/test_resubmit_service.py`

Write tests for a new function `resubmit_submission()` that will live in `apps/fast-api/skillhub/services/submissions.py`.

Test cases (each is a separate test function):

1. **test_resubmit_from_changes_requested** — submission with status `CHANGES_REQUESTED`, new content provided. Asserts:
   - Returns dict with `id`, `display_id`, `status` = `"gate1_passed"` or `"gate1_failed"` (depending on gate1 result)
   - `revision_number` incremented to 2
   - `content_hash` is set (SHA-256 hex of new content)
   - A `SubmissionStateTransition` row was created with `from_status="changes_requested"`, `to_status` matching new status, and `diff_snapshot` containing old/new content

2. **test_resubmit_from_gate3_changes_requested** — same as above but starting status is `GATE3_CHANGES_REQUESTED`. Asserts same outcomes.

3. **test_resubmit_invalid_status_raises** — submission with status `SUBMITTED`. Asserts `ValueError` is raised with message containing "not in a resubmittable state".

4. **test_resubmit_wrong_user_raises** — submission owned by user A, resubmit called by user B. Asserts `PermissionError` is raised.

5. **test_resubmit_skips_gate2_when_hash_unchanged** — resubmit with identical content (same hash). Asserts:
   - Gate 1 re-runs (always)
   - No Gate 2 scan is triggered (return value has `gate2_skipped: True`)

6. **test_resubmit_triggers_gate2_when_hash_changed** — resubmit with different content. Asserts:
   - Gate 1 re-runs
   - Return value has `gate2_skipped: False`

7. **test_resubmit_increments_revision_number_correctly** — submission already at revision 3, resubmit bumps to 4.

8. **test_resubmit_records_audit_log** — after resubmit, an `AuditLog` entry exists with `event_type="submission.resubmitted"`.

**Test setup pattern:**
```python
from unittest.mock import MagicMock, patch, PropertyMock
import uuid
import hashlib
from datetime import datetime, timezone

# Mock the db session. Use mock_db.query().filter().first() chaining.
# For Submission, set attributes directly on MagicMock instances:
#   mock_sub = MagicMock()
#   mock_sub.id = uuid.uuid4()
#   mock_sub.submitted_by = user_id
#   mock_sub.status = SubmissionStatus.CHANGES_REQUESTED
#   mock_sub.content = "old content"
#   mock_sub.revision_number = 1
#   mock_sub.content_hash = hashlib.sha256(b"old content").hexdigest()
```

**VERIFY:** `cd apps/api && python -m pytest tests/test_resubmit_service.py -x` — all tests FAIL (function does not exist yet).

#### 2. Implement `resubmit_submission()`

**MODIFY** `apps/fast-api/skillhub/services/submissions.py`

Add a new function after `review_submission()`:

```python
def resubmit_submission(
    db: Session,
    *,
    submission_id: UUID,
    user_id: UUID,
    new_content: str,
    new_short_desc: str | None = None,
) -> dict[str, Any]:
    """Resubmit a submission after changes were requested.

    Valid precondition statuses: CHANGES_REQUESTED, GATE3_CHANGES_REQUESTED.
    Increments revision_number, computes content_hash, stores diff in
    SubmissionStateTransition, re-runs Gate 1 always, Gate 2 only if
    content_hash changed.
    """
```

Implementation requirements:

1. Load submission by `submission_id`. Raise `ValueError("Submission not found")` if missing.
2. Check `submission.submitted_by == user_id`. Raise `PermissionError("Not authorized to resubmit")` if mismatch.
3. Check `submission.status` is in `{SubmissionStatus.CHANGES_REQUESTED, SubmissionStatus.GATE3_CHANGES_REQUESTED}`. Raise `ValueError(f"Submission is not in a resubmittable state: {current_status}")` otherwise.
4. Store old values: `old_content = submission.content`, `old_hash = submission.content_hash`, `old_status = submission.status.value`.
5. Compute `new_hash = hashlib.sha256(new_content.encode()).hexdigest()`.
6. Update submission:
   - `submission.content = new_content`
   - `submission.content_hash = new_hash`
   - `submission.revision_number += 1`
   - `submission.status = SubmissionStatus.REVISION_PENDING`
   - If `new_short_desc` provided, update `submission.short_desc`
7. Create `SubmissionStateTransition`:
   - `from_status=old_status`
   - `to_status="revision_pending"`
   - `actor_id=user_id`
   - `notes=f"Revision {submission.revision_number} submitted"`
   - `diff_snapshot={"old_content": old_content[:2000], "new_content": new_content[:2000], "old_hash": old_hash, "new_hash": new_hash}`
8. Run Gate 1: call `run_gate1(db, new_content, submission.short_desc)`.
9. Update status based on Gate 1 result. Create `SubmissionGateResult` for gate 1.
10. Determine `gate2_skipped`: `True` if `new_hash == old_hash`, else `False`.
11. Write audit log with `event_type="submission.resubmitted"`.
12. `db.commit()` and `db.refresh(submission)`.
13. Return dict:
    ```python
    {
        "id": submission.id,
        "display_id": submission.display_id,
        "status": submission.status.value,
        "revision_number": submission.revision_number,
        "content_hash": new_hash,
        "gate1_result": {"gate": 1, "result": gate1_result.value, "findings": gate1_findings or None, "score": None},
        "gate2_skipped": gate2_skipped,
    }
    ```

Use the `tracer` and `_write_audit` helper already defined in the file. Add `import hashlib` at the top and import `SubmissionStateTransition` from `skillhub_db.models.submission`.

**VERIFY:** `cd apps/api && python -m pytest tests/test_resubmit_service.py -x` — all 8 tests GREEN.

#### 3. Add `get_audit_trail()` service function

**MODIFY** `apps/fast-api/skillhub/services/submissions.py`

Add after `resubmit_submission()`:

```python
def get_audit_trail(
    db: Session,
    *,
    submission_id: UUID,
    user_id: UUID,
    is_platform_team: bool = False,
) -> list[dict[str, Any]]:
    """Get the state transition history for a submission.

    Returns list of transition dicts ordered by created_at ascending.
    Only submission owner or platform team can view.
    """
```

Implementation:
1. Load submission. Raise `ValueError` if not found.
2. Check ownership or `is_platform_team`. Raise `PermissionError` if unauthorized.
3. Query `SubmissionStateTransition` filtered by `submission_id`, ordered by `created_at ASC`.
4. Batch-resolve actor names from `User` table.
5. Return list of dicts with: `id`, `from_status`, `to_status`, `actor_id`, `actor_name`, `notes`, `diff_snapshot` (only if `is_platform_team`), `created_at`.

#### 4. Add `get_transition_diff()` service function

**MODIFY** `apps/fast-api/skillhub/services/submissions.py`

```python
def get_transition_diff(
    db: Session,
    *,
    transition_id: UUID,
) -> dict[str, Any] | None:
    """Get the diff snapshot for a specific state transition. Platform team only (enforced at route level)."""
```

Implementation: Load `SubmissionStateTransition` by id. Return `{"id": ..., "diff_snapshot": ..., "from_status": ..., "to_status": ..., "created_at": ...}` or `None`.

#### 5. Add `get_submission_by_display_id()` helper

**MODIFY** `apps/fast-api/skillhub/services/submissions.py`

```python
def get_submission_by_display_id(
    db: Session,
    display_id: str,
) -> Submission | None:
    """Look up a submission by its display_id (e.g., SKL-ABC123)."""
    return db.query(Submission).filter(Submission.display_id == display_id).first()
```

#### 6. VERIFY all existing tests still pass

**VERIFY:** `cd apps/api && python -m pytest --tb=short -q` — all tests GREEN, no regressions.

### Acceptance Criteria

- [ ] `resubmit_submission()` accepts `CHANGES_REQUESTED` and `GATE3_CHANGES_REQUESTED` as valid preconditions
- [ ] `revision_number` increments by 1 on each resubmit
- [ ] `content_hash` is SHA-256 hex of new content
- [ ] `SubmissionStateTransition` row created with `diff_snapshot`
- [ ] Gate 1 always re-runs
- [ ] Gate 2 skipped when content hash unchanged, flagged for re-run otherwise
- [ ] Ownership check enforced (PermissionError if wrong user)
- [ ] Invalid status raises ValueError
- [ ] AuditLog entry created
- [ ] `get_audit_trail()` returns transitions ordered by `created_at ASC`
- [ ] `get_transition_diff()` returns diff snapshot for a transition ID
- [ ] `get_submission_by_display_id()` returns Submission or None
- [ ] All 8+ new tests pass, zero regressions

---

## Prompt A.2.2 — Resubmit & Audit Log Flask Endpoints

**Time estimate:** 25-35 minutes
**What:** Wire the new service functions to Flask routes.

### DO NOT

- Modify any service functions — they are done
- Create new services — only add blueprint routes
- Skip auth checks — all endpoints require authentication
- Use `async def` — Flask routes are synchronous

### Steps

#### 1. Add new Pydantic schemas

**MODIFY** `apps/fast-api/skillhub/schemas/submission.py`

Add these schemas:

```python
class ResubmitRequest(BaseModel):
    """Request body for resubmitting a submission."""
    content: str = Field(..., min_length=1, description="Updated SKILL.md text")
    short_desc: str | None = Field(None, max_length=255)


class ResubmitResponse(BaseModel):
    """Response after resubmitting."""
    id: UUID
    display_id: str
    status: str
    revision_number: int
    content_hash: str
    gate1_result: GateResultResponse
    gate2_skipped: bool


class AuditTrailEntry(BaseModel):
    """A single entry in the submission audit trail."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_status: str
    to_status: str
    actor_id: UUID
    actor_name: str | None = None
    notes: str | None = None
    diff_snapshot: dict | None = None
    created_at: datetime | str


class AuditTrailResponse(BaseModel):
    """Audit trail for a submission."""
    submission_id: UUID
    display_id: str
    entries: list[AuditTrailEntry]


class TransitionDiffResponse(BaseModel):
    """Diff snapshot for a single state transition."""
    id: UUID
    from_status: str
    to_status: str
    diff_snapshot: dict | None = None
    created_at: datetime | str
```

#### 2. TEST RED — Write endpoint tests

**CREATE** `apps/api/tests/test_resubmit_endpoints.py`

Test cases:

1. **test_resubmit_success** — POST `/api/v1/submissions/SKL-ABC123/resubmit` with valid token (submission owner) and valid body. Mock `get_submission_by_display_id` to return a submission, mock `resubmit_submission` to return a result dict. Assert 200 and correct response shape.

2. **test_resubmit_not_found** — display_id that returns None from lookup. Assert 404.

3. **test_resubmit_permission_error** — `resubmit_submission` raises `PermissionError`. Assert 403.

4. **test_resubmit_invalid_state** — `resubmit_submission` raises `ValueError`. Assert 400 (or 409 if you prefer conflict semantics; use 400 for consistency).

5. **test_resubmit_no_auth** — no Authorization header. Assert 401.

6. **test_audit_log_success** — GET `/api/v1/submissions/SKL-ABC123/audit-log` with owner token. Mock service. Assert 200 with entries list.

7. **test_audit_log_platform_team** — same endpoint with platform team token. Assert 200.

8. **test_audit_log_forbidden** — different user, not platform team. Assert 403.

9. **test_diff_success** — GET `/api/v1/submissions/SKL-ABC123/diff?transition_id=<uuid>` with platform team token. Mock `get_transition_diff`. Assert 200.

10. **test_diff_requires_platform_team** — same endpoint with regular user token. Assert 403.

11. **test_diff_not_found** — transition_id returns None. Assert 404.

**Test pattern — mock services with `@patch`:**
```python
@patch("skillhub_flask.blueprints.submissions.get_submission_by_display_id")
@patch("skillhub_flask.blueprints.submissions.resubmit_submission")
def test_resubmit_success(mock_resubmit, mock_lookup, client):
    mock_sub = MagicMock()
    mock_sub.id = uuid.uuid4()
    mock_sub.submitted_by = uuid.UUID(USER_ID)
    mock_lookup.return_value = mock_sub
    mock_resubmit.return_value = { ... }
    # ...
```

**VERIFY:** `cd apps/api && python -m pytest tests/test_resubmit_endpoints.py -x` — all FAIL.

#### 3. Add routes to the submissions blueprint

**MODIFY** `apps/api/skillhub_flask/blueprints/submissions.py`

Add these imports at the top (alongside existing ones):

```python
from skillhub.schemas.submission import (
    # ... existing imports ...
    ResubmitRequest,
    ResubmitResponse,
    AuditTrailEntry,
    AuditTrailResponse,
    TransitionDiffResponse,
)
from skillhub.services.submissions import (
    # ... existing imports ...
    resubmit_submission,
    get_audit_trail,
    get_transition_diff,
    get_submission_by_display_id,
)
```

Add three new routes:

**POST** `/api/v1/submissions/<display_id>/resubmit`
- Auth: any authenticated user (ownership checked in service)
- Parse body as `ResubmitRequest`
- Look up submission via `get_submission_by_display_id(db, display_id)`
- If not found, return 404
- Call `resubmit_submission(db, submission_id=sub.id, user_id=user_id, new_content=body.content, new_short_desc=body.short_desc)`
- Catch `PermissionError` -> 403, `ValueError` -> 400
- Return `ResubmitResponse(**result).model_dump(mode="json")`, 200

**GET** `/api/v1/submissions/<display_id>/audit-log`
- Auth: any authenticated user (ownership checked in service)
- Look up submission via `get_submission_by_display_id`
- If not found, return 404
- Call `get_audit_trail(db, submission_id=sub.id, user_id=user_id, is_platform_team=is_platform_team)`
- Catch `PermissionError` -> 403
- Return `AuditTrailResponse(submission_id=sub.id, display_id=sub.display_id, entries=[AuditTrailEntry(**e) for e in entries]).model_dump(mode="json")`, 200

**GET** `/api/v1/submissions/<display_id>/diff`
- Auth: `@require_platform_team`
- Query param: `transition_id` (required, UUID)
- Call `get_transition_diff(db, transition_id=t_uuid)`
- If None, return 404
- Return `TransitionDiffResponse(**result).model_dump(mode="json")`, 200

#### 4. TEST GREEN

**VERIFY:** `cd apps/api && python -m pytest tests/test_resubmit_endpoints.py -x` — all 11 tests GREEN.

**VERIFY:** `cd apps/api && python -m pytest --tb=short -q` — full suite GREEN, no regressions.

### Acceptance Criteria

- [ ] POST `/api/v1/submissions/{display_id}/resubmit` returns 200 on success
- [ ] GET `/api/v1/submissions/{display_id}/audit-log` returns 200 with entries
- [ ] GET `/api/v1/submissions/{display_id}/diff` returns 200 with diff_snapshot (platform team only)
- [ ] Correct HTTP error codes: 401 (no auth), 403 (forbidden), 404 (not found), 400 (invalid state)
- [ ] All display_id-based lookups use `get_submission_by_display_id()`
- [ ] diff endpoint requires `@require_platform_team`
- [ ] All 11+ new tests pass, zero regressions
- [ ] Schemas validate request/response shapes

---

## Prompt A.3.1 — Extract ModalShell Component

**Time estimate:** 15-20 minutes
**What:** Refactor `AdminConfirmDialog` to extract a reusable `ModalShell` component.

### DO NOT

- Change the visual appearance of the existing `AdminConfirmDialog`
- Remove or rename `AdminConfirmDialog` — other code depends on it
- Add any new npm dependencies
- Use `console.log()` in production code

### Steps

#### 1. TEST RED — Write ModalShell unit tests

**CREATE** `apps/web/src/components/admin/__tests__/ModalShell.test.tsx`

Test cases:

1. **renders with title and children** — renders `<ModalShell title="Test Title"><p>body</p></ModalShell>`. Assert heading text and child content visible.
2. **calls onClose when backdrop clicked** — click the overlay. Assert `onClose` spy called once.
3. **calls onClose on Escape key** — fire Escape keydown. Assert `onClose` called.
4. **does not propagate clicks from inner content** — click inside the dialog. Assert `onClose` NOT called.
5. **renders destructive gradient when destructive=true** — assert visual variant (test via data attribute or snapshot).
6. **renders children in the body area** — custom children render inside the dialog body.
7. **applies aria attributes** — assert `role="dialog"`, `aria-modal="true"`, `aria-labelledby` present.

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { ModalShell } from '../ModalShell';

function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
}
```

**VERIFY:** `cd apps/web && npx vitest run src/components/admin/__tests__/ModalShell.test.tsx` — all FAIL.

#### 2. CREATE the ModalShell component

**CREATE** `apps/web/src/components/admin/ModalShell.tsx`

Extract the overlay + dialog chrome from `AdminConfirmDialog`:

```typescript
import { useRef, type ReactNode } from 'react';
import { useT } from '../../context/ThemeContext';
import { useFocusTrap } from '../../hooks/useFocusTrap';

interface ModalShellProps {
  title: string;
  onClose: () => void;
  destructive?: boolean;
  width?: string;
  children: ReactNode;
}

export function ModalShell({
  title,
  onClose,
  destructive = false,
  width = '420px',
  children,
}: ModalShellProps) {
  const C = useT();
  const dialogRef = useRef<HTMLDivElement>(null);
  useFocusTrap(dialogRef, { onEscape: onClose });

  return (
    <div
      data-testid="modal-shell"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-shell-title"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(4,8,16,0.85)',
        backdropFilter: 'blur(10px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: C.surface,
          border: `1px solid ${C.borderHi}`,
          borderRadius: '18px',
          width,
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: C.cardShadow,
        }}
      >
        <div
          style={{
            height: '3px',
            background: destructive
              ? `linear-gradient(90deg,${C.red},${C.amber})`
              : `linear-gradient(90deg,${C.accent},${C.purple},${C.green})`,
          }}
        />
        <div style={{ padding: '28px' }}>
          <h2
            id="modal-shell-title"
            style={{
              fontSize: '17px',
              fontWeight: 700,
              color: C.text,
              margin: '0 0 12px 0',
            }}
          >
            {title}
          </h2>
          {children}
        </div>
      </div>
    </div>
  );
}
```

#### 3. Refactor AdminConfirmDialog to use ModalShell

**MODIFY** `apps/web/src/components/admin/AdminConfirmDialog.tsx`

Replace the internal markup with:

```typescript
import { ModalShell } from './ModalShell';
import { useT } from '../../context/ThemeContext';

interface Props {
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  destructive?: boolean;
}

export function AdminConfirmDialog({
  title,
  message,
  confirmLabel = 'Confirm',
  onConfirm,
  onCancel,
  destructive = false,
}: Props) {
  const C = useT();
  const accentColor = destructive ? C.red : C.accent;

  return (
    <ModalShell title={title} onClose={onCancel} destructive={destructive}>
      <div data-testid="admin-confirm-dialog">
        <p
          style={{
            fontSize: '14px',
            color: C.muted,
            margin: '0 0 24px 0',
            lineHeight: '1.5',
          }}
        >
          {message}
        </p>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            autoFocus={destructive}
            style={{
              padding: '8px 18px',
              borderRadius: '8px',
              border: `1px solid ${C.border}`,
              background: C.bg,
              color: C.text,
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            autoFocus={!destructive}
            style={{
              padding: '8px 18px',
              borderRadius: '8px',
              border: 'none',
              background: accentColor,
              color: '#fff',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </ModalShell>
  );
}
```

#### 4. TEST GREEN

**VERIFY:** `cd apps/web && npx vitest run src/components/admin/__tests__/ModalShell.test.tsx` — all 7 tests GREEN.

**VERIFY:** `cd apps/web && npx vitest run src/components/admin/__tests__/AdminConfirmDialog.test.tsx` — existing tests still GREEN (no regression).

**VERIFY:** `cd apps/web && npx vitest run src/views/admin/__tests__/AdminQueueView.test.tsx` — still GREEN.

### Acceptance Criteria

- [ ] `ModalShell` renders overlay, dialog chrome, title, and children
- [ ] `ModalShell` calls `onClose` on backdrop click and Escape key
- [ ] `ModalShell` supports `destructive` gradient variant
- [ ] `AdminConfirmDialog` uses `ModalShell` internally — no visual change
- [ ] All existing `AdminConfirmDialog` tests pass without modification
- [ ] All existing `AdminQueueView` tests pass without modification
- [ ] 7+ new ModalShell tests pass

---

## Prompt A.3.2 — RequestChangesModal Component

**Time estimate:** 20-30 minutes
**What:** Create a `RequestChangesModal` with flag checkboxes and free text.

### DO NOT

- Modify `ModalShell` or `AdminConfirmDialog`
- Add new npm dependencies
- Hard-code flag labels — use a constant array that is easy to extend

### Steps

#### 1. TEST RED — Write RequestChangesModal tests

**CREATE** `apps/web/src/components/admin/__tests__/RequestChangesModal.test.tsx`

Test cases:

1. **renders title and all flag checkboxes** — Assert "Request Changes" heading. Assert checkboxes for: "Content quality", "Trigger phrases", "Division justification", "Security concerns", "Naming/slug".
2. **renders free-text notes textarea** — Assert textarea with placeholder.
3. **submit button disabled when no flags selected and no notes** — Assert button is disabled.
4. **submit button enabled when at least one flag checked** — Check a box. Assert button enabled.
5. **submit button enabled when notes provided** — Type in textarea. Assert button enabled.
6. **calls onSubmit with selected flags and notes** — Check two flags, type notes, click Submit. Assert `onSubmit` called with `{ flags: ["content_quality", "trigger_phrases"], notes: "fix this" }`.
7. **calls onCancel when Cancel clicked** — Assert `onCancel` spy called.
8. **calls onCancel on Escape** — Press Escape. Assert `onCancel` called (inherited from ModalShell).

**VERIFY:** Tests FAIL (component does not exist).

#### 2. CREATE the component

**CREATE** `apps/web/src/components/admin/RequestChangesModal.tsx`

```typescript
import { useState } from 'react';
import { ModalShell } from './ModalShell';
import { useT } from '../../context/ThemeContext';

const CHANGE_FLAGS = [
  { key: 'content_quality', label: 'Content quality' },
  { key: 'trigger_phrases', label: 'Trigger phrases' },
  { key: 'division_justification', label: 'Division justification' },
  { key: 'security_concerns', label: 'Security concerns' },
  { key: 'naming_slug', label: 'Naming/slug' },
] as const;

interface RequestChangesResult {
  flags: string[];
  notes: string;
}

interface Props {
  skillName: string;
  onSubmit: (result: RequestChangesResult) => void;
  onCancel: () => void;
}

export function RequestChangesModal({ skillName, onSubmit, onCancel }: Props) {
  // Implementation: state for checked flags (Set<string>) and notes (string)
  // Render ModalShell with title="Request Changes"
  // Render each flag as a labeled checkbox
  // Render a textarea for notes
  // Submit button disabled if flags.size === 0 && notes.trim() === ''
  // On submit, call onSubmit({ flags: [...selectedFlags], notes })
}
```

Implement the full component. Use `useT()` for all colors. Style checkboxes with accent color. Use `data-testid="flag-{key}"` on each checkbox for testing.

#### 3. TEST GREEN

**VERIFY:** `cd apps/web && npx vitest run src/components/admin/__tests__/RequestChangesModal.test.tsx` — all 8 tests GREEN.

### Acceptance Criteria

- [ ] Renders all 5 flag checkboxes with labels
- [ ] Renders notes textarea
- [ ] Submit disabled when no flags and no notes
- [ ] Submit enabled when at least one flag checked OR notes non-empty
- [ ] `onSubmit` receives `{ flags: string[], notes: string }`
- [ ] Cancel and Escape both trigger `onCancel`
- [ ] Uses `ModalShell` for chrome (not duplicating overlay logic)
- [ ] All 8 tests pass

---

## Prompt A.3.3 — RejectModal Component

**Time estimate:** 15-25 minutes
**What:** Create a `RejectModal` with reason dropdown and free text.

### DO NOT

- Modify existing modals
- Add npm dependencies
- Skip the "Other" option in the dropdown

### Steps

#### 1. TEST RED — Write RejectModal tests

**CREATE** `apps/web/src/components/admin/__tests__/RejectModal.test.tsx`

Test cases:

1. **renders title with skill name** — Assert "Reject" in heading.
2. **renders reason dropdown with all options** — Assert options: "Duplicate skill", "Low quality", "Security risk", "Out of scope", "Other".
3. **renders notes textarea** — Assert textarea present.
4. **submit disabled when no reason selected** — Default state. Assert disabled.
5. **submit enabled when reason selected** — Select a reason. Assert enabled.
6. **when "Other" selected, notes become required** — Select "Other", leave notes empty. Assert submit disabled. Type notes. Assert enabled.
7. **calls onSubmit with reason and notes** — Select "Low quality", type notes, click Reject. Assert `onSubmit({ reason: "low_quality", notes: "..." })`.
8. **calls onCancel when Cancel clicked** — Assert spy called.

**VERIFY:** Tests FAIL.

#### 2. CREATE the component

**CREATE** `apps/web/src/components/admin/RejectModal.tsx`

```typescript
import { useState } from 'react';
import { ModalShell } from './ModalShell';
import { useT } from '../../context/ThemeContext';

const REJECTION_REASONS = [
  { value: '', label: 'Select a reason...' },
  { value: 'duplicate', label: 'Duplicate skill' },
  { value: 'low_quality', label: 'Low quality' },
  { value: 'security_risk', label: 'Security risk' },
  { value: 'out_of_scope', label: 'Out of scope' },
  { value: 'other', label: 'Other' },
] as const;

interface RejectResult {
  reason: string;
  notes: string;
}

interface Props {
  skillName: string;
  onSubmit: (result: RejectResult) => void;
  onCancel: () => void;
}

export function RejectModal({ skillName, onSubmit, onCancel }: Props) {
  // Implementation: state for selectedReason and notes
  // ModalShell with title="Reject Submission", destructive=true
  // Select dropdown for reason
  // Textarea for notes
  // Submit disabled if no reason, or if reason is "other" and notes empty
  // Submit button label: "Reject"
  // Submit button in red (C.red background)
}
```

#### 3. TEST GREEN

**VERIFY:** `cd apps/web && npx vitest run src/components/admin/__tests__/RejectModal.test.tsx` — all 8 tests GREEN.

### Acceptance Criteria

- [ ] Renders reason dropdown with 5 options + placeholder
- [ ] Renders notes textarea
- [ ] Submit disabled when no reason selected
- [ ] When "Other" selected, notes are required for submit
- [ ] `onSubmit` receives `{ reason: string, notes: string }`
- [ ] Uses `ModalShell` with `destructive=true`
- [ ] Cancel triggers `onCancel`
- [ ] All 8 tests pass

---

## Prompt A.4.1 — Enhanced SubmissionCard Component

**Time estimate:** 20-30 minutes
**What:** Create an enhanced `SubmissionCard` with "Requested By" user info and a `RevisionBadge`.

### DO NOT

- Modify `AdminQueueView` yet — that is prompt A.4.2
- Fetch data — the card receives all data via props
- Use `console.log()`

### Steps

#### 1. TEST RED — Write SubmissionCard tests

**CREATE** `apps/web/src/components/admin/__tests__/SubmissionCard.test.tsx`

Test cases:

1. **renders skill name and display_id** — Assert both visible.
2. **renders submitter name and "Requested By" label** — Assert "Requested by Alice Smith".
3. **renders category badge** — Assert category text visible.
4. **renders RevisionBadge when revision > 1** — Pass `revision_number: 3`. Assert "Rev 3" badge visible.
5. **does not render RevisionBadge when revision is 1** — Pass `revision_number: 1`. Assert no revision badge.
6. **renders SLA badge when wait > 24h** — Pass `wait_time_hours: 30`. Assert "SLA at risk" visible.
7. **renders SLA breached badge when wait > 48h** — Pass `wait_time_hours: 50`. Assert "SLA breached".
8. **calls onClick when clicked** — Assert spy called with `submission_id`.
9. **renders selected state** — Pass `selected=true`. Assert visual indicator (check background or `aria-selected`).
10. **renders divisions chips** — Pass `divisions: ["eng", "sec"]`. Assert both visible.

**Test props shape:**
```typescript
const defaultProps = {
  submission_id: 'sub-1',
  display_id: 'SKL-001',
  skill_name: 'Code Reviewer',
  short_desc: 'Automated code review',
  category: 'development',
  submitter_name: 'Alice Smith',
  submitted_at: new Date().toISOString(),
  wait_time_hours: 2,
  divisions: ['engineering'],
  revision_number: 1,
  selected: false,
  onClick: vi.fn(),
};
```

**VERIFY:** Tests FAIL.

#### 2. CREATE RevisionBadge

**CREATE** `apps/web/src/components/admin/RevisionBadge.tsx`

A small inline badge component:

```typescript
import { useT } from '../../context/ThemeContext';

interface Props {
  revision: number;
}

export function RevisionBadge({ revision }: Props) {
  const C = useT();
  if (revision <= 1) return null;
  return (
    <span
      data-testid="revision-badge"
      style={{
        fontSize: '10px',
        fontWeight: 600,
        padding: '2px 8px',
        borderRadius: '99px',
        background: C.amberDim,
        color: C.amber,
      }}
    >
      Rev {revision}
    </span>
  );
}
```

#### 3. CREATE SubmissionCard

**CREATE** `apps/web/src/components/admin/SubmissionCard.tsx`

```typescript
import { useT } from '../../context/ThemeContext';
import { RevisionBadge } from './RevisionBadge';

interface SubmissionCardProps {
  submission_id: string;
  display_id: string;
  skill_name: string;
  short_desc: string;
  category: string;
  submitter_name: string | null;
  submitted_at: string | null;
  wait_time_hours: number;
  divisions: string[];
  revision_number: number;
  selected: boolean;
  onClick: (id: string) => void;
}

export function SubmissionCard(props: SubmissionCardProps) {
  // Render a button-based card:
  // - Top row: skill_name + RevisionBadge + SLA badge
  // - Second row: "Requested by {submitter_name}" + category badge
  // - If selected, use C.accentDim background
  // - aria-selected={selected}
  // - data-testid="submission-card"
}
```

#### 4. TEST GREEN

**VERIFY:** `cd apps/web && npx vitest run src/components/admin/__tests__/SubmissionCard.test.tsx` — all 10 tests GREEN.

### Acceptance Criteria

- [ ] `SubmissionCard` renders skill name, display_id, submitter name, category, divisions
- [ ] `RevisionBadge` shows "Rev N" when revision > 1, hidden when revision is 1
- [ ] SLA badges show at 24h and 48h thresholds
- [ ] Selected state visually distinct
- [ ] `onClick` fires with `submission_id`
- [ ] `aria-selected` attribute set correctly
- [ ] All 10 tests pass

---

## Prompt A.4.2 — Integrate SubmissionCard into AdminQueueView

**Time estimate:** 15-20 minutes
**What:** Replace inline card markup in `AdminQueueView` with the new `SubmissionCard` component. Wire `RequestChangesModal` and `RejectModal` to the decision flow.

### DO NOT

- Change the queue data fetching logic (useAdminQueue hook)
- Add new API calls — reuse existing `decide` function from the hook
- Break keyboard navigation (j/k/a/r/x)

### Steps

#### 1. TEST RED — Update AdminQueueView tests

**MODIFY** `apps/web/src/views/admin/__tests__/AdminQueueView.test.tsx`

Add new test cases to the existing describe block:

1. **renders SubmissionCard components** — Assert `data-testid="submission-card"` elements appear for each queue item.
2. **opens RequestChangesModal on 'x' keypress** — Select an item, press 'x'. Assert "Request Changes" heading visible.
3. **opens RejectModal on 'r' keypress** — Select an item, press 'r'. Assert "Reject" heading visible.
4. **RequestChangesModal submits with flags** — Open modal, check a flag, type notes, click submit. Assert `decide` mock called with `("sub-1", "request_changes", ...)`.
5. **RejectModal submits with reason** — Open modal, select reason, click Reject. Assert `decide` mock called.

Also update the `ReviewQueueItem` mock data to include `revision_number: 1` (or higher for the second item) since `SubmissionCard` now expects it.

**VERIFY:** New tests FAIL (AdminQueueView still uses inline markup).

#### 2. MODIFY AdminQueueView

**MODIFY** `apps/web/src/views/admin/AdminQueueView.tsx`

Changes:
- Import `SubmissionCard` from `../../components/admin/SubmissionCard`
- Import `RequestChangesModal` from `../../components/admin/RequestChangesModal`
- Import `RejectModal` from `../../components/admin/RejectModal`
- Replace the inline `<button>` cards in the queue list with `<SubmissionCard>` components
- Replace the `AdminConfirmDialog` usage for `request_changes` action with `<RequestChangesModal>`. The modal's `onSubmit` should call `decide(id, "request_changes", JSON.stringify({ flags: result.flags, notes: result.notes }))`.
- Replace the `AdminConfirmDialog` usage for `reject` action with `<RejectModal>`. The modal's `onSubmit` should call `decide(id, "reject", JSON.stringify({ reason: result.reason, notes: result.notes }))`.
- Keep `AdminConfirmDialog` for the `approve` action (it is already fine as a simple confirm).
- Pass `revision_number` to `SubmissionCard`. The `ReviewQueueItem` type in `useAdminQueue.ts` needs updating too.

**MODIFY** `apps/web/src/hooks/useAdminQueue.ts`

Add `revision_number: number;` to the `ReviewQueueItem` interface (default to 1 in the type). The backend `get_review_queue` already returns `revision_number` if available on the Submission model.

#### 3. TEST GREEN

**VERIFY:** `cd apps/web && npx vitest run src/views/admin/__tests__/AdminQueueView.test.tsx` — all tests GREEN (old + new).

**VERIFY:** `cd apps/web && npx vitest run` — full suite GREEN.

#### 4. Update Feature Index

**MODIFY** `docs/features/index.md`

Append:

```markdown
## Enhanced Decision Modals
![Enhanced Decision Modals](assets/decision-modals.gif)
Request Changes modal with flag checkboxes and Reject modal with reason dropdown replace the generic confirmation dialog for nuanced reviewer feedback.

## Submission Card with Revision Badge
![Submission Card](assets/submission-card.gif)
Queue cards now show "Requested By" info, revision badges (Rev 2, Rev 3...), and SLA status indicators.
```

### Acceptance Criteria

- [ ] Queue list uses `SubmissionCard` components (no inline card markup)
- [ ] 'x' key opens `RequestChangesModal` (not generic confirm)
- [ ] 'r' key opens `RejectModal` (not generic confirm)
- [ ] 'a' key still opens `AdminConfirmDialog` for approve
- [ ] j/k keyboard navigation still works
- [ ] `decide()` called with structured JSON for changes_requested and reject
- [ ] `ReviewQueueItem` includes `revision_number`
- [ ] Feature index updated
- [ ] All queue tests pass (old + new), zero regressions

---

## Prompt A.5.1 — AuditLogPanel Component

**Time estimate:** 25-35 minutes
**What:** Build an `AuditLogPanel` component that shows submission state transitions in a conversation-thread style.

### DO NOT

- Fetch data inside AuditLogPanel — it receives entries as props
- Use any date library — use `Intl.DateTimeFormat` or simple relative time
- Add npm dependencies

### Steps

#### 1. TEST RED — Write AuditLogPanel tests

**CREATE** `apps/web/src/components/admin/__tests__/AuditLogPanel.test.tsx`

Test cases:

1. **renders heading "Audit Log"** — Assert heading present.
2. **renders all entries** — Pass 3 entries. Assert 3 entry elements rendered (via `data-testid="audit-entry"`).
3. **renders actor name for each entry** — Assert actor names visible.
4. **renders from/to status transition** — Assert "gate2_passed -> approved" text visible.
5. **renders notes when present** — Entry with notes. Assert notes text visible.
6. **does not render notes when absent** — Entry without notes. Assert notes area not rendered.
7. **renders "View Diff" button when diff_snapshot present** — Assert button visible.
8. **does not render "View Diff" when diff_snapshot absent** — Assert button not present.
9. **calls onViewDiff with transition_id when "View Diff" clicked** — Assert spy called with correct id.
10. **renders entries in chronological order** — Assert first entry is visually at top.
11. **renders empty state when no entries** — Pass empty array. Assert "No audit history" message.
12. **renders relative time for each entry** — Entry from 2 hours ago. Assert some time indicator.

**Entry shape for test data:**
```typescript
const entries = [
  {
    id: 'trans-1',
    from_status: 'submitted',
    to_status: 'gate1_passed',
    actor_id: 'user-1',
    actor_name: 'System',
    notes: null,
    diff_snapshot: null,
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 'trans-2',
    from_status: 'gate2_passed',
    to_status: 'gate3_changes_requested',
    actor_id: 'user-2',
    actor_name: 'Alice Smith',
    notes: 'Please improve trigger phrases',
    diff_snapshot: null,
    created_at: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: 'trans-3',
    from_status: 'gate3_changes_requested',
    to_status: 'revision_pending',
    actor_id: 'user-3',
    actor_name: 'Bob Jones',
    notes: 'Revision 2 submitted',
    diff_snapshot: { old_content: '...', new_content: '...' },
    created_at: new Date().toISOString(),
  },
];
```

**VERIFY:** Tests FAIL.

#### 2. CREATE the component

**CREATE** `apps/web/src/components/admin/AuditLogPanel.tsx`

```typescript
import { useT } from '../../context/ThemeContext';

interface AuditEntry {
  id: string;
  from_status: string;
  to_status: string;
  actor_id: string;
  actor_name: string | null;
  notes: string | null;
  diff_snapshot: Record<string, unknown> | null;
  created_at: string;
}

interface Props {
  entries: AuditEntry[];
  onViewDiff?: (transitionId: string) => void;
}

export function AuditLogPanel({ entries, onViewDiff }: Props) {
  const C = useT();

  // Helper: format relative time
  function relativeTime(iso: string): string {
    const diffMs = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  // Helper: status -> color
  function statusColor(status: string): string {
    if (status.includes('passed') || status === 'approved' || status === 'published') return C.green;
    if (status.includes('failed') || status === 'rejected') return C.red;
    if (status.includes('changes') || status.includes('flagged')) return C.amber;
    return C.muted;
  }

  if (entries.length === 0) {
    return (
      <div data-testid="audit-log-panel">
        <h3 style={{ fontSize: '15px', fontWeight: 700, color: C.text, marginBottom: '12px' }}>
          Audit Log
        </h3>
        <p style={{ color: C.muted, fontSize: '13px' }}>No audit history</p>
      </div>
    );
  }

  return (
    <div data-testid="audit-log-panel">
      <h3 style={{ fontSize: '15px', fontWeight: 700, color: C.text, marginBottom: '12px' }}>
        Audit Log
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
        {entries.map((entry, idx) => (
          <div
            key={entry.id}
            data-testid="audit-entry"
            style={{
              display: 'flex',
              gap: '12px',
              padding: '12px 0',
              borderBottom: idx < entries.length - 1 ? `1px solid ${C.border}` : 'none',
            }}
          >
            {/* Timeline dot + connector */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '20px' }}>
              <div
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: statusColor(entry.to_status),
                  flexShrink: 0,
                }}
              />
              {idx < entries.length - 1 && (
                <div style={{ width: '2px', flex: 1, background: C.border, marginTop: '4px' }} />
              )}
            </div>

            {/* Content */}
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>
                  {entry.actor_name ?? 'Unknown'}
                </span>
                <span style={{ fontSize: '11px', color: C.dim }}>
                  {relativeTime(entry.created_at)}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: C.muted, marginBottom: entry.notes ? '6px' : '0' }}>
                <span style={{ color: statusColor(entry.from_status) }}>{entry.from_status}</span>
                {' -> '}
                <span style={{ color: statusColor(entry.to_status) }}>{entry.to_status}</span>
              </div>
              {entry.notes && (
                <p style={{ fontSize: '12px', color: C.text, margin: '0 0 6px 0', lineHeight: '1.4' }}>
                  {entry.notes}
                </p>
              )}
              {entry.diff_snapshot && onViewDiff && (
                <button
                  onClick={() => onViewDiff(entry.id)}
                  data-testid="view-diff-btn"
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    color: C.accent,
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    cursor: 'pointer',
                    textDecoration: 'underline',
                  }}
                >
                  View Diff
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### 3. TEST GREEN

**VERIFY:** `cd apps/web && npx vitest run src/components/admin/__tests__/AuditLogPanel.test.tsx` — all 12 tests GREEN.

#### 4. Create useAuditLog hook

**CREATE** `apps/web/src/hooks/useAuditLog.ts`

```typescript
import { useState, useCallback } from 'react';
import { api } from '../lib/api';

export interface AuditEntry {
  id: string;
  from_status: string;
  to_status: string;
  actor_id: string;
  actor_name: string | null;
  notes: string | null;
  diff_snapshot: Record<string, unknown> | null;
  created_at: string;
}

interface AuditTrailResponse {
  submission_id: string;
  display_id: string;
  entries: AuditEntry[];
}

export function useAuditLog(displayId: string | null) {
  const [data, setData] = useState<AuditTrailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!displayId) return;
    setLoading(true);
    try {
      const result = await api.get<AuditTrailResponse>(
        `/api/v1/submissions/${displayId}/audit-log`,
      );
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit log');
    } finally {
      setLoading(false);
    }
  }, [displayId]);

  return { data, loading, error, fetch };
}
```

#### 5. Integrate AuditLogPanel into AdminQueueView detail panel

**MODIFY** `apps/web/src/views/admin/AdminQueueView.tsx`

Below the "Divisions" section in the detail panel, add:
- Import `AuditLogPanel` and `useAuditLog`
- Call `useAuditLog(selectedItem?.display_id ?? null)` in the component
- Add a "Load Audit Log" button that calls `auditLog.fetch()`
- When `auditLog.data` exists, render `<AuditLogPanel entries={auditLog.data.entries} onViewDiff={handleViewDiff} />`
- `handleViewDiff` opens the diff in a `ModalShell` (simple JSON display for now)

#### 6. Update Feature Index

**MODIFY** `docs/features/index.md`

Append:

```markdown
## Audit Log Panel
![Audit Log Panel](assets/audit-log-panel.gif)
Conversation-thread style audit trail showing every state transition, reviewer actions, and revision diffs for a submission.
```

#### 7. VERIFY full suite

**VERIFY:** `cd apps/web && npx vitest run` — full suite GREEN.

### Acceptance Criteria

- [ ] AuditLogPanel renders chronological entries with timeline dots
- [ ] Each entry shows actor name, status transition, relative time
- [ ] Notes shown when present, hidden when absent
- [ ] "View Diff" button shown only when diff_snapshot exists
- [ ] onViewDiff callback fires with transition_id
- [ ] Empty state message when no entries
- [ ] useAuditLog hook fetches from `/api/v1/submissions/{displayId}/audit-log`
- [ ] Integrated into AdminQueueView detail panel
- [ ] Feature index updated
- [ ] All 12+ tests pass, zero regressions

---

## Prompt A.6.1 — Post-Approval Versioning Service & Endpoint

**Time estimate:** 30-40 minutes
**What:** Create a service function to version an approved submission into a new SkillVersion, and a Flask endpoint to trigger it.

### DO NOT

- Modify the existing `review_submission()` function's approval flow
- Create new migrations — `SkillVersion.submission_id` already exists
- Skip the content_hash uniqueness check (prevent duplicate versions)

### Steps

#### 1. TEST RED — Write service tests

**CREATE** `apps/api/tests/test_versioning_service.py`

Test cases:

1. **test_version_from_approved_submission** — Submission is `APPROVED`, linked to a skill via `target_skill_id`. Call `version_submission()`. Assert:
   - New `SkillVersion` row created with correct `skill_id`, `version`, `content`, `content_hash`, `submission_id`
   - `Skill.current_version` updated
   - `Submission.status` set to `PUBLISHED`
   - AuditLog entry with `event_type="skill.version_created"`

2. **test_version_invalid_status** — Submission not `APPROVED`. Assert `ValueError`.

3. **test_version_duplicate_hash** — A SkillVersion with the same content_hash already exists for the skill. Assert `ValueError("Duplicate content — version already exists")`.

4. **test_version_no_target_skill** — Submission has no `target_skill_id` and no `skill_id`. Assert `ValueError("No skill linked to this submission")`.

5. **test_version_auto_increment_version** — Skill's current_version is "1.2.0". New version should be "1.3.0" (increment minor). Assert version string.

6. **test_version_records_submission_id** — After versioning, `SkillVersion.submission_id == submission.id`.

**VERIFY:** Tests FAIL.

#### 2. Implement `version_submission()`

**MODIFY** `apps/fast-api/skillhub/services/submissions.py`

Add:

```python
def version_submission(
    db: Session,
    *,
    submission_id: UUID,
    reviewer_id: UUID,
    changelog: str = "",
) -> dict[str, Any]:
    """Create a new SkillVersion from an approved submission.

    The submission must be in APPROVED status and linked to a skill.
    """
```

Implementation:
1. Load submission. Validate status is `APPROVED`.
2. Determine skill: use `submission.target_skill_id` or `submission.skill_id`. Raise ValueError if neither set.
3. Load the Skill. Compute `content_hash = hashlib.sha256(submission.content.encode()).hexdigest()`.
4. Check for duplicate: query `SkillVersion` where `skill_id` and `content_hash` match. Raise if exists.
5. Auto-increment version: parse `skill.current_version` as `major.minor.patch`, increment minor, reset patch to 0. Use simple string split (no semver library).
6. Create `SkillVersion`:
   - `skill_id`, `version` (new version string), `content` (from submission), `frontmatter` (parse via `_parse_frontmatter`), `content_hash`, `changelog`, `submission_id=submission.id`
7. Update `skill.current_version` to new version.
8. Update `submission.status = SubmissionStatus.PUBLISHED`.
9. Create `SubmissionStateTransition` from `approved` to `published`.
10. Write audit log.
11. Commit and return dict with version info.

#### 3. TEST GREEN

**VERIFY:** `cd apps/api && python -m pytest tests/test_versioning_service.py -x` — all 6 tests GREEN.

#### 4. TEST RED — Write endpoint test

**ADD to** `apps/api/tests/test_resubmit_endpoints.py` (or create `apps/api/tests/test_versioning_endpoint.py`):

1. **test_version_endpoint_success** — POST `/api/v1/skills/<skill_id>/versions` with platform team token. Body: `{ "submission_id": "...", "changelog": "..." }`. Mock service. Assert 201.
2. **test_version_endpoint_not_platform_team** — Regular user token. Assert 403.
3. **test_version_endpoint_invalid_submission** — Service raises ValueError. Assert 400.

#### 5. Add Flask endpoint

**MODIFY** `apps/api/skillhub_flask/blueprints/submissions.py`

Add schema:

**MODIFY** `apps/fast-api/skillhub/schemas/submission.py` — add:

```python
class VersionCreateRequest(BaseModel):
    """Request to create a new skill version from an approved submission."""
    submission_id: UUID
    changelog: str = ""

class VersionCreateResponse(BaseModel):
    """Response after creating a version."""
    skill_id: UUID
    version: str
    content_hash: str
    submission_id: UUID
    created_at: datetime | str
```

Add route in the submissions blueprint:

```python
@bp.route("/api/v1/skills/<skill_id>/versions", methods=["POST"])
@require_platform_team
def create_skill_version(skill_id: str) -> tuple:
    """Create a new skill version from an approved submission. Platform team only."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user
    reviewer_id = uuid.UUID(current_user["user_id"])

    body = VersionCreateRequest(**request.get_json(force=True))

    try:
        result = version_submission(
            db,
            submission_id=body.submission_id,
            reviewer_id=reviewer_id,
            changelog=body.changelog,
        )
    except ValueError as e:
        return jsonify({"detail": str(e)}), 400

    return jsonify(VersionCreateResponse(**result).model_dump(mode="json")), 201
```

#### 6. TEST GREEN

**VERIFY:** `cd apps/api && python -m pytest tests/test_versioning_endpoint.py -x` — all 3 tests GREEN.

**VERIFY:** `cd apps/api && python -m pytest --tb=short -q` — full suite GREEN.

### Acceptance Criteria

- [ ] `version_submission()` creates SkillVersion with correct fields
- [ ] `SkillVersion.submission_id` links back to the submission
- [ ] Duplicate content_hash check prevents duplicate versions
- [ ] Version string auto-increments minor version
- [ ] Submission status transitions to PUBLISHED
- [ ] SubmissionStateTransition recorded
- [ ] AuditLog entry created
- [ ] POST `/api/v1/skills/{skill_id}/versions` requires platform team
- [ ] Returns 201 on success, 400 on validation error, 403 if not platform team
- [ ] All 9+ new tests pass, zero regressions

---

## Prompt A.6.2 — VersionSelector & VersionDiffView Components

**Time estimate:** 25-35 minutes
**What:** Create frontend components for selecting and comparing skill versions.

### DO NOT

- Fetch version list inside VersionSelector — it receives versions as props
- Use any diff library — render a simple side-by-side or unified view
- Add npm dependencies

### Steps

#### 1. TEST RED — Write VersionSelector tests

**CREATE** `apps/web/src/components/admin/__tests__/VersionSelector.test.tsx`

Test cases:

1. **renders dropdown with version options** — Pass versions `["1.0.0", "1.1.0", "1.2.0"]`. Assert 3 options.
2. **shows current version as selected** — Pass `current="1.2.0"`. Assert "1.2.0" is selected.
3. **calls onChange when different version selected** — Select "1.0.0". Assert `onChange("1.0.0")` called.
4. **renders version labels** — Assert "v1.0.0", "v1.1.0", "v1.2.0" text.
5. **highlights current version** — Assert "(current)" label on current version.

**VERIFY:** Tests FAIL.

#### 2. CREATE VersionSelector

**CREATE** `apps/web/src/components/admin/VersionSelector.tsx`

```typescript
import { useT } from '../../context/ThemeContext';

interface Props {
  versions: string[];
  current: string;
  selected: string;
  onChange: (version: string) => void;
}

export function VersionSelector({ versions, current, selected, onChange }: Props) {
  const C = useT();
  // Render a styled select dropdown
  // Each option: "v{version}" + "(current)" suffix if it matches current
}
```

#### 3. TEST RED — Write VersionDiffView tests

**CREATE** `apps/web/src/components/admin/__tests__/VersionDiffView.test.tsx`

Test cases:

1. **renders left and right panels** — Assert two panels visible.
2. **renders version labels** — Pass `leftVersion="1.0.0"` and `rightVersion="1.1.0"`. Assert both labels.
3. **renders content in each panel** — Pass `leftContent` and `rightContent`. Assert both visible.
4. **highlights added lines in right panel** — Lines in right not in left. Assert green background styling (via data attribute or class).
5. **highlights removed lines in left panel** — Lines in left not in right. Assert red background.
6. **renders empty state when no content** — Assert "Select versions to compare" message.

**VERIFY:** Tests FAIL.

#### 4. CREATE VersionDiffView

**CREATE** `apps/web/src/components/admin/VersionDiffView.tsx`

```typescript
import { useT } from '../../context/ThemeContext';

interface Props {
  leftVersion: string;
  rightVersion: string;
  leftContent: string;
  rightContent: string;
}

export function VersionDiffView({ leftVersion, rightVersion, leftContent, rightContent }: Props) {
  const C = useT();

  // Simple line-by-line diff:
  const leftLines = leftContent.split('\n');
  const rightLines = rightContent.split('\n');
  const rightSet = new Set(rightLines);
  const leftSet = new Set(leftLines);

  // Render side-by-side panels
  // Left panel: each line. If line not in rightSet, mark as removed (red background).
  // Right panel: each line. If line not in leftSet, mark as added (green background).
  // Use data-testid="diff-added" and data-testid="diff-removed" for testing.
}
```

#### 5. Create useSkillVersions hook

**CREATE** `apps/web/src/hooks/useSkillVersions.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

interface SkillVersionSummary {
  version: string;
  content_hash: string;
  published_at: string;
  changelog: string | null;
}

interface SkillVersionDetail extends SkillVersionSummary {
  content: string;
}

export function useSkillVersions(skillId: string | null) {
  const [versions, setVersions] = useState<SkillVersionSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchVersions = useCallback(async () => {
    if (!skillId) return;
    setLoading(true);
    try {
      const result = await api.get<{ versions: SkillVersionSummary[] }>(
        `/api/v1/skills/${skillId}/versions`,
      );
      setVersions(result.versions);
    } catch {
      // silently fail for now
    } finally {
      setLoading(false);
    }
  }, [skillId]);

  useEffect(() => { fetchVersions(); }, [fetchVersions]);

  const fetchContent = useCallback(async (version: string): Promise<string> => {
    if (!skillId) return '';
    const result = await api.get<SkillVersionDetail>(
      `/api/v1/skills/${skillId}/versions/${version}`,
    );
    return result.content;
  }, [skillId]);

  return { versions, loading, fetchVersions, fetchContent };
}
```

#### 6. TEST GREEN

**VERIFY:** `cd apps/web && npx vitest run src/components/admin/__tests__/VersionSelector.test.tsx` — all 5 tests GREEN.

**VERIFY:** `cd apps/web && npx vitest run src/components/admin/__tests__/VersionDiffView.test.tsx` — all 6 tests GREEN.

#### 7. Update Feature Index

**MODIFY** `docs/features/index.md`

Append:

```markdown
## Version Selector & Diff View
![Version Diff View](assets/version-diff-view.gif)
Compare skill versions side-by-side with added/removed line highlighting. Select any two versions from the dropdown to see what changed.
```

#### 8. VERIFY full suite

**VERIFY:** `cd apps/web && npx vitest run` — full suite GREEN.

**VERIFY:** `cd apps/api && python -m pytest --tb=short -q` — full suite GREEN.

### Acceptance Criteria

- [ ] VersionSelector renders version dropdown with "(current)" label
- [ ] VersionSelector fires onChange with selected version
- [ ] VersionDiffView renders side-by-side panels
- [ ] Added lines highlighted green, removed lines highlighted red
- [ ] Empty state shown when no content
- [ ] useSkillVersions hook fetches from `/api/v1/skills/{id}/versions`
- [ ] Feature index updated
- [ ] All 11+ new component tests pass, zero regressions across entire suite

---

## Final Verification Checklist

After completing all prompts (A.2.1 through A.6.2), run these commands to confirm everything is green:

```bash
# Backend — all tests, coverage check
cd apps/api && python -m pytest --tb=short -q --cov=skillhub_flask --cov-fail-under=80

# Frontend — all tests, coverage check
cd apps/web && npx vitest run --coverage

# Lint
cd apps/fast-api && ruff check skillhub/ && ruff format --check skillhub/
cd apps/api && ruff check skillhub_flask/ && ruff format --check skillhub_flask/
cd apps/web && npx eslint src/ --max-warnings 0

# Type check
cd apps/web && npx tsc --noEmit
```

### Summary of New Files Created

| File | Type |
|------|------|
| `apps/api/tests/test_resubmit_service.py` | Backend test |
| `apps/api/tests/test_resubmit_endpoints.py` | Backend test |
| `apps/api/tests/test_versioning_service.py` | Backend test |
| `apps/api/tests/test_versioning_endpoint.py` | Backend test (optional, can merge) |
| `apps/web/src/components/admin/ModalShell.tsx` | React component |
| `apps/web/src/components/admin/RequestChangesModal.tsx` | React component |
| `apps/web/src/components/admin/RejectModal.tsx` | React component |
| `apps/web/src/components/admin/RevisionBadge.tsx` | React component |
| `apps/web/src/components/admin/SubmissionCard.tsx` | React component |
| `apps/web/src/components/admin/AuditLogPanel.tsx` | React component |
| `apps/web/src/components/admin/VersionSelector.tsx` | React component |
| `apps/web/src/components/admin/VersionDiffView.tsx` | React component |
| `apps/web/src/hooks/useAuditLog.ts` | React hook |
| `apps/web/src/hooks/useSkillVersions.ts` | React hook |
| `apps/web/src/components/admin/__tests__/ModalShell.test.tsx` | Frontend test |
| `apps/web/src/components/admin/__tests__/RequestChangesModal.test.tsx` | Frontend test |
| `apps/web/src/components/admin/__tests__/RejectModal.test.tsx` | Frontend test |
| `apps/web/src/components/admin/__tests__/SubmissionCard.test.tsx` | Frontend test |
| `apps/web/src/components/admin/__tests__/AuditLogPanel.test.tsx` | Frontend test |
| `apps/web/src/components/admin/__tests__/VersionSelector.test.tsx` | Frontend test |
| `apps/web/src/components/admin/__tests__/VersionDiffView.test.tsx` | Frontend test |

### Summary of Modified Files

| File | What Changed |
|------|-------------|
| `apps/fast-api/skillhub/services/submissions.py` | Added `resubmit_submission()`, `get_audit_trail()`, `get_transition_diff()`, `get_submission_by_display_id()`, `version_submission()` |
| `apps/fast-api/skillhub/schemas/submission.py` | Added `ResubmitRequest/Response`, `AuditTrailEntry/Response`, `TransitionDiffResponse`, `VersionCreateRequest/Response` |
| `apps/api/skillhub_flask/blueprints/submissions.py` | Added 4 new routes (resubmit, audit-log, diff, versions) |
| `apps/web/src/components/admin/AdminConfirmDialog.tsx` | Refactored to use ModalShell |
| `apps/web/src/views/admin/AdminQueueView.tsx` | Uses SubmissionCard, RequestChangesModal, RejectModal, AuditLogPanel |
| `apps/web/src/hooks/useAdminQueue.ts` | Added `revision_number` to ReviewQueueItem |
| `apps/web/src/views/admin/__tests__/AdminQueueView.test.tsx` | Added 5 new test cases, updated mock data |
| `docs/features/index.md` | Added 4 feature entries |

### Estimated New Test Count

- Backend: ~25 new tests (8 resubmit service + 11 endpoint + 6 versioning)
- Frontend: ~61 new tests (7 ModalShell + 8 RequestChanges + 8 Reject + 10 SubmissionCard + 12 AuditLog + 5 VersionSelector + 6 VersionDiff + 5 QueueView updates)
- **Total: ~86 new tests**
