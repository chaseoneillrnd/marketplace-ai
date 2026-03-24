# SkillHub Phase 6 — Post-Migration Enhancements: Technical Implementation Guide

## For Claude Code — Complete Handoff Document

**Project:** SkillHub Post-Migration Enhancements
**Starting Point:** Flask migration complete (Phase 5). Flask app at `apps/api` with 63 paths, 326 security tests. Existing models in `libs/db/skillhub_db/models/`.
**Approach:** TDD-first, new feature development on the Flask app

---

## Supplementary Materials

```
+-----------------------------------------------------------------------------+
| COMPANION DOCUMENT                                                          |
+-----------------------------------------------------------------------------+
|                                                                             |
|  phase6-post-migration-diagrams.md                                          |
|                                                                             |
|  Visual architecture companion with Mermaid diagrams covering:              |
|  - Revision state machine (Section 1)                                       |
|  - Submission pipeline with revision loops (Section 2)                      |
|  - VitePress architecture (Section 3)                                       |
|  - Component hierarchy for submission page (Section 4)                      |
|  - Audit log data flow (Section 5)                                          |
|  - Version selector UX flow (Section 6)                                     |
|  - Database schema changes ERD (Section 7)                                  |
|                                                                             |
|  USAGE: Reference by section when executing prompts.                        |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

## Table of Contents

1. [Global Standards](#global-standards)
2. [Stage A — Admin HITL Queue Enhancements](#stage-a)
3. [Stage B — User Documentation via VitePress](#stage-b)
4. [Stage C — User Skill Submission UI/UX](#stage-c)
5. [Open Design Questions](#open-design-questions)
6. [Quick Reference: Prompt Sequence](#quick-reference)

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
  - Python coverage gate: >=80% (pytest-cov --cov-fail-under=80)
  - TypeScript coverage gate: >=80% (vitest --coverage)
  - Test file lives adjacent to implementation: test_auth.py next to auth.py

Security:
  - No secrets in code — all via Settings (pydantic-settings) or Flask config
  - JWT: decode before trusting, never trust raw claims without verification
  - Division enforcement happens server-side — never client-side
  - audit_log: append-only, no UPDATE/DELETE from application code
  - submission_state_transitions: append-only, same policy

Existing Patterns:
  - Models live in libs/db/skillhub_db/models/
  - Services live in apps/fast-api/skillhub/services/
  - Routers live in apps/api/skillhub_flask/blueprints/
  - Schemas live in apps/fast-api/skillhub/schemas/
  - Tests live in apps/api/tests/
  - React components live in apps/web/src/components/
  - React views live in apps/web/src/views/

Definition of Done (every prompt):
  - [ ] Tests written first and passing
  - [ ] No type errors (mypy / tsc)
  - [ ] No lint warnings (ruff / eslint)
  - [ ] Acceptance criteria verified
  - [ ] No secrets in committed code
  - [ ] Existing tests still pass (no regressions)
```

### Flask-Specific Patterns (All New Routes Must Follow)

```
File locations:
  - Models: libs/db/skillhub_db/models/
  - Services: apps/fast-api/skillhub/services/ (shared via PYTHONPATH)
  - Schemas: apps/fast-api/skillhub/schemas/ (shared via PYTHONPATH)
  - Flask blueprints: apps/api/skillhub_flask/blueprints/
  - Tests: apps/api/tests/
  - PYTHONPATH: apps/api:apps/fast-api:libs/db:libs/python-common

Validation decorators (use these, don't reinvent):
  - validated_body(PydanticModel) — validates JSON body, returns 422 on failure
  - validated_query(PydanticModel) — normalizes MultiDict for Pydantic, returns 422
  - json_response(data, status=200) — handles model_dump(mode="json") + jsonify

Auth patterns:
  - g.current_user — set by before_request hook, always available in auth'd routes
  - @require_platform_team — decorator for admin routes
  - @require_security_team — decorator for security-team-only routes
  - Blueprint-level before_request — use for auth-heavy blueprints (see review_queue.py)
  - PUBLIC_ENDPOINTS — add endpoint names for any new public routes

DB access:
  - from skillhub_flask.db import get_db
  - Background threads: use SessionLocal() directly, never scoped session proxy
```

---

## Stage A — Admin HITL Queue Enhancements

> See Sections 1, 2, 5, 7 of phase6-post-migration-diagrams.md for state machine, pipeline, audit flow, and ERD diagrams.

**Goal:** Enhance the admin HITL queue with structured decision modals, revision tracking, audit logs, and post-approval versioning.

---

### Phase A.1 — Database: Submission State Transitions Table

#### Prompt A.1.1 — Create submission_state_transitions migration and model

```
Add a new append-only table `submission_state_transitions` to track every state
change in a submission's lifecycle.

CONTEXT:
- Existing models: libs/db/skillhub_db/models/submission.py
- Existing SubmissionStatus enum has: submitted, gate1_passed, gate1_failed,
  gate2_passed, gate2_flagged, gate2_failed, gate3_changes_requested,
  approved, rejected, published
- Existing Submission model has: display_id, skill_id, submitted_by, name,
  short_desc, category, content, declared_divisions, division_justification,
  status, gate3_reviewer_id, gate3_reviewed_at, gate3_notes

Requirements:
1. Add new SubmissionStatus enum values:
   - CHANGES_REQUESTED = "changes_requested"
   - REVISION_PENDING = "revision_pending"
   (Keep gate3_changes_requested as legacy alias)

2. Create SubmissionStateTransition model in libs/db/skillhub_db/models/submission.py:
   - id: UUID PK
   - submission_id: FK to submissions.id, NOT NULL, indexed
   - from_status: VARCHAR(30), nullable (null for initial submission)
   - to_status: VARCHAR(30), NOT NULL
   - action: VARCHAR(50), NOT NULL (e.g. "submit", "gate1_pass", "gate1_fail",
     "gate2_pass", "gate2_flag", "gate2_fail", "request_changes", "reject",
     "approve", "resubmit", "publish")
   - actor_id: FK to users.id, NOT NULL
   - notes: TEXT, nullable
   - diff_hunks: JSON, nullable (stores unified diff when content changes)
   - change_request_flags: JSON, nullable (stores flag checkboxes on request_changes)
   - rejection_category: VARCHAR(50), nullable
   - metadata_: JSON, nullable (extra context, named with underscore to avoid
     Python keyword collision per existing AuditLog pattern)
   - created_at: DateTime with timezone, server_default=func.now()

3. This table is APPEND-ONLY. Do NOT add any UPDATE or DELETE operations in
   service code. Enforce via code review convention (no ORM update on this model).

4. Add index on (submission_id, created_at) for efficient audit log queries.

Write tests FIRST for:
- Model can be instantiated with all fields
- created_at defaults to server time
- submission_id FK constraint works
- actor_id FK constraint works
- Append-only: service layer has no update/delete functions for this model

Do NOT:
- Create an Alembic migration yet (next prompt)
- Modify the Submission model yet (next prompt)
- Add any router or service code beyond the model

Acceptance Criteria:
- [ ] SubmissionStateTransition model defined with all columns
- [ ] New enum values added to SubmissionStatus
- [ ] Composite index on (submission_id, created_at) exists
- [ ] All tests pass
- [ ] libs/db/skillhub_db/models/__init__.py exports the new model
```

---

#### Prompt A.1.2 — Extend Submission model with revision and versioning columns

```
Add new columns to the existing Submission model to support revision tracking
and post-approval versioning.

CONTEXT:
- Existing Submission model: libs/db/skillhub_db/models/submission.py
- Existing SkillVersion model: libs/db/skillhub_db/models/skill.py
- We need to track revision rounds, content hashes, and link submissions to
  version updates

Requirements:
1. Add columns to Submission model:
   - revision_number: Integer, default=1, NOT NULL
   - content_hash: VARCHAR(64), nullable, indexed
     (SHA-256 of content field, used for Gate 2 delta check)
   - rejection_category: VARCHAR(50), nullable
     (malicious_content, policy_violation, duplicate, low_quality,
      out_of_scope, other)
   - change_request_flags: JSON, nullable
     (list of flag strings from request_changes decision)
   - parent_submission_id: FK to submissions.id, nullable
     (set when this is a version update submission)
   - target_skill_id: FK to skills.id, nullable
     (set when this submission targets an existing skill for version update)

2. Add submission_id column to SkillVersion model:
   - submission_id: FK to submissions.id, nullable
     (links the approved submission that created this version)

3. Add content_hash computation helper:
   - In libs/db/skillhub_db/models/submission.py, add a module-level function:
     def compute_content_hash(content: str) -> str
   - Uses hashlib.sha256, returns hex digest

Write tests FIRST for:
- Submission model has all new columns with correct defaults
- content_hash index exists
- parent_submission_id self-referential FK works
- target_skill_id FK works
- SkillVersion.submission_id FK works
- compute_content_hash returns consistent SHA-256 hex
- compute_content_hash("") != compute_content_hash("hello")

Do NOT:
- Write Alembic migration (do that manually after both model prompts)
- Change any service logic yet
- Modify any router or schema

Acceptance Criteria:
- [ ] All new columns exist on Submission model
- [ ] SkillVersion has submission_id FK
- [ ] compute_content_hash function works correctly
- [ ] All existing tests still pass
- [ ] All new tests pass
```

---

### Phase A.2 — Revision Tracking Service

#### Prompt A.2.1 — Revision state machine and resubmit service

```
Implement the revision tracking service layer: state transitions, resubmission
logic, and content-hash delta detection.

CONTEXT:
- See Section 1 of phase6-post-migration-diagrams.md for the state machine.
- Existing service: apps/fast-api/skillhub/services/submissions.py
- Existing audit helper: _write_audit() in that file
- New model: SubmissionStateTransition (from Prompt A.1.1)
- New Submission columns: revision_number, content_hash, change_request_flags,
  rejection_category (from Prompt A.1.2)
- The state machine is:
  SUBMITTED -> GATE1 -> GATE2 -> GATE3 (HITL)
                                   |
              APPROVED <-- approve  |
              REJECTED <-- reject   |  <- terminal
              CHANGES_REQUESTED ----+
                      |
              REVISION_PENDING (author editing)
                      |
              SUBMITTED (revision_number++, content overwritten, diff stored)

Requirements:
1. Add function record_state_transition() to submissions service:
   - Creates SubmissionStateTransition row
   - Parameters: db, submission_id, from_status, to_status, action, actor_id,
     notes=None, diff_hunks=None, change_request_flags=None,
     rejection_category=None, metadata=None
   - Always called inside existing transaction (no separate commit)

2. Add function resubmit_submission():
   - Parameters: db, display_id, user_id, new_content, new_name=None,
     new_short_desc=None
   - Validates: submission exists, user is owner, status is CHANGES_REQUESTED
     or REVISION_PENDING
   - Computes unified diff between old content and new content (use difflib)
   - Mutates the EXISTING Submission row:
     * content = new_content
     * name = new_name (if provided)
     * short_desc = new_short_desc (if provided)
     * content_hash = compute_content_hash(new_content)
     * revision_number += 1
     * status = SUBMITTED
     * updated_at = now
   - Records state transition with diff_hunks
   - Runs Gate 1 synchronously (reuse existing gate1 logic)
   - If Gate 1 passes, queue Gate 2 in background
   - Gate 2 optimization: if content_hash unchanged, skip with "no_change" result
   - Gate 3: always fresh HITL review
   - Returns updated SubmissionDetail-compatible dict

3. Modify existing review_submission() to use record_state_transition():
   - On "approved": record transition, create Skill + SkillVersion
   - On "changes_requested": record transition with change_request_flags
   - On "rejected": record transition with rejection_category
   - Soft escalation: if revision_number >= 3, add escalation_recommended=True
     to the transition metadata

4. Modify existing create_submission() to:
   - Compute and store content_hash
   - Record initial SUBMITTED state transition

Write tests FIRST for:
- record_state_transition creates correct row with all fields
- resubmit_submission: happy path (changes_requested -> submitted)
- resubmit_submission: revision_number increments
- resubmit_submission: diff_hunks stored correctly
- resubmit_submission: wrong user -> 403
- resubmit_submission: wrong status -> 409
- resubmit_submission: content_hash computed and stored
- Gate 2 skipped when content_hash unchanged
- review_submission now records state transitions
- Soft escalation at revision_number >= 3
- create_submission records initial transition

Do NOT:
- Add any router or API endpoint (next prompt)
- Modify any frontend code
- Change the database schema further

Acceptance Criteria:
- [ ] record_state_transition function works
- [ ] resubmit_submission full flow works with diff storage
- [ ] Existing review_submission enhanced with transitions
- [ ] Gate 2 content-hash optimization works
- [ ] Soft escalation flag at 3+ revisions
- [ ] All existing submission tests still pass
- [ ] All new tests pass with >=80% coverage on changed files
```

---

#### Prompt A.2.2 — Resubmit and audit-log API endpoints

```
Add API endpoints for resubmission and audit log retrieval.

CONTEXT:
- Existing router: apps/api/skillhub_flask/blueprints/submissions.py
- Existing schemas: apps/fast-api/skillhub/schemas/submission.py
- New service functions: resubmit_submission(), record_state_transition()

Requirements:
1. New schemas in apps/fast-api/skillhub/schemas/submission.py:
   - ResubmitRequest: content (str, required), name (str, optional),
     short_desc (str, optional)
   - StateTransitionResponse: action, actor_id, timestamp, state_before,
     state_after, notes, diff_hunks, change_request_flags, rejection_category
   - AuditLogResponse: items (list[StateTransitionResponse]), total (int)
   - DiffResponse: display_id, revision_number, diff_hunks (list of strings),
     old_content_preview (str, first 500 chars), new_content_preview (str)

2. New endpoints in apps/api/skillhub_flask/blueprints/submissions.py:
   - POST /api/v1/submissions/{display_id}/resubmit
     Auth: submission owner only
     Body: ResubmitRequest
     Returns: SubmissionDetail (updated)
     Errors: 403 not owner, 404 not found, 409 wrong status

   - GET /api/v1/submissions/{display_id}/audit-log
     Auth: submission owner OR platform_team
     Query params: page (default 1), per_page (default 50)
     Returns: AuditLogResponse
     Sources: submission_state_transitions ordered by created_at ASC

   - GET /api/v1/submissions/{display_id}/diff
     Auth: platform_team only
     Query params: revision (optional, defaults to latest)
     Returns: DiffResponse
     Returns diff_hunks from the state transition for the specified revision

Write tests FIRST for:
- POST resubmit: 201 on valid resubmission
- POST resubmit: 403 when not owner
- POST resubmit: 404 when not found
- POST resubmit: 409 when status is not changes_requested
- GET audit-log: returns all transitions in chronological order
- GET audit-log: owner can see own submission audit log
- GET audit-log: platform_team can see any audit log
- GET audit-log: other user gets 403
- GET audit-log: pagination works
- GET diff: returns correct diff hunks
- GET diff: 403 for non-platform-team
- GET diff: specific revision parameter works

Do NOT:
- Add frontend components yet
- Modify any model code
- Change existing endpoint signatures

Acceptance Criteria:
- [ ] All three endpoints functional
- [ ] Auth checks correct for each endpoint
- [ ] Pagination on audit-log works
- [ ] All tests pass with >=80% coverage
- [ ] Existing tests unbroken
```

---

### Phase A.3 — Enhanced Decision Modals (Frontend)

#### Prompt A.3.1 — Extract ModalShell from AdminConfirmDialog

```
Extract a reusable ModalShell component from the existing AdminConfirmDialog.

CONTEXT:
- Existing: apps/web/src/components/admin/AdminConfirmDialog.tsx
- It has: fixed overlay backdrop (rgba(4,8,16,0.85) + blur), focus trap via
  useFocusTrap hook, aria-modal="true", gradient top bar, 420px card
- We need to share this chrome across RequestChangesModal, RejectModal,
  and the existing AdminConfirmDialog
- See Section 4 of phase6-post-migration-diagrams.md for component hierarchy

Requirements:
1. Create apps/web/src/components/admin/ModalShell.tsx:
   - Props: children, title, onClose, width (default '420px'),
     accentGradient (string, default the blue-purple-green gradient),
     testId (string)
   - Renders: fixed backdrop, blur, centered card, gradient top bar,
     title in header, close X button (top-right), children slot
   - Uses useFocusTrap with onEscape: onClose
   - aria-modal="true", role="dialog", aria-labelledby

2. Refactor AdminConfirmDialog to use ModalShell:
   - Remove duplicated backdrop/card/focus-trap code
   - Keep existing props interface unchanged (backwards compatible)
   - AdminConfirmDialog becomes: ModalShell + message + button row

3. Ensure AdminConfirmDialog tests still pass unchanged.

Write tests FIRST for:
- ModalShell renders with title
- ModalShell calls onClose when backdrop clicked
- ModalShell calls onClose on Escape key
- ModalShell has aria-modal="true"
- ModalShell renders children
- ModalShell uses custom width when provided
- AdminConfirmDialog still renders correctly (existing tests pass)

Do NOT:
- Create RequestChangesModal or RejectModal yet (next prompts)
- Change any admin view code
- Add any API calls

Acceptance Criteria:
- [ ] ModalShell component works standalone
- [ ] AdminConfirmDialog refactored to use ModalShell
- [ ] All existing AdminConfirmDialog tests pass without changes
- [ ] New ModalShell tests pass
- [ ] No visual regression (same styles as before)
```

---

#### Prompt A.3.2 — RequestChangesModal component

```
Create the RequestChangesModal for structured change-request decisions in HITL review.

CONTEXT:
- ModalShell component from Prompt A.3.1
- Used in AdminQueueView when reviewer clicks "Request Changes"
- Standard flag checkboxes + free-text notes

Requirements:
1. Create apps/web/src/components/admin/RequestChangesModal.tsx:
   - Props: onSubmit(data: ChangeRequestData), onCancel, submissionName (string)
   - ChangeRequestData type: { flags: string[], notes: string }
   - Available flags (render as checkboxes):
     * missing_front_matter — "Missing or incomplete front matter"
     * security_concern — "Security concern identified"
     * scope_too_broad — "Scope too broad for single skill"
     * quality_insufficient — "Quality does not meet standards"
     * division_mismatch — "Division assignment incorrect"
     * needs_changelog — "Changelog required"
   - Free-text textarea for notes (required, min 10 chars)
   - At least one flag must be checked to submit
   - "Submit Feedback" button (disabled until valid)
   - Uses ModalShell with amber-red gradient, title "Request Changes"
   - Show submission name in subtitle

2. Export ChangeRequestData type from a shared types location.

Write tests FIRST for:
- Renders all 6 flag checkboxes
- Submit disabled when no flags checked
- Submit disabled when notes < 10 chars
- Submit enabled when >= 1 flag checked AND notes >= 10 chars
- onSubmit called with correct flags array and notes
- onCancel called when cancel clicked
- Checkbox toggle works
- Notes textarea updates

Do NOT:
- Wire to API yet (that happens in the view integration prompt)
- Create RejectModal yet (next prompt)
- Modify AdminQueueView

Acceptance Criteria:
- [ ] Component renders correctly
- [ ] Validation logic works (flags + notes)
- [ ] onSubmit payload shape is correct
- [ ] All tests pass
- [ ] Accessible: labels on checkboxes, aria-required on textarea
```

---

#### Prompt A.3.3 — RejectModal component

```
Create the RejectModal for structured rejection decisions in HITL review.

CONTEXT:
- ModalShell component from Prompt A.3.1
- Used in AdminQueueView when reviewer clicks "Reject"
- Dropdown for rejection category + conditional free-text

Requirements:
1. Create apps/web/src/components/admin/RejectModal.tsx:
   - Props: onSubmit(data: RejectData), onCancel, submissionName (string)
   - RejectData type: { category: string, notes: string }
   - Rejection categories (render as <select> dropdown):
     * malicious_content — "Malicious content"
     * policy_violation — "Policy violation"
     * duplicate — "Duplicate of existing skill"
     * low_quality — "Low quality"
     * out_of_scope — "Out of scope for platform"
     * other — "Other (specify below)"
   - When "other" selected: notes textarea becomes required (min 10 chars)
   - When non-other selected: notes textarea optional but available
   - "Reject Submission" button (destructive red style)
   - Uses ModalShell with red gradient, title "Reject Submission"
   - Warning text: "This action is final. The submission cannot be reopened."

2. Export RejectData type.

Write tests FIRST for:
- Renders dropdown with all 6 categories
- Submit disabled when no category selected
- Submit enabled when non-other category selected (notes optional)
- Submit disabled when "other" selected and notes empty
- Submit enabled when "other" selected and notes >= 10 chars
- onSubmit called with correct category and notes
- Warning text visible
- Destructive button styling applied

Do NOT:
- Wire to API
- Modify AdminQueueView
- Change RequestChangesModal

Acceptance Criteria:
- [ ] Component renders correctly
- [ ] Conditional validation for "other" category works
- [ ] Destructive styling applied to reject button
- [ ] Warning text present
- [ ] All tests pass
- [ ] Accessible: label on select, required indicators
```

---

### Phase A.4 — Submission Card Enhancements

#### Prompt A.4.1 — Enhanced SubmissionCard with user info and RevisionBadge

```
Create enhanced SubmissionCard and RevisionBadge components for the admin queue.

CONTEXT:
- Existing AdminQueueView: apps/web/src/views/admin/AdminQueueView.tsx
- Currently uses inline card rendering — we need a dedicated component
- See Section 4 of phase6-post-migration-diagrams.md

Requirements:
1. Create apps/web/src/components/admin/RevisionBadge.tsx:
   - Props: revisionNumber (number)
   - Displays "Round N" (never "N rejections")
   - Styling: pill badge, neutral color for rounds 1-2
   - At 3+ rounds: amber/warning color + tooltip "Consider escalation"
   - Round 1: no badge shown (return null)

2. Create apps/web/src/components/admin/SubmissionCard.tsx:
   - Props: submission (AdminSubmissionSummary extended with revision_number,
     submitted_by_name, submitted_by_division, submitted_by_avatar_url),
     onClick, onApprove, onRequestChanges, onReject
   - Layout: card with gradient left border based on status
   - Shows: name, short_desc, category badge, status badge
   - Shows: "Requested by" section with user name, division chip, avatar
   - Shows: RevisionBadge when revision_number > 1
   - Shows: action buttons (Approve / Request Changes / Reject) only when
     status is gate2_passed or gate2_flagged (HITL-ready)
   - Clicking card body -> onClick (opens detail)

Write tests FIRST for:
- RevisionBadge: null for round 1
- RevisionBadge: "Round 2" for revision_number=2
- RevisionBadge: warning style for revision_number=3
- RevisionBadge: escalation tooltip at 3+
- SubmissionCard: renders submission name and description
- SubmissionCard: shows "Requested by" with user info
- SubmissionCard: shows RevisionBadge when revision > 1
- SubmissionCard: action buttons only for HITL-ready statuses
- SubmissionCard: onClick fires on card body click
- SubmissionCard: onApprove/onRequestChanges/onReject fire on button clicks

Do NOT:
- Modify AdminQueueView yet (integration is a separate prompt)
- Add API calls to these components
- Create the SubmissionDetail component yet

Acceptance Criteria:
- [ ] RevisionBadge renders correctly for all round numbers
- [ ] SubmissionCard shows user info section
- [ ] Action buttons conditional on status
- [ ] All tests pass
- [ ] Components are presentation-only (no API calls)
```

---

#### Prompt A.4.2 — Integrate enhanced cards and modals into AdminQueueView

```
Wire the new SubmissionCard, RequestChangesModal, and RejectModal into the
existing AdminQueueView.

CONTEXT:
- Existing: apps/web/src/views/admin/AdminQueueView.tsx
- New components: SubmissionCard, RequestChangesModal, RejectModal, ModalShell
- Existing API calls in AdminQueueView for approve/reject
- Need to add resubmit-aware API calls

Requirements:
1. Replace inline card rendering in AdminQueueView with SubmissionCard component.

2. Add modal state management:
   - activeModal: null | 'requestChanges' | 'reject' | 'approve'
   - selectedSubmission: the submission being acted on
   - When "Request Changes" clicked on card -> open RequestChangesModal
   - When "Reject" clicked on card -> open RejectModal
   - When "Approve" clicked on card -> open existing AdminConfirmDialog

3. Wire modal submissions to API:
   - RequestChangesModal.onSubmit -> PATCH /api/v1/submissions/{id}/review
     with decision="changes_requested", notes, change_request_flags
   - RejectModal.onSubmit -> PATCH /api/v1/submissions/{id}/review
     with decision="rejected", notes, rejection_category
   - Existing approve flow unchanged

4. After successful action: remove card from list, show toast/notification.

5. Extend the admin submissions API response schema to include:
   - revision_number
   - submitted_by_name, submitted_by_division (join user data server-side)

Write tests FIRST for:
- AdminQueueView renders SubmissionCard components
- Clicking "Request Changes" opens RequestChangesModal
- Clicking "Reject" opens RejectModal
- Clicking "Approve" opens AdminConfirmDialog
- Submitting RequestChangesModal calls API with correct payload
- Submitting RejectModal calls API with correct payload
- Card removed from list after successful action
- Modal closes after successful submission
- Error handling: API error shows error state

Do NOT:
- Change the SubmissionCard or modal components themselves
- Modify the backend beyond the schema extension for user info
- Add the AuditLogPanel yet

Acceptance Criteria:
- [ ] AdminQueueView uses SubmissionCard
- [ ] All three modal flows work end-to-end
- [ ] API payloads include new fields (flags, category)
- [ ] Cards removed after action
- [ ] All existing AdminQueueView tests updated and passing
- [ ] All new tests pass
```

---

### Phase A.5 — Audit Log

#### Prompt A.5.1 — AuditLogPanel component

```
Create the AuditLogPanel component that displays submission history in a
conversation-thread style (like GitHub PR review timeline).

CONTEXT:
- API endpoint: GET /api/v1/submissions/{display_id}/audit-log (from A.2.2)
- See Section 5 of phase6-post-migration-diagrams.md for data flow
- Displays in SubmissionDetail view sidebar/panel

Requirements:
1. Create apps/web/src/components/admin/AuditLogPanel.tsx:
   - Props: displayId (string), isVisible (boolean)
   - Fetches audit log from API on mount (when visible)
   - Renders timeline:
     * Each entry is a "card" in a vertical timeline
     * Left: colored dot (green=approve, amber=changes_requested, red=reject,
       blue=submit/resubmit, gray=gate results)
     * Content: action label, actor name, timestamp (relative, e.g. "2h ago"),
       notes (if any), expandable diff viewer (if diff_hunks present)
     * Change request flags shown as pills/chips when present
     * Rejection category shown as a labeled badge when present
   - Chronological order (oldest first, newest at bottom)
   - Loading skeleton while fetching
   - Empty state: "No history yet"

2. Diff viewer sub-component (inline, not separate file):
   - Renders unified diff with red/green line highlighting
   - Collapsed by default, "Show changes" toggle to expand
   - Monospace font, line numbers

Write tests FIRST for:
- Renders loading skeleton initially
- Renders timeline entries after fetch
- Correct dot colors for each action type
- Relative timestamps displayed
- Notes text rendered when present
- Diff toggle expands/collapses diff view
- Change request flags rendered as chips
- Empty state when no transitions
- Error state on fetch failure

Do NOT:
- Integrate into AdminQueueView yet
- Create the full SubmissionDetail view yet
- Add any API mutations

Acceptance Criteria:
- [ ] Timeline renders correctly with all entry types
- [ ] Diff viewer works with expand/collapse
- [ ] Loading/empty/error states handled
- [ ] All tests pass
- [ ] Accessible: timeline semantics, expandable region aria-expanded
```

---

### Phase A.6 — Post-Approval Versioning

#### Prompt A.6.1 — Version submission service and endpoint

```
Implement the post-approval versioning flow: skill owners can submit version
updates that go through the same gate pipeline.

CONTEXT:
- Existing: apps/fast-api/skillhub/services/submissions.py (create_submission)
- Existing: libs/db/skillhub_db/models/skill.py (Skill, SkillVersion)
- New columns: parent_submission_id, target_skill_id on Submission
- New column: submission_id on SkillVersion

Requirements:
1. Add function create_version_submission() to submissions service:
   - Parameters: db, user_id, skill_id, content, changelog, version,
     background_tasks
   - Validates:
     * Skill exists and is published
     * User is skill owner OR is platform_team
     * Version is valid semver (X.Y.Z)
     * Version is greater than skill.current_version (use packaging.version)
     * Changelog is non-empty
   - Creates Submission with:
     * target_skill_id = skill_id
     * parent_submission_id = None (or latest submission for this skill)
     * name = existing skill name
     * content_hash = computed
   - Gate 1 modification: slug uniqueness check is INVERTED for version
     submissions — the slug MUST match an existing skill (not be unique)
   - Gate 2 + Gate 3: normal flow
   - On approval (in review_submission):
     * Creates new SkillVersion row with submission_id set
     * Updates Skill.current_version
     * Does NOT create a new Skill row

2. New endpoint: POST /api/v1/skills/{skill_id}/versions
   - Auth: skill owner OR platform_team
   - Body: { content: str, changelog: str, version: str }
   - Returns: SubmissionCreateResponse
   - Errors: 403 not owner, 404 skill not found, 409 version not greater,
     422 invalid semver

3. New schema: VersionSubmitRequest (content, changelog, version)

Write tests FIRST for:
- create_version_submission: happy path creates submission
- Version must be semver format
- Version must be greater than current
- Only owner or platform_team can submit
- Skill must be published
- Gate 1 inverted slug check passes for existing skill
- Gate 1 inverted slug check fails for non-matching skill
- On approval: SkillVersion created with correct submission_id
- On approval: Skill.current_version updated
- On approval: no new Skill row created
- API endpoint: 201 on success
- API endpoint: 403 for non-owner
- API endpoint: 409 for version not greater

Do NOT:
- Add frontend components yet
- Modify the browse/detail views
- Change existing submission flow for new skills

Acceptance Criteria:
- [ ] Version submission creates correct Submission with target_skill_id
- [ ] Semver validation works
- [ ] Gate 1 inverted check works
- [ ] Approval creates SkillVersion and updates current_version
- [ ] API endpoint with correct auth
- [ ] All tests pass with >=80% coverage
```

---

#### Prompt A.6.2 — VersionSelector and VersionDiffView components

```
Create frontend components for viewing and comparing skill versions.

CONTEXT:
- Existing: apps/web/src/views/SkillDetailView.tsx
- Existing API: GET /api/v1/skills/{slug} returns skill with current_version
- Need: version list endpoint, version detail, diff between versions
- See Section 6 of phase6-post-migration-diagrams.md for UX flow

Requirements:
1. New API endpoint (backend): GET /api/v1/skills/{skill_id}/versions
   - Returns: list of { version, changelog, published_at, content_hash }
   - Ordered by published_at DESC
   - No auth required (public, respects division visibility)

2. Create apps/web/src/components/VersionSelector.tsx:
   - Props: skillId (string), currentVersion (string),
     selectedVersion (string), onVersionChange(version: string)
   - Dropdown showing all versions with current marked "(current)"
   - Fetches version list on mount
   - Shows version + date + changelog preview in dropdown items

3. Create apps/web/src/components/VersionDiffView.tsx:
   - Props: skillId (string), fromVersion (string), toVersion (string)
   - Fetches content for both versions
   - Displays side-by-side or unified diff
   - Toggle between side-by-side and unified views
   - "Compare with current" shortcut button

4. Banner component (inline in SkillDetailView, not separate file):
   - When viewing non-current version: yellow banner
     "Viewing historical version {X.Y.Z}. Current is {A.B.C}."
   - "View current" link in banner

5. Browse grid badge (update SkillCard.tsx):
   - Show "v{current_version}" badge
   - Show "{N} versions" count if N > 1
   - Click badge -> navigate to detail

Write tests FIRST for:
- VersionSelector: renders dropdown with versions
- VersionSelector: marks current version
- VersionSelector: calls onVersionChange
- VersionDiffView: renders diff between two versions
- VersionDiffView: toggle between side-by-side and unified
- Historical version banner shows when non-current selected
- Historical version banner hidden for current
- SkillCard badge shows version
- API endpoint returns versions in order

Do NOT:
- Modify the submission flow
- Change admin queue views
- Add edit capabilities (view only)

Acceptance Criteria:
- [ ] VersionSelector dropdown works
- [ ] VersionDiffView shows meaningful diff
- [ ] Historical version banner works
- [ ] SkillCard updated with version badge
- [ ] API endpoint returns version list
- [ ] All tests pass
```

---

## Stage B — User Documentation via VitePress

> See Section 3 of phase6-post-migration-diagrams.md for VitePress architecture diagram.

**Goal:** Create a VitePress documentation site served at /docs, integrated into the NX monorepo.

---

### Phase B.1 — VitePress Scaffold

#### Prompt B.1.1 — Initialize VitePress app in NX monorepo

```
Create a new VitePress documentation app at apps/docs/ in the NX monorepo.

CONTEXT:
- NX monorepo with apps/web, apps/api, apps/mcp-server
- VitePress will be served at /docs via nginx location block
- See Section 3 of phase6-post-migration-diagrams.md

Requirements:
1. Create apps/docs/ directory structure:
   apps/docs/
   ├── package.json          (name: @skillhub/docs)
   ├── .vitepress/
   │   ├── config.ts         (VitePress config)
   │   └── theme/
   │       └── index.ts      (theme customization entry)
   ├── index.md              (landing page)
   ├── public/
   │   └── logo.svg          (placeholder)
   └── project.json          (NX project config)

2. VitePress config (apps/docs/.vitepress/config.ts):
   - base: '/docs/'
   - title: 'SkillHub Docs'
   - description: 'User documentation for SkillHub AI Skills Marketplace'
   - themeConfig.nav: include "Back to SkillHub" link pointing to "/"
   - themeConfig.sidebar: structured for all planned pages
   - themeConfig.socialLinks: internal GitLab link (placeholder)

3. NX project config (apps/docs/project.json):
   - targets:
     * dev: vitepress dev
     * build: vitepress build
     * preview: vitepress preview

4. Update root package.json workspaces to include apps/docs.

5. Add mise tasks:
   - dev:docs -> nx run docs:dev
   - build:docs -> nx run docs:build

6. Index page content:
   - Hero with title "SkillHub Documentation"
   - Quick links to Getting Started, Submitting a Skill, FAQ
   - Brief intro paragraph

Write tests FIRST for:
- vitepress build exits 0 (docs compile)
- NX recognizes the docs project (nx show projects includes docs)
- base path is '/docs/' in config

Do NOT:
- Write all documentation content yet (just index page)
- Configure nginx yet (separate prompt)
- Add search functionality yet
- Install VitePress globally — use workspace dependency

Acceptance Criteria:
- [ ] apps/docs/ exists with correct structure
- [ ] nx run docs:dev starts dev server
- [ ] nx run docs:build produces dist output
- [ ] VitePress config has base: '/docs/'
- [ ] "Back to SkillHub" link in nav
- [ ] Sidebar structure defined for all planned pages
- [ ] mise tasks work
```

---

#### Prompt B.1.2 — Nginx configuration and Docker integration

```
Configure nginx to serve VitePress docs at /docs and integrate into Docker build.

CONTEXT:
- VitePress app at apps/docs/ with base: '/docs/'
- Existing docker-compose.yml has web service serving React app
- Need nginx to route /docs to VitePress static output, everything else to React

Requirements:
1. Create apps/docs/nginx.conf (or update existing nginx config):
   - location /docs/ -> serve VitePress dist/ static files
   - location / -> serve React app (existing)
   - Try files with fallback for SPA routing on both

2. Update Dockerfile for web/nginx service:
   - Multi-stage build:
     * Stage 1: build React app (existing)
     * Stage 2: build VitePress docs
     * Stage 3: nginx with both dist outputs
   - Copy React dist to /usr/share/nginx/html/
   - Copy VitePress dist to /usr/share/nginx/html/docs/

3. Update docker-compose.yml:
   - Ensure docs build is included in the web service build

4. Navigation integration:
   - In apps/web/src/components/Nav.tsx: add "Docs" link
   - Use plain <a href="/docs/"> (NOT React Router Link)
   - This ensures a full page navigation to VitePress

Write tests FIRST for:
- nginx config is valid (nginx -t with the config)
- Docker build succeeds for the combined image
- Nav component renders "Docs" link with correct href
- Docs link uses <a> tag, not React Router Link

Do NOT:
- Write documentation content
- Add search or algolia
- Change VitePress config

Acceptance Criteria:
- [ ] nginx config routes /docs/ to VitePress output
- [ ] nginx config routes / to React app
- [ ] Docker multi-stage build works
- [ ] "Docs" link in Nav component
- [ ] Tests pass
```

---

### Phase B.2 — Documentation Content

#### Prompt B.2.1 — Getting Started and introductory pages

```
Write the first batch of VitePress documentation pages: Getting Started,
Introduction to Skills, and Uses for Skills.

CONTEXT:
- VitePress app at apps/docs/
- Sidebar already configured for these pages
- Target audience: end users of SkillHub (not developers)

Requirements:
1. Create apps/docs/getting-started.md:
   - Overview of SkillHub
   - Installation methods section with sub-pages/tabs:
     * Claude Code CLI: how to install skills via CLI
     * Cline: how to install via Cline extension
     * MCP: how to connect via MCP server
     * Manual: how to manually copy skill files
   - First skill walkthrough (step-by-step)
   - "What's Next" links

2. Create apps/docs/introduction.md:
   - What is an AI Skill?
   - How skills work (non-technical explanation)
   - Skill anatomy: front matter, content, trigger phrases
   - Skill types: automation, coding, analysis, documentation

3. Create apps/docs/uses.md:
   - Use cases organized by role (developer, PM, analyst, etc.)
   - Real examples with skill names
   - "Most popular skills" section
   - Tips for finding the right skill

4. All pages must:
   - Use VitePress markdown features (containers, code groups, badges)
   - Include frontmatter with title, description
   - Have proper heading hierarchy (single H1, H2s for sections)
   - Link to related pages

Write tests FIRST for:
- All .md files have frontmatter with title
- No broken internal links (VitePress build succeeds)
- Each page has exactly one H1

Do NOT:
- Add custom Vue components
- Write pages not in this prompt's scope
- Include real API keys or secrets in examples

Acceptance Criteria:
- [ ] Three pages created with full content
- [ ] VitePress build succeeds with new pages
- [ ] Frontmatter correct on all pages
- [ ] Internal links work
- [ ] Content is user-focused (not developer docs)
```

---

#### Prompt B.2.2 — Discovery, Social, and Advanced Usage pages

```
Write the second batch of documentation pages: Skill Discovery, Social Features,
and Advanced Usage.

CONTEXT:
- VitePress app at apps/docs/
- Existing pages: getting-started, introduction, uses

Requirements:
1. Create apps/docs/discovery.md:
   - Browse by category
   - Search tips and filters
   - Division-based visibility explained
   - Featured and trending skills
   - Sorting options

2. Create apps/docs/social.md:
   - Reviews and ratings
   - Comments and discussions
   - Favorites and collections
   - Following skill authors
   - Community guidelines

3. Create apps/docs/advanced.md:
   - Skill chaining and composition
   - MCP server integration details
   - Custom trigger phrases
   - Skill configuration via front matter
   - Environment-specific skill variants
   - Performance tips

4. All pages: VitePress containers, code examples where relevant,
   frontmatter, proper heading hierarchy.

Write tests FIRST for:
- All .md files have frontmatter
- VitePress build succeeds
- No broken internal links

Do NOT:
- Modify existing pages
- Add custom components

Acceptance Criteria:
- [ ] Three pages created
- [ ] Build succeeds
- [ ] Links between pages work
- [ ] Content appropriate for each topic
```

---

#### Prompt B.2.3 — Submission guide, FAQ, and Resources pages

```
Write the final batch of documentation pages: Submitting a Skill, Feature Requests,
FAQ, and Resources.

CONTEXT:
- VitePress app at apps/docs/
- This batch completes the full documentation set

Requirements:
1. Create apps/docs/submitting.md:
   - Prerequisites for submission
   - Step-by-step submission guide (matches the 3 modes: form, upload, MCP sync)
   - Front matter requirements and examples
   - What happens after submission (gate pipeline explained simply)
   - Responding to change requests
   - Version updates for published skills

2. Create apps/docs/feature-requests.md:
   - How to submit feature requests
   - Roadmap visibility
   - Voting on features
   - What makes a good feature request

3. Create apps/docs/faq.md:
   - 15-20 Q&A pairs covering:
     * Account and access
     * Skill installation
     * Submission process
     * Reviews and visibility
     * Technical questions
   - Collapsible sections using VitePress details containers

4. Create apps/docs/resources.md:
   - Links to related tools
   - Glossary of terms
   - Changelog link
   - Contact and support info

Write tests FIRST for:
- All .md files have frontmatter
- VitePress build succeeds
- Complete sidebar coverage (every sidebar entry has a page)

Do NOT:
- Modify existing pages
- Reference real internal URLs (use placeholders)

Acceptance Criteria:
- [ ] Four pages created
- [ ] Full documentation set complete (10 pages)
- [ ] VitePress build succeeds
- [ ] All sidebar entries resolve to existing pages
- [ ] FAQ has 15+ questions
```

---

## Stage C — User Skill Submission UI/UX

> See Section 4 of phase6-post-migration-diagrams.md for component hierarchy diagram.

**Goal:** Build a multi-mode skill submission page with form builder, file upload, MCP sync, live preview, and validation.

---

### Phase C.1 — Shared Components

#### Prompt C.1.1 — FrontMatterValidator component

```
Create a mode-agnostic front matter validation component that provides real-time
feedback on skill content structure.

CONTEXT:
- Used by all three submission modes (form, upload, MCP sync)
- Validates the front matter block of SKILL.md content
- See Section 4 of phase6-post-migration-diagrams.md for component hierarchy

Requirements:
1. Create apps/web/src/components/submission/FrontMatterValidator.tsx:
   - Props: content (string — full SKILL.md text), onChange(issues: Issue[])
   - Issue type: { field: string, severity: 'error'|'warning'|'info',
     message: string }
   - Validates:
     * Front matter delimiters present (--- ... ---)
     * Required fields: name, description, category, version, author,
       install_method, data_sensitivity
     * Field value constraints:
       - name: 1-255 chars
       - description: 1-255 chars
       - version: valid semver (X.Y.Z)
       - category: must be from known list
       - install_method: claude-code | mcp | manual | all
       - data_sensitivity: low | medium | high | phi
     * Warnings for:
       - Missing optional fields (tags, trigger_phrases, changelog)
       - Very short description (< 20 chars)
       - No trigger phrases defined
   - Renders: compact list of issues with severity icons
   - Updates on every content change (debounced 300ms)
   - Green checkmark when all required fields valid

2. Export the validation logic as a pure function (testable without React):
   validateFrontMatter(content: string): Issue[]

Write tests FIRST for:
- validateFrontMatter: valid content returns no errors
- validateFrontMatter: missing delimiters returns error
- validateFrontMatter: missing required field returns error per field
- validateFrontMatter: invalid semver returns error
- validateFrontMatter: invalid category returns error
- validateFrontMatter: missing optional fields returns warnings
- validateFrontMatter: short description returns warning
- Component renders issues list
- Component shows green checkmark when valid
- Component debounces validation on rapid changes
- onChange callback fires with current issues

Do NOT:
- Add API calls (validation is client-side only)
- Create the preview panel yet
- Wire to any submission mode

Acceptance Criteria:
- [ ] Pure validation function works standalone
- [ ] Component renders correctly for all severity levels
- [ ] Debounce works (no excessive re-renders)
- [ ] All tests pass
- [ ] Accessible: severity communicated via both icon and text
```

---

#### Prompt C.1.2 — SkillPreviewPanel component

```
Create a live preview panel that renders SKILL.md content as it would appear
to end users.

CONTEXT:
- Shared across all submission modes
- Renders the skill as it would look on the browse/detail page
- Updates live as user edits

Requirements:
1. Create apps/web/src/components/submission/SkillPreviewPanel.tsx:
   - Props: content (string — full SKILL.md text), mode ('split'|'preview')
   - Parses front matter to extract metadata
   - Renders:
     * Header: skill name, category badge, version badge
     * Description text
     * Install method badge
     * Data sensitivity indicator
     * Tags as chips
     * Trigger phrases list
     * Content body rendered as markdown (use a lightweight md renderer,
       e.g. marked + DOMPurify for sanitization)
   - Split mode: side-by-side with editor (just the preview half)
   - Preview mode: full width
   - "No content yet" placeholder when empty
   - Error boundary: if markdown parsing fails, show raw text

2. Markdown rendering:
   - Code blocks with syntax highlighting (use highlight.js or similar)
   - Tables, lists, headings
   - NO raw HTML allowed (sanitize)
   - Links open in new tab

Write tests FIRST for:
- Renders skill name from front matter
- Renders category and version badges
- Renders markdown content body
- Handles empty content gracefully
- Handles malformed front matter (shows error, not crash)
- Sanitizes HTML in content
- Code blocks rendered with highlighting
- Split vs preview mode layout

Do NOT:
- Add editing capability (this is read-only preview)
- Wire to API
- Create submission modes yet

Acceptance Criteria:
- [ ] Preview renders accurately from SKILL.md content
- [ ] Front matter metadata displayed as badges/chips
- [ ] Markdown rendered safely (sanitized)
- [ ] Empty and error states handled
- [ ] All tests pass
```

---

### Phase C.2 — Submission Modes

#### Prompt C.2.1 — FormBuilderMode: guided wizard

```
Create the form-based guided wizard for skill submission.

CONTEXT:
- One of three submission modes in SubmitSkillPage
- Produces { frontMatter, content } output consumed by shared validator/preview
- See Section 4 of phase6-post-migration-diagrams.md

Requirements:
1. Create apps/web/src/components/submission/FormBuilderMode.tsx:
   - Props: onContentChange(content: string), initialContent (string, optional)
   - Multi-step wizard with progress indicator:
     * Step 1 — Basics: name, short_desc, category (dropdown), version
     * Step 2 — Configuration: install_method, data_sensitivity, divisions,
       tags (tag input), trigger_phrases (list builder)
     * Step 3 — Content: rich text editor area for skill body
       (plain textarea with markdown formatting toolbar)
     * Step 4 — Preview: read-only preview using SkillPreviewPanel
   - Navigation: Previous / Next buttons, step indicator dots
   - Assembles SKILL.md from form fields:
     * Generates front matter block from step 1+2 fields
     * Appends content body from step 3
   - Calls onContentChange on every field change (debounced 500ms)
   - Form validation per step (must complete before advancing)
   - "Import from file" button on step 3 to load existing .md content

2. Each step validates independently:
   - Step 1: all fields required, name 1-255, desc 1-255
   - Step 2: at least one division selected, install_method required
   - Step 3: content non-empty
   - Step 4: no validation (review only)

Write tests FIRST for:
- Renders step 1 by default
- Cannot advance past step 1 with empty fields
- Can advance to step 2 after filling required fields
- Step 2 division selection works
- Step 2 tag input adds/removes tags
- Step 3 textarea accepts content
- Step 4 shows preview
- onContentChange called with assembled SKILL.md
- Navigation: Previous goes back, Next goes forward
- Step indicator shows current step
- Import from file populates content

Do NOT:
- Create FileUploadMode or MCPSyncMode (separate prompts)
- Add API submission calls
- Create SubmitSkillPage wrapper

Acceptance Criteria:
- [ ] 4-step wizard navigable
- [ ] Form fields assemble valid SKILL.md
- [ ] Per-step validation works
- [ ] onContentChange fires with correct content
- [ ] All tests pass
- [ ] Accessible: fieldset/legend, required indicators, step announcements
```

---

#### Prompt C.2.2 — FileUploadMode: drag-and-drop .md upload

```
Create the file upload mode for skill submission.

CONTEXT:
- Second of three submission modes
- Drag-drop .md file, parse, validate, preview

Requirements:
1. Create apps/web/src/components/submission/FileUploadMode.tsx:
   - Props: onContentChange(content: string), initialContent (string, optional)
   - Drop zone with visual feedback:
     * Dashed border, "Drop .md file here" text
     * Drag-over state: border color change, "Release to upload"
     * Accept only .md files (reject others with error message)
     * Max file size: 500KB
   - On file drop:
     * Read file content via FileReader
     * Call onContentChange with file content
     * Show filename and size as confirmation
   - After upload:
     * Show editable textarea with file content
     * FrontMatterValidator runs automatically
     * SkillPreviewPanel shows live preview
   - "Replace file" button to upload a different file
   - "Clear" button to reset

2. File validation:
   - Must be .md extension
   - Must be under 500KB
   - Must contain front matter delimiters (warning if missing, not blocking)
   - UTF-8 encoding assumed

Write tests FIRST for:
- Drop zone renders with correct text
- Drag-over state changes visual feedback
- .md file accepted and content read
- Non-.md file rejected with error
- File over 500KB rejected with error
- Content appears in textarea after upload
- onContentChange called with file content
- Replace file works
- Clear button resets state
- Missing front matter shows warning

Do NOT:
- Create MCPSyncMode or SubmitSkillPage
- Add API calls
- Handle binary files

Acceptance Criteria:
- [ ] Drag-and-drop works
- [ ] File validation works
- [ ] Content displayed and editable after upload
- [ ] All tests pass
- [ ] Accessible: drop zone has aria-label, keyboard accessible
```

---

#### Prompt C.2.3 — MCPSyncMode: URL-based introspection

```
Create the MCP sync mode for skill submission (under "Advanced" disclosure).

CONTEXT:
- Third submission mode, hidden under an "Advanced" disclosure/accordion
- Takes an MCP server URL, introspects available tools, and generates SKILL.md

Requirements:
1. Create apps/web/src/components/submission/MCPSyncMode.tsx:
   - Props: onContentChange(content: string)
   - Initially hidden behind "Advanced: Import from MCP Server" disclosure
   - Workflow:
     * Step 1: URL input + "Introspect" button
     * Step 2: Display discovered tools/resources from server
     * Step 3: User selects which tool to import
     * Step 4: Auto-generate SKILL.md front matter + content from tool metadata
   - URL validation: must be valid URL, https preferred (warn on http)
   - Introspection call: POST /api/v1/mcp/introspect { url: string }
     (new backend endpoint)
   - Display tool list: name, description, input schema summary
   - "Select" button per tool -> generate SKILL.md content
   - Generated content editable in textarea
   - Loading state during introspection
   - Error state: connection failed, invalid response, timeout

2. New backend endpoint: POST /api/v1/mcp/introspect
   - Auth required
   - Body: { url: string }
   - Attempts MCP handshake with the given URL
   - Returns: { tools: [{ name, description, input_schema }],
     resources: [{ uri, name, description }] }
   - Timeout: 10 seconds
   - Returns 502 if server unreachable
   - Returns 422 if URL invalid

3. SKILL.md generation from tool metadata:
   - Front matter: name from tool name, description from tool description,
     category guessed from tool name (default "automation"),
     install_method: "mcp", version: "1.0.0"
   - Content: tool description, input parameters documentation,
     usage example template

Write tests FIRST for:
- Disclosure initially collapsed
- Disclosure expands on click
- URL input validates format
- Introspect button disabled for invalid URL
- Loading state shown during introspection
- Tool list rendered after successful introspection
- Error state on failed introspection
- Selecting tool generates SKILL.md
- Generated content is editable
- onContentChange called with generated content
- Backend: introspect endpoint returns tool list
- Backend: 422 for invalid URL
- Backend: 502 for unreachable server
- Backend: auth required

Do NOT:
- Create SubmitSkillPage wrapper
- Implement full MCP protocol (just list_tools is sufficient)
- Store MCP server credentials

Acceptance Criteria:
- [ ] Disclosure pattern works
- [ ] URL introspection flow complete
- [ ] Tool selection generates valid SKILL.md
- [ ] Backend endpoint works with auth
- [ ] Error handling for all failure modes
- [ ] All tests pass
```

---

### Phase C.3 — Submission Page Assembly

#### Prompt C.3.1 — SubmitSkillPage and ModeSelector

```
Assemble the complete skill submission page with mode selector, shared
validator/preview, and submit flow.

CONTEXT:
- Components built: FormBuilderMode, FileUploadMode, MCPSyncMode,
  FrontMatterValidator, SkillPreviewPanel
- See Section 4 of phase6-post-migration-diagrams.md for full hierarchy
- Architecture:
  SubmitSkillPage
    -> ModeSelector (tabs: Form | Upload | MCP Sync)
    -> [active mode] -> produces { content }
    -> FrontMatterValidator (shared)
    -> SkillPreviewPanel (shared, live)
    -> SubmitButton

Requirements:
1. Create apps/web/src/components/submission/ModeSelector.tsx:
   - Props: activeMode, onModeChange
   - Three tabs: "Form Builder" | "File Upload" | "MCP Sync"
   - MCP Sync tab has "Advanced" label/badge
   - Tab content switches between modes
   - Preserves content when switching modes (content state lifted to parent)

2. Create apps/web/src/views/SubmitSkillPage.tsx:
   - Route: /submit (add to React Router config)
   - Auth required (redirect to login if not authenticated)
   - Layout:
     * Top: page title "Submit a New Skill" + subtitle
     * Mode selector tabs
     * Main area: active mode component (left/top) +
       SkillPreviewPanel (right/bottom in split view)
     * Bottom-left: FrontMatterValidator inline
     * Bottom-right: Submit button
   - State management:
     * content: string (shared across modes)
     * mode: 'form' | 'upload' | 'mcp'
     * validationIssues: Issue[]
     * isSubmitting: boolean
   - Submit flow:
     * Button disabled if any validation errors (not warnings)
     * On click: POST /api/v1/submissions with assembled payload
     * Show SubmissionStatusTracker after submission
     * Handle 201 (success), 422 (validation), 500 (server error)

3. Create apps/web/src/components/submission/SubmissionStatusTracker.tsx:
   - Props: submissionId (string), displayId (string)
   - Polls GET /api/v1/submissions/{id} every 5 seconds
   - Shows: current status with progress indicator
   - Status stages: Submitted -> Gate 1 -> Gate 2 -> Awaiting Review
   - Completed: "Your skill is being reviewed by the team"
   - Failed: shows gate findings with suggestions

4. Update React Router in App.tsx to add /submit route.

Write tests FIRST for:
- ModeSelector renders three tabs
- ModeSelector switches active mode
- Content preserved when switching modes
- SubmitSkillPage renders with all components
- Submit button disabled when validation errors present
- Submit button enabled when no errors
- Submission API call on submit
- SubmissionStatusTracker polls for status
- SubmissionStatusTracker shows progress stages
- Redirect to login when not authenticated
- Error handling for failed submission

Do NOT:
- Modify existing views
- Add admin-specific submission flow (that's the same flow, different approval)
- Implement LLM judge live hints yet (next prompt)

Acceptance Criteria:
- [ ] Full submission page renders with mode selector
- [ ] Content flows from mode -> validator + preview
- [ ] Submit calls API and shows tracker
- [ ] Route added and accessible
- [ ] All tests pass
- [ ] Responsive layout works
```

---

#### Prompt C.3.2 — LLM Judge live hints during editing

> **Note:** The preview-scan endpoint (`POST /api/v1/submissions/preview-scan`) accepts
> `{ content, name, category }` and returns LLM suggestions (category recommendation,
> quality score, tagging hints) without creating a submission row. Rate-limited to
> prevent abuse. This is NOT the same as the admin-only scan endpoint.

```
Add live LLM judge feedback during skill editing (non-blocking hints,
not a gate).

CONTEXT:
- Existing LLM judge service: apps/fast-api/skillhub/services/llm_judge.py
- FrontMatterValidator already provides structural validation
- LLM judge provides content quality feedback (different from structural)
- Must be async with debounce — never block the editor

Requirements:
1. New backend endpoint: POST /api/v1/submissions/preview-judge
   - Auth required
   - Body: { content: string }
   - Runs a lightweight version of the LLM judge (Gate 2 style)
   - Returns: { hints: [{ severity: 'suggestion'|'warning', message: string,
     category: string }] }
   - Rate limited: max 1 request per user per 10 seconds (server-side)
   - Timeout: 15 seconds (do not block if LLM is slow)
   - Returns partial results if timeout (whatever hints were generated)

2. Create apps/web/src/hooks/useJudgeHints.ts:
   - Custom hook: useJudgeHints(content: string)
   - Returns: { hints: Hint[], isLoading: boolean, error: string|null }
   - Debounces 3 seconds after last content change
   - Aborts previous request on new content change (AbortController)
   - Caches results by content hash (avoid re-fetching same content)
   - Falls back gracefully on error (empty hints, no error shown to user)

3. Integrate hints into SubmitSkillPage:
   - Show hints below FrontMatterValidator
   - Hint display: light yellow background for suggestions,
     light orange for warnings
   - Hints are advisory only — do NOT block submission
   - "AI Suggestions" section header with dismiss-all button
   - Individual dismiss per hint

Write tests FIRST for:
- useJudgeHints debounces requests
- useJudgeHints aborts previous request
- useJudgeHints caches by content hash
- useJudgeHints handles errors gracefully
- Backend endpoint rate-limits correctly
- Backend endpoint returns hints
- Backend endpoint times out gracefully
- Hints rendered in SubmitSkillPage
- Hints dismissable individually and all-at-once
- Hints do NOT block submit button

Do NOT:
- Modify the structural FrontMatterValidator
- Make hints blocking
- Change the LLM judge gate logic (this is a separate lightweight call)

Acceptance Criteria:
- [ ] Live hints appear during editing
- [ ] 3-second debounce works
- [ ] Rate limiting on backend
- [ ] Hints are non-blocking
- [ ] Dismiss functionality works
- [ ] All tests pass
- [ ] Falls back gracefully on LLM errors
```

---

#### Prompt C.3.3 — Upload endpoint and multipart submission

```
Add the file upload submission endpoint and wire the FileUploadMode to use it.

CONTEXT:
- FileUploadMode reads files client-side, but we also need a server-side upload
  path for larger files or direct submission without client-side processing
- Existing: POST /api/v1/submissions (JSON body)

Requirements:
1. New endpoint: POST /api/v1/submissions/upload
   - Auth required
   - Content-Type: multipart/form-data
   - Fields:
     * file: .md file upload (required)
     * declared_divisions: JSON string array
     * division_justification: string
   - Server-side processing:
     * Read file content
     * Parse front matter for name, short_desc, category
     * Validate front matter (same rules as client-side)
     * Compute content_hash
     * Create Submission (reuse create_submission service)
     * Run Gate 1
   - Max file size: 500KB (reject larger with 413)
   - Only .md files accepted (reject others with 415)
   - Returns: SubmissionCreateResponse

2. Update FileUploadMode to offer two paths:
   - "Submit" button uses the existing JSON endpoint (content already parsed)
   - "Direct Upload" button uses the new multipart endpoint
   - Both end up at the same SubmissionStatusTracker

3. Add file size and type validation on the backend:
   - 413 Payload Too Large for > 500KB
   - 415 Unsupported Media Type for non-.md files
   - 422 for missing/invalid front matter

Write tests FIRST for:
- Upload endpoint: 201 with valid .md file
- Upload endpoint: 413 for oversized file
- Upload endpoint: 415 for wrong file type
- Upload endpoint: 422 for missing front matter
- Upload endpoint: auth required
- Upload endpoint: creates submission with correct fields
- Upload endpoint: Gate 1 runs
- FileUploadMode: both submission paths work

Do NOT:
- Add multipart support to other endpoints
- Store uploaded files permanently (content goes into Submission.content)
- Allow binary file uploads

Acceptance Criteria:
- [ ] Upload endpoint handles multipart correctly
- [ ] File validation works (size, type, content)
- [ ] Front matter parsed server-side
- [ ] Submission created through normal pipeline
- [ ] All tests pass
- [ ] 413/415/422 error codes correct
```

---

## 6.5 — New API Endpoints Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/submissions/{display_id}/resubmit | submission owner | Resubmit with updated content after change request |
| GET | /api/v1/submissions/{display_id}/audit-log | owner or platform_team | Audit log of state transitions |
| GET | /api/v1/submissions/{display_id}/diff | platform_team | Diff hunks for a specific revision |
| POST | /api/v1/skills/{skill_id}/versions | skill owner or platform_team | Submit a version update for a published skill |
| GET | /api/v1/skills/{skill_id}/versions | public (division-scoped) | List all versions of a skill |
| POST | /api/v1/mcp/introspect | auth required | Introspect an MCP server URL for tools/resources |
| POST | /api/v1/submissions/upload | auth required | Multipart .md file upload submission |
| POST | /api/v1/submissions/preview-judge | auth required | LLM Judge live hints during editing |
| POST | /api/v1/submissions/preview-scan | auth required | Stage C LLM Judge live assist — returns suggestions without creating a submission |

---

## Open Design Questions

These questions are flagged for human decision. Agent should implement the
default behavior noted, but structure code to allow easy configuration changes.

```
1. Max revision rounds before auto-reject?
   DEFAULT: 3 rounds, then soft escalation prompt (not auto-reject)
   CONFIG: SKILLHUB_MAX_REVISION_ROUNDS env var, default 3
   BEHAVIOR: At max rounds, add escalation_recommended to transition metadata.
   Admin can still approve/request-changes. No auto-reject.

2. Dual approval for admin submissions?
   DEFAULT: Admin submissions require approval from a DIFFERENT admin
   CONFIG: SKILLHUB_REQUIRE_DUAL_APPROVAL feature flag, default true
   BEHAVIOR: Submitter cannot be the reviewer. If only 1 admin, skip check.

3. Should REJECTED allow one appeal?
   DEFAULT: No appeal. REJECTED is terminal.
   CONFIG: SKILLHUB_ALLOW_APPEAL feature flag, default false
   BEHAVIOR: When enabled, add "Appeal" action on rejected submissions.
   Creates new submission linked via parent_submission_id.

4. VitePress content ownership?
   DEFAULT: Docs content managed via git (not CMS).
   No runtime editing. Changes require PR + deploy.

5. MCP Sync: full introspection vs URL-only?
   DEFAULT: URL + list_tools only (no full protocol).
   CONFIG: SKILLHUB_MCP_FULL_INTROSPECTION feature flag, default false
   BEHAVIOR: When enabled, also fetch resources and prompts.

6. display_id vs UUID in Phase 6 endpoint URLs?
   RESOLVED: New Phase 6 user-facing submission endpoints use display_id in
   URLs (resubmit, audit-log). Internal/admin endpoints (diff) use UUID.
   Add get_submission_by_display_id(db, display_id) helper to submissions service.
```

---

## Quick Reference: Prompt Sequence

```
STAGE A — Admin HITL Queue Enhancements (8 prompts)
  A.1.1  submission_state_transitions model
  A.1.2  Submission model extensions (revision, versioning columns)
  A.2.1  Revision state machine + resubmit service
  A.2.2  Resubmit and audit-log API endpoints
  A.3.1  Extract ModalShell from AdminConfirmDialog
  A.3.2  RequestChangesModal component
  A.3.3  RejectModal component
  A.4.1  SubmissionCard + RevisionBadge
  A.4.2  Integrate cards and modals into AdminQueueView
  A.5.1  AuditLogPanel component
  A.6.1  Version submission service + endpoint
  A.6.2  VersionSelector + VersionDiffView components

STAGE B — User Documentation via VitePress (5 prompts)
  B.1.1  VitePress scaffold in NX monorepo
  B.1.2  Nginx + Docker integration
  B.2.1  Getting Started + Intro + Uses pages
  B.2.2  Discovery + Social + Advanced pages
  B.2.3  Submission guide + FAQ + Resources pages

STAGE C — User Skill Submission UI/UX (6 prompts)
  C.1.1  FrontMatterValidator component
  C.1.2  SkillPreviewPanel component
  C.2.1  FormBuilderMode: guided wizard
  C.2.2  FileUploadMode: drag-and-drop
  C.2.3  MCPSyncMode: URL introspection
  C.3.1  SubmitSkillPage + ModeSelector + StatusTracker
  C.3.2  LLM Judge live hints
  C.3.3  Upload endpoint + multipart submission

TOTAL: 23 prompts across 3 stages
```

### Dependency Graph

```
A.1.1 → A.1.2 → A.2.1 → A.2.2
                       ↘
A.3.1 → A.3.2 → A.3.3 → A.4.1 → A.4.2
                                      ↘
                              A.5.1 → A.6.1 → A.6.2

B.1.1 → B.1.2
B.1.1 → B.2.1 → B.2.2 → B.2.3

C.1.1 ──→ C.2.1 ──→ C.3.1
C.1.2 ──↗ C.2.2 ──↗ C.3.2
           C.2.3 ──↗ C.3.3

Stages A, B, C are independent of each other and can be parallelized.
Within each stage, follow the prompt order.
```
