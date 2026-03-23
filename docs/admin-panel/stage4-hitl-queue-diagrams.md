# Stage 4: HITL Review Queue — Visual Architecture Companion

Mermaid diagrams for the HITL submission approval workflow.

---

## Diagram 1: Submission State Machine (Gate 3 Focus)

```mermaid
stateDiagram-v2
    direction LR

    [*] --> submitted
    submitted --> gate1_passed : Gate 1 pass
    submitted --> gate1_failed : Gate 1 fail
    gate1_passed --> gate2_passed : Gate 2 pass (score ≥ threshold)
    gate1_passed --> gate2_flagged : Gate 2 flagged (score borderline)
    gate1_passed --> gate2_failed : Gate 2 fail (score < min)

    state "Gate 3 Eligible" as g3 {
        gate2_passed
        gate2_flagged
    }

    gate2_passed --> approved : reviewer: approve
    gate2_passed --> rejected : reviewer: reject
    gate2_passed --> gate3_changes_requested : reviewer: request_changes

    gate2_flagged --> approved : reviewer: approve
    gate2_flagged --> rejected : reviewer: reject
    gate2_flagged --> gate3_changes_requested : reviewer: request_changes

    gate3_changes_requested --> gate2_passed : submitter resubmits
    approved --> published : admin publishes

    gate1_failed --> [*]
    gate2_failed --> [*]
    rejected --> [*]
```

---

## Diagram 2: Claim + Decision Sequence

```mermaid
sequenceDiagram
    participant UI as AdminQueueView
    participant Hook as useAdminQueue
    participant API as FastAPI Router
    participant Svc as review_queue service
    participant DB as PostgreSQL

    UI->>Hook: claimItem(submission_id)
    Hook->>API: POST /api/v1/admin/review-queue/{id}/claim
    API->>Svc: claim_submission(db, submission_id, reviewer_id)
    Svc->>DB: SELECT ... FOR UPDATE SKIP LOCKED
    DB-->>Svc: Submission row (or null if locked)
    alt submission locked by another reviewer
        Svc-->>API: ValueError("locked")
        API-->>Hook: 404
        Hook-->>UI: error state
    else submission available
        Svc->>DB: UPDATE submissions SET gate3_reviewer_id = reviewer_id
        Svc->>DB: INSERT INTO audit_log (event_type='submission.gate3.claimed')
        DB-->>Svc: ok
        Svc-->>API: ClaimResponse
        API-->>Hook: 200 ClaimResponse
        Hook-->>UI: claimed_at timestamp
    end

    UI->>Hook: decideItem(submission_id, {decision, notes, score})
    Hook->>API: POST /api/v1/admin/review-queue/{id}/decision
    API->>Svc: decide_submission(db, ...)

    alt decision = "approve"
        Svc->>DB: UPDATE submissions SET status='approved', gate3_reviewed_at, gate3_notes
        Svc->>DB: INSERT INTO submission_gate_results (gate=3, result='passed')
        Svc->>DB: INSERT INTO audit_log (event_type='submission.approved')
    else decision = "reject"
        Svc->>DB: UPDATE submissions SET status='rejected'
        Svc->>DB: INSERT INTO submission_gate_results (gate=3, result='failed', findings)
        Svc->>DB: INSERT INTO audit_log (event_type='submission.rejected')
    else decision = "request_changes"
        Svc->>DB: UPDATE submissions SET status='gate3_changes_requested'
        Svc->>DB: INSERT INTO audit_log (event_type='submission.changes_requested')
    end

    Svc-->>API: DecisionResponse
    API-->>Hook: 200 DecisionResponse
    Hook->>Hook: refetch()
    Hook-->>UI: updated queue
    UI->>UI: announce(message)
    UI->>UI: focusItem(nextIndex)
```

---

## Diagram 3: Frontend Component Tree

```mermaid
graph TD
    App["App.tsx\n(BrowserRouter)"]
    AppShell["AppShell"]
    Nav["Nav"]
    Routes["Routes"]
    AQV["AdminQueueView\n/admin/queue"]
    ACD["AdminConfirmDialog\n(conditional)"]
    RP["RejectPanel\n(conditional)"]
    KL["KeyboardLegend\n(conditional)"]
    ANN["Announcer\naria-live=polite"]
    SLB["SlaBadge\n(per item)"]
    STB["StatusBadge\n(per item)"]

    App --> AppShell
    AppShell --> Nav
    AppShell --> Routes
    Routes --> AQV
    AQV --> ACD
    AQV --> RP
    AQV --> KL
    AQV --> ANN
    AQV --> SLB
    AQV --> STB

    style AQV fill:#1a2a40,color:#ddeaf7
    style ACD fill:#1a2a40,color:#ddeaf7
    style RP fill:#1a2a40,color:#ddeaf7
```

---

## Diagram 4: Master-Detail Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Nav (60px, fixed)                                                   │
└─────────────────────────────────────────────────────────────────────┘
┌────────────────────────┬────────────────────────────────────────────┐
│  Queue List (380px)    │  Detail Panel (flex-1)                     │
│  ─────────────────     │  ─────────────────────────────────────     │
│  role="grid"           │                                            │
│  aria-rowcount=N       │  [Skill Name]        [Approve] [Reject]    │
│                        │  SKL-001  v1.0.0     [Request Changes]     │
│  ┌──────────────────┐  │                                            │
│  │ SKL-001  [SLA⚠]  │  │  Submitted by Alice · 30h ago             │
│  │ My Test Skill    │  │                                            │
│  │ Alice · 30h ago  │  │  ┌──────────────┬───────────────────────┐ │
│  └──────────────────┘  │  │ GATE 1       │ GATE 2                │ │
│  ┌──────────────────┐  │  │ Content      │ LLM Score             │ │
│  │ SKL-002          │  │  │ Passed       │ 82/100                │ │
│  │ Other Skill      │  │  │              │ "Solid implementation"│ │
│  │ Bob · 2h ago     │  │  └──────────────┴───────────────────────┘ │
│  └──────────────────┘  │                                            │
│                        │  Content Preview                           │
│  [?] keyboard legend   │  ┌────────────────────────────────────┐   │
│                        │  │ This is the skill content preview… │   │
│                        │  └────────────────────────────────────┘   │
└────────────────────────┴────────────────────────────────────────────┘
  ← 380px →              ← flex-1 →
```

---

## Diagram 5: Keyboard Navigation Map

```
Global keydown handler (fires when activeElement is NOT input/textarea)
│
├── J ──────────────── focusItem(selectedIndex + 1)
│                      selectItem(items[next].submission_id)
│                      → URL: /admin/queue?id=<next-uuid>
│
├── K ──────────────── focusItem(selectedIndex - 1)
│                      selectItem(items[prev].submission_id)
│
├── A ──────────────── if isSelfSubmission → announce("You cannot approve...")
│                      else → setShowConfirm(true)
│                             [AdminConfirmDialog opens]
│
├── Shift+A ─────────── if batchSelected.size > 0 → handleBatchApprove()
│                       (processes up to 20 items sequentially)
│
├── R ──────────────── setShowRejectPanel(true)
│                      [RejectPanel opens with textarea]
│
├── X ──────────────── toggle selectedId in batchSelected Set
│                      (NOT Space — avoids page scroll conflict)
│
├── ? ──────────────── setShowLegend(true/false)
│
└── Escape ──────────── close all modals
                        setShowConfirm(false)
                        setShowRejectPanel(false)
                        setShowLegend(false)
                        confirmTriggerRef.current?.focus()
```

---

## Diagram 6: Self-Approval Guard — Frontend Decision Tree

```
User clicks "Approve" button
          │
          ▼
  isSelfSubmission?
   (submitter_id === user.user_id)
          │
    ┌─────┴─────┐
   YES          NO
    │            │
    ▼            ▼
announce(     setShowConfirm(true)
 "You cannot      │
  approve your    ▼
  own           AdminConfirmDialog
  submission.") opens (destructive=false)
                  │
           User confirms?
            ┌────┴────┐
           YES        NO
            │          │
            ▼          ▼
         claimItem  dialog closes
            +       focus restored
         decideItem    to trigger
         {approve}
            │
            ▼
         announce(
          "Submission approved.
           N items remaining.")
            │
            ▼
         focusItem(nextIndex)
```

---

## Diagram 7: Self-Approval Guard — Backend Decision Tree

```
POST /api/v1/admin/review-queue/{id}/decision
 body: { decision: "approve" }
          │
          ▼
  require_platform_team
  dependency validates JWT
          │
          ▼
  decide_submission(
    reviewer_id = UUID(current_user["user_id"])
  )
          │
          ▼
  Load submission from DB
          │
          ▼
  sub.submitted_by == reviewer_id?
    ┌─────┴─────┐
   YES          NO
    │            │
    ▼            ▼
  raise        proceed with
  PermissionError  decision logic
  "Cannot approve
   own submission"
          │
  HTTP 403 returned
```

---

## Diagram 8: Concurrent Claim Safety (SELECT FOR UPDATE SKIP LOCKED)

```
Time ──────────────────────────────────────────────────────────────►

Reviewer A                     DB Transaction A
──────────                     ─────────────────
claimItem(sub-001)  ─────────► BEGIN
                               SELECT * FROM submissions
                               WHERE id = sub-001
                               FOR UPDATE SKIP LOCKED
                               → Row acquired ✓
                               UPDATE gate3_reviewer_id = reviewer_a
                               COMMIT

Reviewer B (concurrent)        DB Transaction B
───────────────────            ─────────────────
claimItem(sub-001)  ─────────► BEGIN
                               SELECT * FROM submissions
                               WHERE id = sub-001
                               FOR UPDATE SKIP LOCKED
                               → Row is locked → SKIPPED
                               → scalar_one_or_none() returns None
                               ← ValueError("not found or locked")
                  ◄──────────  HTTP 404

Result: sub-001 claimed by Reviewer A only.
        Reviewer B sees 404 and must pick another item.
```

---

## Diagram 9: SLA Badge Logic

```
wait_time_hours = (now - submitted_at).total_seconds() / 3600

       0h ──────── 24h ─────── 48h ───────────────►

       [  no badge  ][ SLA at risk ][ SLA breached ]
                       amber badge    red badge
                    amberDim bg      redDim bg
                    C.amber text     C.red text
```

---

## Diagram 10: Database Schema — New Columns in Context

```
submissions
┌─────────────────────────────┬──────────────────────────┬──────────┐
│ Column                      │ Type                     │ Nullable │
├─────────────────────────────┼──────────────────────────┼──────────┤
│ id (PK)                     │ UUID                     │ NO       │
│ display_id                  │ VARCHAR(10) UNIQUE       │ NO       │
│ skill_id (FK skills.id)     │ UUID                     │ YES      │
│ submitted_by (FK users.id)  │ UUID                     │ NO       │
│ name                        │ VARCHAR(255)             │ NO       │
│ short_desc                  │ VARCHAR(255)             │ NO       │
│ category                    │ VARCHAR(100)             │ NO       │
│ content                     │ TEXT                     │ NO       │
│ declared_divisions          │ JSON                     │ NO       │
│ division_justification      │ TEXT                     │ NO       │
│ status                      │ VARCHAR(30)              │ NO       │
│ ══════════════ NEW ════════ │ ════════════════════════ │          │
│ gate3_reviewer_id           │ UUID (FK users.id)       │ YES  ←── │
│ gate3_reviewed_at           │ TIMESTAMPTZ              │ YES  ←── │
│ gate3_notes                 │ TEXT                     │ YES  ←── │
│ ════════════════════════════│ ════════════════════════ │          │
│ created_at                  │ TIMESTAMPTZ              │ NO       │
│ updated_at                  │ TIMESTAMPTZ              │ NO       │
└─────────────────────────────┴──────────────────────────┴──────────┘

Index: ix_submissions_gate3_reviewer_id on (gate3_reviewer_id)

submission_gate_results (existing — gate=3 rows created by this stage)
┌─────────────────────────────┬──────────────────────────┬──────────┐
│ Column                      │ Type                     │ Nullable │
├─────────────────────────────┼──────────────────────────┼──────────┤
│ id (PK)                     │ UUID                     │ NO       │
│ submission_id (FK)          │ UUID                     │ NO       │
│ gate                        │ INTEGER (= 3)            │ NO       │
│ result                      │ VARCHAR(10)              │ NO       │
│ findings                    │ JSON                     │ YES      │
│ score                       │ INTEGER                  │ YES      │
│ reviewer_id (FK users.id)   │ UUID                     │ YES      │
│ created_at                  │ TIMESTAMPTZ              │ NO       │
└─────────────────────────────┴──────────────────────────┴──────────┘
```

---

## Diagram 11: API Endpoint Map (Stage 4 additions)

```
/api/v1/admin/review-queue
│
├── GET  /
│        Auth:    require_platform_team
│        Params:  page, per_page
│        Returns: ReviewQueueResponse (paginated fat objects)
│        Service: get_review_queue()
│
├── POST /{submission_id}/claim
│        Auth:    require_platform_team
│        Body:    (none)
│        Returns: ClaimResponse
│        Service: claim_submission() — SELECT FOR UPDATE SKIP LOCKED
│        Errors:  403 (self-claim), 404 (not found/locked)
│
└── POST /{submission_id}/decision
         Auth:    require_platform_team
         Body:    DecisionRequest {decision, notes, score}
         Returns: DecisionResponse
         Service: decide_submission()
         Errors:  403 (self-approve), 422 (short reject notes / bad decision)
```

---

## Diagram 12: Review Queue Data Flow — Full Picture

```
PostgreSQL
  submissions
  (status IN
   gate2_passed,
   gate2_flagged)
        │
        │ get_review_queue()
        │ ORDER BY created_at ASC
        │ + join user names
        │ + join gate_results
        │
        ▼
FastAPI /api/v1/admin/review-queue GET
        │
        │ ReviewQueueResponse JSON
        │
        ▼
useAdminQueue hook (React)
  data.items: ReviewQueueItem[]
        │
        ▼
AdminQueueView
  ┌─────────────────────────┐
  │  Queue List (role=grid) │
  │  - Item rows            │
  │  - SLA badges           │
  │  - Claimed indicator    │
  └────────────┬────────────┘
               │ user selects item
               │ setSearchParams({id}, replace: true)
               ▼
  ┌─────────────────────────┐
  │  Detail Panel           │
  │  - Gate 1 / 2 results  │
  │  - Content preview      │
  │  - Action buttons       │
  └────────────┬────────────┘
               │
     ┌─────────┼──────────────┐
     ▼         ▼              ▼
  Approve   Reject     Request Changes
     │         │              │
     ▼         ▼              ▼
AdminConfirm RejectPanel  immediate POST
Dialog      (textarea,    /decision
(focuses     min 10 chars)  {request_changes}
 Cancel if
 destructive)
     │         │
     ▼         ▼
POST /claim   POST /claim
POST /decision POST /decision
{approve}     {reject, notes}
     │         │
     └────┬────┘
          ▼
       refetch()
       announce()
       focusItem(next)
```
