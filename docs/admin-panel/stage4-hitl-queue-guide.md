# Stage 4: HITL Review Queue — Submission Approval Workflow

**Admin Panel Technical Implementation Guide**
Date: 2026-03-23
Prerequisites: Stages 1–3 complete (AdminShell, Audit Log, User Management)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture Decision Record](#2-architecture-decision-record)
3. [File Map](#3-file-map)
4. [Task Breakdown](#4-task-breakdown)
5. [Backend: DB Model Extension](#5-backend-db-model-extension)
6. [Backend: Alembic Migration](#6-backend-alembic-migration)
7. [Backend: Pydantic Schemas](#7-backend-pydantic-schemas)
8. [Backend: Review Queue Service](#8-backend-review-queue-service)
9. [Backend: Review Queue Router](#9-backend-review-queue-router)
10. [Frontend: useAdminQueue Hook](#10-frontend-useadminqueue-hook)
11. [Frontend: AdminConfirmDialog Component](#11-frontend-adminconfirmdialog-component)
12. [Frontend: AdminQueueView](#12-frontend-adminqueueview)
13. [Frontend: App.tsx Route Registration](#13-frontend-apptsx-route-registration)
14. [Testing: Backend](#14-testing-backend)
15. [Testing: Frontend](#15-testing-frontend)
16. [Verification Checklist](#16-verification-checklist)
17. [SLA Badge Reference](#17-sla-badge-reference)
18. [Accessibility Contract](#18-accessibility-contract)

---

## 1. Overview

Stage 4 implements the Human-in-the-Loop (HITL) review queue: the final gate before a skill reaches `approved` status. After Gate 1 (content validation) and Gate 2 (LLM scoring), submissions enter Gate 3 where platform-team reviewers claim, inspect, and decide on each submission.

### State machine (relevant transitions for this stage)

```
gate2_passed  ──claim──►  gate2_passed (reviewer claimed, gate3_reviewer_id set)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
           approved        rejected    gate3_changes_requested
```

Claiming is a soft lock (SELECT FOR UPDATE SKIP LOCKED). It does NOT change submission status — it only sets `gate3_reviewer_id`. The decision step transitions status.

### Self-approval protection

The service raises `PermissionError` when `submission.submitted_by == reviewer_id`. The frontend mirrors this with `aria-disabled="true"` on the approve button for owned submissions — the button stays focusable and announces the constraint rather than silently hiding.

---

## 2. Architecture Decision Record

| Decision | Choice | Rationale |
|---|---|---|
| Concurrency model | `SELECT FOR UPDATE SKIP LOCKED` | Prevents double-claim without blocking; reviewers see only unclaimed items |
| Claim semantics | Soft lock (sets reviewer_id only, no status change) | Claim can be abandoned; status is only mutated by a definitive decision |
| Self-approval check | Service layer, not DB constraint | Tested in isolation; DB constraint would complicate seeding |
| Frontend routing | `?id=<uuid>` query param, `replace: true` | Avoids Back-button pollution; deep-linkable without extra route segment |
| Keyboard shortcuts | J/K/A/R/X/Shift+A (not Space for batch) | Space conflicts with page scroll; matches vim-style reviewer muscle memory |
| aria-disabled vs disabled | `aria-disabled="true"` on self-approve | Keeps button reachable by keyboard; screen reader can announce the constraint |
| Batch limit | 20 items | Prevents accidental bulk approvals; matches typical review session size |

---

## 3. File Map

### New files to create

```
libs/db/migrations/versions/<rev>_add_gate3_reviewer_fields.py
apps/api/skillhub/services/review_queue.py
apps/api/skillhub/routers/review_queue.py
apps/api/skillhub/schemas/review_queue.py
apps/api/tests/test_review_queue_service.py
apps/api/tests/test_review_queue_router.py
apps/web/src/hooks/useAdminQueue.ts
apps/web/src/components/admin/AdminConfirmDialog.tsx
apps/web/src/views/admin/AdminQueueView.tsx
apps/web/src/__tests__/AdminQueueView.test.tsx
```

### Files to modify

```
libs/db/skillhub_db/models/submission.py         — add 3 columns
apps/api/skillhub/main.py                        — include review_queue router
apps/web/src/App.tsx                             — add /admin/queue route
```

---

## 4. Task Breakdown

Each task is designed to be completable in 2–5 minutes following RED-GREEN-REFACTOR.

| # | Task | TDD phase |
|---|---|---|
| 4.1 | Extend Submission model + write migration | Model first, migration after model tests pass |
| 4.2 | Write schema file `review_queue.py` | Types before service |
| 4.3 | Write `test_review_queue_service.py` (RED) | All tests fail initially |
| 4.4 | Implement `services/review_queue.py` (GREEN) | Make service tests pass |
| 4.5 | Write `test_review_queue_router.py` (RED) | Router tests fail |
| 4.6 | Implement `routers/review_queue.py` (GREEN) | Make router tests pass |
| 4.7 | Register router in `main.py` | Integration check |
| 4.8 | Write `AdminQueueView.test.tsx` (RED) | Frontend tests fail |
| 4.9 | Implement `useAdminQueue.ts` | Hook tests pass |
| 4.10 | Implement `AdminConfirmDialog.tsx` | Component tests pass |
| 4.11 | Implement `AdminQueueView.tsx` (GREEN) | View tests pass |
| 4.12 | Register route in `App.tsx` | Smoke check |

---

## 5. Backend: DB Model Extension

**File:** `libs/db/skillhub_db/models/submission.py`

Add three columns to the `Submission` class after the `status` field:

```python
# Gate 3 human review fields
gate3_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("users.id"), nullable=True
)
gate3_reviewed_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True
)
gate3_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

The required imports are already present in the file (`ForeignKey`, `Text`, `DateTime`, `uuid`, `datetime`). No new imports needed.

The full `Submission` class after the edit:

```python
class Submission(UUIDMixin, TimestampMixin, Base):
    """Skill submission through the pipeline."""

    __tablename__ = "submissions"

    display_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"), nullable=True)
    submitted_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_desc: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    declared_divisions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    division_justification: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, native_enum=False, length=30),
        default=SubmissionStatus.SUBMITTED,
    )
    # Gate 3 human review fields
    gate3_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    gate3_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    gate3_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Submission {self.display_id}>"
```

---

## 6. Backend: Alembic Migration

**File:** `libs/db/migrations/versions/<timestamp>_add_gate3_reviewer_fields.py`

Generate the skeleton with:
```bash
cd libs/db && alembic revision --autogenerate -m "add_gate3_reviewer_fields"
```

Then verify/adjust the generated file to match exactly:

```python
"""add gate3 reviewer fields to submissions

Revision ID: <generated>
Revises: e20cb6415067
Create Date: <generated>
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "<generated>"
down_revision: Union[str, None] = "e20cb6415067"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column(
            "gate3_reviewer_id",
            sa.UUID(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "submissions",
        sa.Column(
            "gate3_reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "submissions",
        sa.Column("gate3_notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_submissions_gate3_reviewer_id",
        "submissions",
        ["gate3_reviewer_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_submissions_gate3_reviewer_id", table_name="submissions")
    op.drop_column("submissions", "gate3_notes")
    op.drop_column("submissions", "gate3_reviewed_at")
    op.drop_column("submissions", "gate3_reviewer_id")
```

Apply with:
```bash
cd libs/db && alembic upgrade head
```

---

## 7. Backend: Pydantic Schemas

**File:** `apps/api/skillhub/schemas/review_queue.py`

```python
"""Pydantic v2 schemas for the HITL review queue endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GateResultSummary(BaseModel):
    """Flattened gate result embedded in queue items."""

    gate: int
    result: str
    score: int | None = None
    summary: str | None = None  # from findings["summary"] for gate 2
    findings: dict | None = None


class ReviewQueueItem(BaseModel):
    """Fat object returned by the review queue — everything a reviewer needs."""

    model_config = ConfigDict(from_attributes=True)

    submission_id: UUID
    display_id: str
    skill_name: str
    version: str
    submitter_id: UUID
    submitter_name: str | None = None
    submitted_at: datetime
    gate1_passed: bool
    gate2_score: int | None = None
    gate2_summary: str | None = None
    content_preview: str  # first 500 chars
    wait_time_hours: float
    gate3_reviewer_id: UUID | None = None


class ReviewQueueResponse(BaseModel):
    """Paginated review queue response."""

    items: list[ReviewQueueItem]
    total: int
    page: int
    per_page: int
    has_more: bool


class ClaimResponse(BaseModel):
    """Returned after claiming a submission."""

    submission_id: UUID
    display_id: str
    claimed_by: UUID
    claimed_at: datetime


class DecisionRequest(BaseModel):
    """Body for POST .../decision."""

    decision: Literal["approve", "reject", "request_changes"]
    notes: str = Field(default="", description="Required for reject (min 10 chars enforced in service)")
    score: int | None = Field(default=None, ge=0, le=100)


class DecisionResponse(BaseModel):
    """Returned after a decision is recorded."""

    submission_id: UUID
    display_id: str
    new_status: str
    decided_by: UUID
    decided_at: datetime
    gate_result_id: UUID | None = None
```

---

## 8. Backend: Review Queue Service

**File:** `apps/api/skillhub/services/review_queue.py`

```python
"""HITL review queue service — claim and decide on gate3 submissions."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from opentelemetry import trace
from skillhub_db.models.audit import AuditLog
from skillhub_db.models.submission import (
    GateResult,
    Submission,
    SubmissionGateResult,
    SubmissionStatus,
)
from skillhub_db.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("skillhub.services.review_queue")

# Statuses that are eligible for gate3 human review
_GATE3_ELIGIBLE = {
    SubmissionStatus.GATE2_PASSED,
    SubmissionStatus.GATE2_FLAGGED,
}


def _write_audit(
    db: Session,
    *,
    event_type: str,
    actor_id: UUID,
    target_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    entry = AuditLog(
        id=uuid.uuid4(),
        event_type=event_type,
        actor_id=actor_id,
        target_type="submission",
        target_id=target_id,
        metadata_=metadata,
    )
    db.add(entry)


def get_review_queue(
    db: Session,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Return paginated submissions awaiting gate3, oldest first.

    Each item is a fat object with pre-resolved gate results and submitter name.
    """
    with tracer.start_as_current_span("service.review_queue.get_review_queue") as span:
        span.set_attribute("queue.page", page)

        query = db.query(Submission).filter(
            Submission.status.in_([s.value for s in _GATE3_ELIGIBLE])
        )
        total = query.count()
        span.set_attribute("queue.total", total)

        submissions = (
            query.order_by(Submission.created_at.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        # Bulk-resolve submitter names
        submitter_ids = {s.submitted_by for s in submissions}
        name_map: dict[UUID, str] = {}
        if submitter_ids:
            rows = db.query(User.id, User.name).filter(User.id.in_(submitter_ids)).all()
            name_map = {r.id: r.name for r in rows}

        # Bulk-fetch gate results for these submissions
        sub_ids = [s.id for s in submissions]
        gate_results: dict[UUID, list[SubmissionGateResult]] = {}
        if sub_ids:
            results = (
                db.query(SubmissionGateResult)
                .filter(SubmissionGateResult.submission_id.in_(sub_ids))
                .all()
            )
            for r in results:
                gate_results.setdefault(r.submission_id, []).append(r)

        now = datetime.now(timezone.utc)
        items: list[dict[str, Any]] = []
        for sub in submissions:
            results_for_sub = gate_results.get(sub.id, [])
            gate1_passed = any(
                r.gate == 1 and r.result == GateResult.PASSED for r in results_for_sub
            )
            gate2_row = next(
                (r for r in results_for_sub if r.gate == 2), None
            )
            gate2_score = gate2_row.score if gate2_row else None
            gate2_summary: str | None = None
            if gate2_row and gate2_row.findings:
                gate2_summary = gate2_row.findings.get("summary")

            submitted_at = sub.created_at
            if submitted_at and submitted_at.tzinfo is None:
                submitted_at = submitted_at.replace(tzinfo=timezone.utc)
            wait_hours = (
                (now - submitted_at).total_seconds() / 3600.0
                if submitted_at
                else 0.0
            )

            items.append(
                {
                    "submission_id": sub.id,
                    "display_id": sub.display_id,
                    "skill_name": sub.name,
                    "version": "1.0.0",  # submissions don't carry version; use default
                    "submitter_id": sub.submitted_by,
                    "submitter_name": name_map.get(sub.submitted_by),
                    "submitted_at": submitted_at,
                    "gate1_passed": gate1_passed,
                    "gate2_score": gate2_score,
                    "gate2_summary": gate2_summary,
                    "content_preview": (sub.content or "")[:500],
                    "wait_time_hours": round(wait_hours, 2),
                    "gate3_reviewer_id": sub.gate3_reviewer_id,
                }
            )

        return items, total


def claim_submission(
    db: Session,
    *,
    submission_id: UUID,
    reviewer_id: UUID,
) -> dict[str, Any]:
    """Soft-claim a submission using SELECT FOR UPDATE SKIP LOCKED.

    Sets gate3_reviewer_id. Does NOT change submission status.
    Raises ValueError if submission is not in a claimable state.
    Raises PermissionError if the reviewer is the submitter.
    """
    with tracer.start_as_current_span("service.review_queue.claim_submission") as span:
        span.set_attribute("queue.submission_id", str(submission_id))
        span.set_attribute("queue.reviewer_id", str(reviewer_id))

        stmt = (
            select(Submission)
            .where(Submission.id == submission_id)
            .with_for_update(skip_locked=True)
        )
        sub = db.execute(stmt).scalar_one_or_none()

        if sub is None:
            span.set_attribute("queue.result", "not_found_or_locked")
            raise ValueError("Submission not found or currently locked by another reviewer")

        if sub.status not in [s.value for s in _GATE3_ELIGIBLE]:
            span.set_attribute("queue.result", "not_eligible")
            raise ValueError(
                f"Submission {sub.display_id} is not eligible for gate3 review (status={sub.status})"
            )

        if sub.submitted_by == reviewer_id:
            span.set_attribute("queue.result", "self_claim")
            raise PermissionError("Cannot approve your own submission")

        claimed_at = datetime.now(timezone.utc)
        sub.gate3_reviewer_id = reviewer_id

        _write_audit(
            db,
            event_type="submission.gate3.claimed",
            actor_id=reviewer_id,
            target_id=str(sub.id),
            metadata={"display_id": sub.display_id},
        )

        db.commit()
        db.refresh(sub)

        span.set_attribute("queue.result", "claimed")
        return {
            "submission_id": sub.id,
            "display_id": sub.display_id,
            "claimed_by": reviewer_id,
            "claimed_at": claimed_at,
        }


def decide_submission(
    db: Session,
    *,
    submission_id: UUID,
    reviewer_id: UUID,
    decision: str,
    notes: str = "",
    score: int | None = None,
) -> dict[str, Any]:
    """Record a gate3 decision: approve, reject, or request_changes.

    Business rules:
    - Self-approval is blocked.
    - Reject requires notes (min 10 chars).
    - Approve creates gate_result(gate=3, result='pass') + transitions to 'approved'.
    - Reject creates gate_result(gate=3, result='fail') + transitions to 'rejected'.
    - request_changes transitions to 'gate3_changes_requested' (no gate_result row).
    All paths write an audit log entry.
    """
    with tracer.start_as_current_span("service.review_queue.decide_submission") as span:
        span.set_attribute("queue.submission_id", str(submission_id))
        span.set_attribute("queue.reviewer_id", str(reviewer_id))
        span.set_attribute("queue.decision", decision)

        sub = db.query(Submission).filter(Submission.id == submission_id).first()
        if not sub:
            span.set_attribute("queue.result", "not_found")
            raise ValueError("Submission not found")

        if sub.submitted_by == reviewer_id:
            span.set_attribute("queue.result", "self_approve")
            raise PermissionError("Cannot approve your own submission")

        if decision not in ("approve", "reject", "request_changes"):
            raise ValueError(f"Unknown decision: {decision!r}")

        if decision == "reject" and len(notes.strip()) < 10:
            raise ValueError("Rejection notes must be at least 10 characters")

        decided_at = datetime.now(timezone.utc)
        sub.gate3_reviewed_at = decided_at
        sub.gate3_notes = notes or None
        sub.gate3_reviewer_id = reviewer_id

        gate_result_row: SubmissionGateResult | None = None

        if decision == "approve":
            sub.status = SubmissionStatus.APPROVED
            gate_result_row = SubmissionGateResult(
                id=uuid.uuid4(),
                submission_id=sub.id,
                gate=3,
                result=GateResult.PASSED,
                score=score,
                reviewer_id=reviewer_id,
                findings={"notes": notes} if notes else None,
            )
            db.add(gate_result_row)
            _write_audit(
                db,
                event_type="submission.approved",
                actor_id=reviewer_id,
                target_id=str(sub.id),
                metadata={"display_id": sub.display_id, "score": score, "notes": notes},
            )

        elif decision == "reject":
            sub.status = SubmissionStatus.REJECTED
            gate_result_row = SubmissionGateResult(
                id=uuid.uuid4(),
                submission_id=sub.id,
                gate=3,
                result=GateResult.FAILED,
                score=score,
                reviewer_id=reviewer_id,
                findings={"reason": "rejected", "notes": notes},
            )
            db.add(gate_result_row)
            _write_audit(
                db,
                event_type="submission.rejected",
                actor_id=reviewer_id,
                target_id=str(sub.id),
                metadata={"display_id": sub.display_id, "notes": notes},
            )

        else:  # request_changes
            sub.status = SubmissionStatus.GATE3_CHANGES_REQUESTED
            _write_audit(
                db,
                event_type="submission.changes_requested",
                actor_id=reviewer_id,
                target_id=str(sub.id),
                metadata={"display_id": sub.display_id, "notes": notes},
            )

        db.commit()
        db.refresh(sub)

        span.set_attribute("queue.result", "success")
        return {
            "submission_id": sub.id,
            "display_id": sub.display_id,
            "new_status": sub.status.value if hasattr(sub.status, "value") else sub.status,
            "decided_by": reviewer_id,
            "decided_at": decided_at,
            "gate_result_id": gate_result_row.id if gate_result_row else None,
        }
```

---

## 9. Backend: Review Queue Router

**File:** `apps/api/skillhub/routers/review_queue.py`

```python
"""HITL review queue router — claim and decide on gate3 submissions."""

from __future__ import annotations

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_db, require_platform_team
from skillhub.schemas.review_queue import (
    ClaimResponse,
    DecisionRequest,
    DecisionResponse,
    ReviewQueueResponse,
)
from skillhub.services.review_queue import (
    claim_submission,
    decide_submission,
    get_review_queue,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin/review-queue", tags=["admin-review-queue"])


@router.get("", response_model=ReviewQueueResponse)
def list_review_queue(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> ReviewQueueResponse:
    """Return paginated submissions awaiting gate3 human review. Platform Team only."""
    items, total = get_review_queue(db, page=page, per_page=per_page)
    return ReviewQueueResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )


@router.post("/{submission_id}/claim", response_model=ClaimResponse)
def claim_queue_item(
    submission_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> ClaimResponse:
    """Soft-claim a submission for review. SELECT FOR UPDATE SKIP LOCKED. Platform Team only."""
    reviewer_id = UUID(current_user["user_id"])
    try:
        result = claim_submission(db, submission_id=submission_id, reviewer_id=reviewer_id)
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return ClaimResponse(**result)


@router.post("/{submission_id}/decision", response_model=DecisionResponse)
def decide_queue_item(
    submission_id: UUID,
    body: DecisionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> DecisionResponse:
    """Record approve / reject / request_changes for a submission. Platform Team only."""
    reviewer_id = UUID(current_user["user_id"])
    try:
        result = decide_submission(
            db,
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            decision=body.decision,
            notes=body.notes,
            score=body.score,
        )
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err)) from err
    return DecisionResponse(**result)
```

### Register in main.py

Add to `apps/api/skillhub/main.py` alongside existing router includes:

```python
from skillhub.routers.review_queue import router as review_queue_router
# ...
app.include_router(review_queue_router)
```

---

## 10. Frontend: useAdminQueue Hook

**File:** `apps/web/src/hooks/useAdminQueue.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

export interface ReviewQueueItem {
  submission_id: string;
  display_id: string;
  skill_name: string;
  version: string;
  submitter_id: string;
  submitter_name: string | null;
  submitted_at: string;
  gate1_passed: boolean;
  gate2_score: number | null;
  gate2_summary: string | null;
  content_preview: string;
  wait_time_hours: number;
  gate3_reviewer_id: string | null;
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface ClaimResponse {
  submission_id: string;
  display_id: string;
  claimed_by: string;
  claimed_at: string;
}

export interface DecisionRequest {
  decision: 'approve' | 'reject' | 'request_changes';
  notes: string;
  score: number | null;
}

export interface DecisionResponse {
  submission_id: string;
  display_id: string;
  new_status: string;
  decided_by: string;
  decided_at: string;
  gate_result_id: string | null;
}

export function useAdminQueue(page = 1, perPage = 50) {
  const [data, setData] = useState<ReviewQueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<ReviewQueueResponse>(
        '/api/v1/admin/review-queue',
        { page, per_page: perPage },
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load queue');
    } finally {
      setLoading(false);
    }
  }, [page, perPage]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const claimItem = useCallback(async (submissionId: string): Promise<ClaimResponse> => {
    return api.post<ClaimResponse>(`/api/v1/admin/review-queue/${submissionId}/claim`);
  }, []);

  const decideItem = useCallback(
    async (submissionId: string, req: DecisionRequest): Promise<DecisionResponse> => {
      return api.post<DecisionResponse>(
        `/api/v1/admin/review-queue/${submissionId}/decision`,
        req,
      );
    },
    [],
  );

  return { data, loading, error, refetch: fetchQueue, claimItem, decideItem };
}
```

---

## 11. Frontend: AdminConfirmDialog Component

**File:** `apps/web/src/components/admin/AdminConfirmDialog.tsx`

This component follows the `AuthModal` overlay pattern established in the codebase (see `apps/web/src/components/AuthModal.tsx`): `rgba(4,8,16,0.85)` backdrop with `blur(10px)`, `18px` border radius, `borderHi` border color.

```typescript
import { useEffect, useRef } from 'react';
import { useT } from '../../context/ThemeContext';

interface Props {
  title: string;
  message: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  destructive?: boolean;
}

/**
 * Modal confirmation dialog.
 * - Destructive dialogs focus Cancel by default.
 * - Focus is trapped: Tab/Shift+Tab cycle between Cancel and Confirm.
 * - Escape closes and restores focus to the trigger.
 * - For destructive actions a red gradient bar is rendered above the title.
 */
export function AdminConfirmDialog({
  title,
  message,
  confirmLabel,
  onConfirm,
  onCancel,
  destructive = false,
}: Props) {
  const C = useT();
  const cancelRef = useRef<HTMLButtonElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);

  // Focus Cancel by default on destructive; Confirm otherwise
  useEffect(() => {
    if (destructive) {
      cancelRef.current?.focus();
    } else {
      confirmRef.current?.focus();
    }
  }, [destructive]);

  // Trap focus within dialog
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
      return;
    }
    if (e.key !== 'Tab') return;
    const focusable = [cancelRef.current, confirmRef.current].filter(Boolean) as HTMLButtonElement[];
    if (focusable.length < 2) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
      onKeyDown={handleKeyDown}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(4,8,16,0.85)',
        backdropFilter: 'blur(10px)',
        zIndex: 1100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          background: C.surface,
          border: `1px solid ${C.borderHi}`,
          borderRadius: '18px',
          width: '100%',
          maxWidth: '420px',
          overflow: 'hidden',
          boxShadow: C.cardShadow,
        }}
      >
        {/* Destructive indicator bar */}
        {destructive && (
          <div
            style={{
              height: '4px',
              background: `linear-gradient(90deg, ${C.red}, ${C.red}44)`,
            }}
          />
        )}

        <div style={{ padding: '28px 28px 24px' }}>
          <h2
            id="confirm-dialog-title"
            style={{
              fontSize: '17px',
              fontWeight: 700,
              color: C.text,
              margin: '0 0 10px',
            }}
          >
            {title}
          </h2>
          <p
            id="confirm-dialog-message"
            style={{
              fontSize: '14px',
              color: C.muted,
              margin: '0 0 24px',
              lineHeight: 1.6,
            }}
          >
            {message}
          </p>

          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
            <button
              ref={cancelRef}
              onClick={onCancel}
              style={{
                padding: '8px 18px',
                borderRadius: '8px',
                border: `1px solid ${C.border}`,
                background: 'transparent',
                color: C.muted,
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              ref={confirmRef}
              onClick={onConfirm}
              style={{
                padding: '8px 18px',
                borderRadius: '8px',
                border: 'none',
                background: destructive ? C.red : C.accent,
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
      </div>
    </div>
  );
}
```

---

## 12. Frontend: AdminQueueView

**File:** `apps/web/src/views/admin/AdminQueueView.tsx`

Design constants referenced in the spec:
- `queueListWidth` = `380px`
- Overlay/modal background: `rgba(4,8,16,0.85)` + `blur(10px)` (matches AuthModal)
- SLA badge thresholds: `< 24h` = none, `24-48h` = amber, `> 48h` = red

```typescript
import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useT } from '../../context/ThemeContext';
import { useAuth } from '../../hooks/useAuth';
import { useAdminQueue } from '../../hooks/useAdminQueue';
import { AdminConfirmDialog } from '../../components/admin/AdminConfirmDialog';
import type { ReviewQueueItem } from '../../hooks/useAdminQueue';

const QUEUE_LIST_WIDTH = '380px';
const BATCH_LIMIT = 20;

// ---- Utility helpers ----

function formatWait(hours: number): string {
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 24) return `${Math.round(hours)}h`;
  return `${Math.round(hours / 24)}d`;
}

function SlaBadge({ hours }: { hours: number }) {
  const C = useT();
  if (hours < 24) return null;
  const breached = hours >= 48;
  return (
    <span
      aria-label={breached ? 'SLA breached' : 'SLA at risk'}
      style={{
        fontSize: '10px',
        fontWeight: 600,
        padding: '2px 7px',
        borderRadius: '99px',
        background: breached ? C.redDim : C.amberDim,
        color: breached ? C.red : C.amber,
        border: `1px solid ${breached ? C.red : C.amber}44`,
      }}
    >
      {breached ? 'SLA breached' : 'SLA at risk'}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const C = useT();
  const colors: Record<string, { bg: string; color: string }> = {
    gate2_passed: { bg: C.greenDim, color: C.green },
    gate2_flagged: { bg: C.amberDim, color: C.amber },
  };
  const style = colors[status] ?? { bg: C.accentDim, color: C.accent };
  return (
    <span
      style={{
        fontSize: '10px',
        fontWeight: 600,
        padding: '2px 7px',
        borderRadius: '99px',
        background: style.bg,
        color: style.color,
      }}
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
}

// ---- Live announce region ----

function Announcer({ message }: { message: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0,0,0,0)' }}
    >
      {message}
    </div>
  );
}

// ---- Keyboard legend overlay ----

function KeyboardLegend({ onClose }: { onClose: () => void }) {
  const C = useT();
  const shortcuts = [
    ['J / K', 'Navigate items'],
    ['A', 'Approve selected'],
    ['R', 'Reject (opens notes)'],
    ['X', 'Toggle batch selection'],
    ['Shift + A', 'Batch approve (max 20)'],
    ['?', 'Toggle this legend'],
    ['Esc', 'Close dialog / deselect'],
  ];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(4,8,16,0.85)',
        backdropFilter: 'blur(10px)',
        zIndex: 1200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: C.surface,
          border: `1px solid ${C.borderHi}`,
          borderRadius: '18px',
          padding: '28px',
          minWidth: '340px',
          boxShadow: C.cardShadow,
        }}
      >
        <h2 style={{ fontSize: '16px', fontWeight: 700, color: C.text, marginBottom: '18px' }}>
          Keyboard Shortcuts
        </h2>
        <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 16px' }}>
          {shortcuts.map(([key, desc]) => (
            <>
              <dt key={`key-${key}`}>
                <kbd
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '11px',
                    background: C.surfaceHi,
                    border: `1px solid ${C.borderHi}`,
                    borderRadius: '5px',
                    padding: '2px 7px',
                    color: C.accent,
                  }}
                >
                  {key}
                </kbd>
              </dt>
              <dd key={`desc-${key}`} style={{ fontSize: '13px', color: C.muted, lineHeight: '1.6' }}>
                {desc}
              </dd>
            </>
          ))}
        </dl>
        <button
          onClick={onClose}
          autoFocus
          style={{
            marginTop: '20px',
            padding: '7px 18px',
            background: C.accent,
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: 600,
          }}
        >
          Close
        </button>
      </div>
    </div>
  );
}

// ---- Reject notes panel ----

interface RejectPanelProps {
  onReject: (notes: string) => void;
  onCancel: () => void;
}

function RejectPanel({ onReject, onCancel }: RejectPanelProps) {
  const C = useT();
  const [notes, setNotes] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const tooShort = notes.trim().length > 0 && notes.trim().length < 10;
  const errorId = 'reject-notes-error';

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Reject submission"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(4,8,16,0.85)',
        backdropFilter: 'blur(10px)',
        zIndex: 1100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          background: C.surface,
          border: `1px solid ${C.borderHi}`,
          borderRadius: '18px',
          width: '100%',
          maxWidth: '460px',
          overflow: 'hidden',
          boxShadow: C.cardShadow,
        }}
      >
        <div style={{ height: '4px', background: `linear-gradient(90deg, ${C.red}, ${C.red}44)` }} />
        <div style={{ padding: '28px' }}>
          <h2 style={{ fontSize: '17px', fontWeight: 700, color: C.text, marginBottom: '12px' }}>
            Reject Submission
          </h2>
          <label
            htmlFor="reject-notes"
            style={{ fontSize: '13px', color: C.muted, display: 'block', marginBottom: '8px' }}
          >
            Reason for rejection <span aria-hidden="true">(min 10 chars)</span>
          </label>
          <textarea
            id="reject-notes"
            ref={textareaRef}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            aria-describedby={tooShort ? errorId : undefined}
            aria-invalid={tooShort}
            rows={4}
            style={{
              width: '100%',
              background: C.inputBg,
              border: `1px solid ${tooShort ? C.red : C.border}`,
              borderRadius: '8px',
              padding: '10px 12px',
              color: C.text,
              fontSize: '14px',
              resize: 'vertical',
              outline: 'none',
            }}
          />
          {tooShort && (
            <p id={errorId} role="alert" style={{ fontSize: '12px', color: C.red, marginTop: '6px' }}>
              Rejection reason must be at least 10 characters.
            </p>
          )}
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px' }}>
            <button
              onClick={onCancel}
              style={{
                padding: '8px 18px',
                borderRadius: '8px',
                border: `1px solid ${C.border}`,
                background: 'transparent',
                color: C.muted,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              onClick={() => notes.trim().length >= 10 && onReject(notes.trim())}
              disabled={notes.trim().length < 10}
              style={{
                padding: '8px 18px',
                borderRadius: '8px',
                border: 'none',
                background: notes.trim().length >= 10 ? C.red : C.dim,
                color: '#fff',
                fontSize: '13px',
                fontWeight: 600,
                cursor: notes.trim().length >= 10 ? 'pointer' : 'not-allowed',
              }}
            >
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---- Main view ----

export function AdminQueueView() {
  const C = useT();
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedId = searchParams.get('id');

  const { data, loading, error, refetch, claimItem, decideItem } = useAdminQueue();

  const [announcement, setAnnouncement] = useState('');
  const [showLegend, setShowLegend] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [showRejectPanel, setShowRejectPanel] = useState(false);
  const [batchSelected, setBatchSelected] = useState<Set<string>>(new Set());
  const [actionPending, setActionPending] = useState(false);

  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);
  const confirmTriggerRef = useRef<HTMLElement | null>(null);

  const items: ReviewQueueItem[] = data?.items ?? [];
  const selectedItem = items.find((it) => it.submission_id === selectedId) ?? null;
  const selectedIndex = items.findIndex((it) => it.submission_id === selectedId);
  const isSelfSubmission = selectedItem?.submitter_id === user?.user_id;

  const selectItem = useCallback(
    (id: string) => {
      setSearchParams({ id }, { replace: true });
    },
    [setSearchParams],
  );

  const focusItem = useCallback(
    (index: number) => {
      const item = items[index];
      if (!item) return;
      selectItem(item.submission_id);
      itemRefs.current[index]?.focus();
    },
    [items, selectItem],
  );

  const announce = useCallback((msg: string) => {
    setAnnouncement('');
    // Defer to ensure the DOM clears before re-announcing
    setTimeout(() => setAnnouncement(msg), 10);
  }, []);

  const handleApprove = useCallback(
    async (id: string) => {
      setActionPending(true);
      try {
        await claimItem(id);
        await decideItem(id, { decision: 'approve', notes: '', score: null });
        await refetch();
        const remaining = (data?.total ?? 1) - 1;
        announce(`Submission approved. ${remaining} items remaining.`);
        // Move focus to next item
        const nextIndex = Math.min(selectedIndex, items.length - 2);
        if (nextIndex >= 0) {
          focusItem(nextIndex);
        }
      } finally {
        setActionPending(false);
        setShowConfirm(false);
      }
    },
    [claimItem, decideItem, refetch, data?.total, announce, selectedIndex, items, focusItem],
  );

  const handleReject = useCallback(
    async (id: string, notes: string) => {
      setActionPending(true);
      try {
        await claimItem(id);
        await decideItem(id, { decision: 'reject', notes, score: null });
        await refetch();
        announce('Submission rejected.');
        const nextIndex = Math.min(selectedIndex, items.length - 2);
        if (nextIndex >= 0) {
          focusItem(nextIndex);
        }
      } finally {
        setActionPending(false);
        setShowRejectPanel(false);
      }
    },
    [claimItem, decideItem, refetch, announce, selectedIndex, items, focusItem],
  );

  const handleBatchApprove = useCallback(async () => {
    const ids = [...batchSelected].slice(0, BATCH_LIMIT);
    setActionPending(true);
    try {
      for (const id of ids) {
        await claimItem(id);
        await decideItem(id, { decision: 'approve', notes: '', score: null });
      }
      setBatchSelected(new Set());
      await refetch();
      announce(`${ids.length} submissions approved.`);
    } finally {
      setActionPending(false);
    }
  }, [batchSelected, claimItem, decideItem, refetch, announce]);

  // ---- Keyboard navigation ----
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // Do not fire shortcuts when typing in an input
      const tag = (document.activeElement as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      switch (e.key) {
        case 'j':
        case 'J':
          e.preventDefault();
          focusItem(Math.min(selectedIndex + 1, items.length - 1));
          break;
        case 'k':
        case 'K':
          e.preventDefault();
          focusItem(Math.max(selectedIndex - 1, 0));
          break;
        case 'a':
          if (e.shiftKey) {
            e.preventDefault();
            if (batchSelected.size > 0) handleBatchApprove();
          } else {
            e.preventDefault();
            if (selectedItem && !isSelfSubmission) {
              confirmTriggerRef.current = document.activeElement as HTMLElement;
              setShowConfirm(true);
            } else if (selectedItem && isSelfSubmission) {
              announce('You cannot approve your own submission.');
            }
          }
          break;
        case 'r':
        case 'R':
          e.preventDefault();
          if (selectedItem) setShowRejectPanel(true);
          break;
        case 'x':
        case 'X':
          e.preventDefault();
          if (selectedId) {
            setBatchSelected((prev) => {
              const next = new Set(prev);
              if (next.has(selectedId)) next.delete(selectedId);
              else next.add(selectedId);
              return next;
            });
          }
          break;
        case '?':
          e.preventDefault();
          setShowLegend((v) => !v);
          break;
        case 'Escape':
          setShowConfirm(false);
          setShowRejectPanel(false);
          setShowLegend(false);
          confirmTriggerRef.current?.focus();
          break;
        default:
          break;
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [
    selectedIndex,
    selectedId,
    selectedItem,
    isSelfSubmission,
    items,
    batchSelected,
    focusItem,
    handleBatchApprove,
    announce,
  ]);

  // ---- Render ----

  if (loading) {
    return (
      <div style={{ padding: '40px', color: C.muted, textAlign: 'center' }}>
        Loading review queue…
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', color: C.red, textAlign: 'center' }}>
        {error}
        <button
          onClick={refetch}
          style={{ marginLeft: '12px', color: C.accent, background: 'none', border: 'none', cursor: 'pointer' }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <>
      <Announcer message={announcement} />

      {showLegend && <KeyboardLegend onClose={() => setShowLegend(false)} />}

      {showConfirm && selectedItem && (
        <AdminConfirmDialog
          title="Approve Submission"
          message={`Approve "${selectedItem.skill_name}" submitted by ${selectedItem.submitter_name ?? 'unknown'}? This will publish the skill pending final review.`}
          confirmLabel="Approve"
          onConfirm={() => handleApprove(selectedItem.submission_id)}
          onCancel={() => {
            setShowConfirm(false);
            confirmTriggerRef.current?.focus();
          }}
          destructive={false}
        />
      )}

      {showRejectPanel && selectedItem && (
        <RejectPanel
          onReject={(notes) => handleReject(selectedItem.submission_id, notes)}
          onCancel={() => setShowRejectPanel(false)}
        />
      )}

      <div style={{ display: 'flex', height: 'calc(100vh - 60px)', overflow: 'hidden' }}>
        {/* ---- Queue list ---- */}
        <div
          role="grid"
          aria-label="Submissions awaiting review"
          aria-rowcount={items.length}
          style={{
            width: QUEUE_LIST_WIDTH,
            flexShrink: 0,
            borderRight: `1px solid ${C.border}`,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '16px 16px 12px',
              borderBottom: `1px solid ${C.border}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexShrink: 0,
            }}
          >
            <h1 style={{ fontSize: '15px', fontWeight: 700, color: C.text, margin: 0 }}>
              Review Queue
              {data && (
                <span
                  style={{
                    marginLeft: '8px',
                    fontSize: '11px',
                    fontWeight: 500,
                    color: C.muted,
                    background: C.surfaceHi,
                    padding: '1px 8px',
                    borderRadius: '99px',
                  }}
                >
                  {data.total}
                </span>
              )}
            </h1>
            <button
              onClick={() => setShowLegend(true)}
              aria-label="Show keyboard shortcuts"
              title="Keyboard shortcuts (?)"
              style={{
                background: 'none',
                border: `1px solid ${C.border}`,
                color: C.muted,
                borderRadius: '6px',
                padding: '3px 8px',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              ?
            </button>
          </div>

          {/* Batch bar */}
          {batchSelected.size > 0 && (
            <div
              style={{
                padding: '8px 16px',
                background: C.accentDim,
                borderBottom: `1px solid ${C.border}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexShrink: 0,
              }}
            >
              <span style={{ fontSize: '12px', color: C.accent }}>
                {batchSelected.size} selected
              </span>
              <button
                onClick={handleBatchApprove}
                disabled={actionPending}
                style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  padding: '4px 12px',
                  background: C.accent,
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: actionPending ? 'not-allowed' : 'pointer',
                }}
              >
                Approve {Math.min(batchSelected.size, BATCH_LIMIT)}
              </button>
            </div>
          )}

          {/* Empty state */}
          {items.length === 0 && (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '40px 20px',
                color: C.muted,
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>✓</div>
              <p style={{ fontSize: '14px', fontWeight: 600, color: C.text, marginBottom: '4px' }}>
                Queue is empty
              </p>
              <p style={{ fontSize: '13px' }}>All submissions have been reviewed.</p>
            </div>
          )}

          {/* Queue items */}
          {items.map((item, index) => {
            const isSelected = item.submission_id === selectedId;
            const isBatched = batchSelected.has(item.submission_id);
            return (
              <div
                key={item.submission_id}
                ref={(el) => { itemRefs.current[index] = el; }}
                role="row"
                aria-rowindex={index + 1}
                aria-selected={isSelected}
                tabIndex={isSelected ? 0 : -1}
                onClick={() => selectItem(item.submission_id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    selectItem(item.submission_id);
                  }
                }}
                style={{
                  padding: '14px 16px',
                  borderBottom: `1px solid ${C.border}`,
                  background: isSelected ? C.surfaceHi : isBatched ? C.accentDim : 'transparent',
                  cursor: 'pointer',
                  outline: 'none',
                  borderLeft: isSelected ? `3px solid ${C.accent}` : '3px solid transparent',
                  transition: 'background 0.12s',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: C.text }}>
                    {item.skill_name}
                  </span>
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: '10px',
                      color: C.dim,
                    }}
                  >
                    {item.display_id}
                  </span>
                </div>
                <div style={{ fontSize: '11px', color: C.muted, marginBottom: '8px' }}>
                  {item.submitter_name ?? 'Unknown'} · {formatWait(item.wait_time_hours)} ago
                </div>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <SlaBadge hours={item.wait_time_hours} />
                  {item.gate3_reviewer_id && (
                    <span
                      style={{
                        fontSize: '10px',
                        color: C.purple,
                        background: C.accentDim,
                        padding: '1px 7px',
                        borderRadius: '99px',
                        fontWeight: 600,
                      }}
                    >
                      claimed
                    </span>
                  )}
                  {item.gate2_score != null && (
                    <span style={{ fontSize: '10px', color: C.muted }}>
                      G2: {item.gate2_score}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* ---- Detail panel ---- */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '28px 32px',
          }}
        >
          {!selectedItem ? (
            <div
              style={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: C.muted,
                textAlign: 'center',
              }}
            >
              <p style={{ fontSize: '15px', fontWeight: 600, color: C.text, marginBottom: '6px' }}>
                Select a submission to review
              </p>
              <p style={{ fontSize: '13px' }}>
                Press <kbd style={{ fontFamily: 'monospace', color: C.accent }}>J</kbd> /{' '}
                <kbd style={{ fontFamily: 'monospace', color: C.accent }}>K</kbd> to navigate
              </p>
            </div>
          ) : (
            <>
              {/* Detail header */}
              <div style={{ marginBottom: '24px' }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '8px',
                  }}
                >
                  <div>
                    <h2 style={{ fontSize: '20px', fontWeight: 800, color: C.text, margin: '0 0 4px' }}>
                      {selectedItem.skill_name}
                    </h2>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span
                        style={{
                          fontFamily: "'JetBrains Mono', monospace",
                          fontSize: '11px',
                          color: C.dim,
                        }}
                      >
                        {selectedItem.display_id}
                      </span>
                      <span style={{ fontSize: '11px', color: C.muted }}>
                        v{selectedItem.version}
                      </span>
                      <SlaBadge hours={selectedItem.wait_time_hours} />
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                    <button
                      onClick={() => {
                        if (!isSelfSubmission) {
                          confirmTriggerRef.current = document.activeElement as HTMLElement;
                          setShowConfirm(true);
                        } else {
                          announce('You cannot approve your own submission.');
                        }
                      }}
                      aria-disabled={isSelfSubmission ? 'true' : undefined}
                      aria-describedby={isSelfSubmission ? 'self-approve-tooltip' : undefined}
                      disabled={actionPending}
                      style={{
                        padding: '8px 18px',
                        borderRadius: '8px',
                        border: 'none',
                        background: isSelfSubmission ? C.dim : C.green,
                        color: '#fff',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: isSelfSubmission ? 'not-allowed' : 'pointer',
                        opacity: actionPending ? 0.6 : 1,
                      }}
                    >
                      Approve
                    </button>
                    {isSelfSubmission && (
                      <span
                        id="self-approve-tooltip"
                        role="tooltip"
                        style={{ position: 'absolute', clip: 'rect(0,0,0,0)', width: 1, height: 1 }}
                      >
                        You cannot approve your own submission.
                      </span>
                    )}
                    <button
                      onClick={() => setShowRejectPanel(true)}
                      disabled={actionPending}
                      style={{
                        padding: '8px 18px',
                        borderRadius: '8px',
                        border: `1px solid ${C.border}`,
                        background: 'transparent',
                        color: C.red,
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        opacity: actionPending ? 0.6 : 1,
                      }}
                    >
                      Reject
                    </button>
                    <button
                      onClick={async () => {
                        setActionPending(true);
                        try {
                          await claimItem(selectedItem.submission_id);
                          await decideItem(selectedItem.submission_id, {
                            decision: 'request_changes',
                            notes: '',
                            score: null,
                          });
                          await refetch();
                          announce('Changes requested.');
                        } finally {
                          setActionPending(false);
                        }
                      }}
                      disabled={actionPending}
                      style={{
                        padding: '8px 18px',
                        borderRadius: '8px',
                        border: `1px solid ${C.border}`,
                        background: 'transparent',
                        color: C.amber,
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        opacity: actionPending ? 0.6 : 1,
                      }}
                    >
                      Request Changes
                    </button>
                  </div>
                </div>

                <div style={{ fontSize: '13px', color: C.muted }}>
                  Submitted by{' '}
                  <strong style={{ color: C.text }}>
                    {selectedItem.submitter_name ?? selectedItem.submitter_id}
                  </strong>{' '}
                  · {formatWait(selectedItem.wait_time_hours)} ago
                  {selectedItem.gate3_reviewer_id && (
                    <span style={{ marginLeft: '8px', color: C.purple }}>· claimed</span>
                  )}
                </div>
              </div>

              {/* Gate results */}
              <section style={{ marginBottom: '24px' }}>
                <h3 style={{ fontSize: '13px', fontWeight: 700, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>
                  Gate Results
                </h3>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <div
                    style={{
                      flex: 1,
                      padding: '14px 16px',
                      background: selectedItem.gate1_passed ? C.greenDim : C.redDim,
                      border: `1px solid ${selectedItem.gate1_passed ? C.green : C.red}44`,
                      borderRadius: '10px',
                    }}
                  >
                    <div style={{ fontSize: '11px', fontWeight: 700, color: C.muted, marginBottom: '4px' }}>
                      GATE 1 · Content
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: selectedItem.gate1_passed ? C.green : C.red }}>
                      {selectedItem.gate1_passed ? 'Passed' : 'Failed'}
                    </div>
                  </div>
                  <div
                    style={{
                      flex: 1,
                      padding: '14px 16px',
                      background: C.accentDim,
                      border: `1px solid ${C.accent}44`,
                      borderRadius: '10px',
                    }}
                  >
                    <div style={{ fontSize: '11px', fontWeight: 700, color: C.muted, marginBottom: '4px' }}>
                      GATE 2 · LLM Score
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: C.accent }}>
                      {selectedItem.gate2_score != null ? `${selectedItem.gate2_score}/100` : 'N/A'}
                    </div>
                    {selectedItem.gate2_summary && (
                      <p style={{ fontSize: '12px', color: C.muted, marginTop: '4px', lineHeight: 1.5 }}>
                        {selectedItem.gate2_summary}
                      </p>
                    )}
                  </div>
                </div>
              </section>

              {/* Content preview */}
              <section>
                <h3 style={{ fontSize: '13px', fontWeight: 700, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>
                  Content Preview
                </h3>
                <pre
                  style={{
                    background: C.codeBg,
                    border: `1px solid ${C.border}`,
                    borderRadius: '10px',
                    padding: '16px',
                    fontSize: '13px',
                    fontFamily: "'JetBrains Mono', monospace",
                    color: C.text,
                    overflowX: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    lineHeight: 1.6,
                  }}
                >
                  {selectedItem.content_preview}
                  {selectedItem.content_preview.length >= 500 && (
                    <span style={{ color: C.dim }}>{'\n'}… (truncated at 500 chars)</span>
                  )}
                </pre>
              </section>
            </>
          )}
        </div>
      </div>
    </>
  );
}
```

---

## 13. Frontend: App.tsx Route Registration

Add the import and route to `apps/web/src/App.tsx`:

```typescript
// Add import alongside existing view imports:
import { AdminQueueView } from './views/admin/AdminQueueView';

// Add route inside <Routes>:
<Route path="/admin/queue" element={<AdminQueueView />} />
```

The `AdminQueueView` does not require a layout wrapper beyond the existing `<Nav>` — it uses `height: calc(100vh - 60px)` for the split-pane layout where `60px` is the nav height.

---

## 14. Testing: Backend

**File:** `apps/api/tests/test_review_queue_service.py`

Write these tests FIRST (RED phase), then implement the service (GREEN).

```python
"""Tests for the HITL review queue service."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from skillhub_db.models.submission import GateResult, Submission, SubmissionGateResult, SubmissionStatus

from skillhub.services.review_queue import (
    claim_submission,
    decide_submission,
    get_review_queue,
)


def _make_submission(
    db: MagicMock,
    *,
    status: SubmissionStatus = SubmissionStatus.GATE2_PASSED,
    submitted_by: uuid.UUID | None = None,
    age_hours: float = 10.0,
) -> Submission:
    sub = Submission()
    sub.id = uuid.uuid4()
    sub.display_id = "SKL-TEST1"
    sub.name = "Test Skill"
    sub.short_desc = "A test skill"
    sub.category = "productivity"
    sub.content = "This is the skill content " * 30
    sub.declared_divisions = ["eng"]
    sub.division_justification = "needed for eng"
    sub.status = status
    sub.submitted_by = submitted_by or uuid.uuid4()
    sub.gate3_reviewer_id = None
    sub.gate3_reviewed_at = None
    sub.gate3_notes = None
    sub.created_at = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    return sub


class TestGetReviewQueue:
    def test_returns_only_gate2_passed_and_flagged(self, db_session):
        """Only submissions with status gate2_passed or gate2_flagged appear in queue."""
        gate2_passed = _make_submission(db_session, status=SubmissionStatus.GATE2_PASSED)
        gate2_flagged = _make_submission(db_session, status=SubmissionStatus.GATE2_FLAGGED)
        gate2_failed = _make_submission(db_session, status=SubmissionStatus.GATE2_FAILED)
        approved = _make_submission(db_session, status=SubmissionStatus.APPROVED)

        db_session.add_all([gate2_passed, gate2_flagged, gate2_failed, approved])
        db_session.commit()

        items, total = get_review_queue(db_session)
        ids = [i["submission_id"] for i in items]
        assert gate2_passed.id in ids
        assert gate2_flagged.id in ids
        assert gate2_failed.id not in ids
        assert approved.id not in ids
        assert total == 2

    def test_ordered_oldest_first(self, db_session):
        """Oldest submissions appear first in the queue."""
        newer = _make_submission(db_session, age_hours=5.0)
        older = _make_submission(db_session, age_hours=30.0)
        db_session.add_all([newer, older])
        db_session.commit()

        items, _ = get_review_queue(db_session)
        assert items[0]["submission_id"] == older.id

    def test_content_preview_truncated_at_500(self, db_session):
        sub = _make_submission(db_session)
        sub.content = "A" * 1000
        db_session.add(sub)
        db_session.commit()

        items, _ = get_review_queue(db_session)
        assert len(items[0]["content_preview"]) == 500

    def test_wait_time_calculated(self, db_session):
        sub = _make_submission(db_session, age_hours=25.0)
        db_session.add(sub)
        db_session.commit()

        items, _ = get_review_queue(db_session)
        assert 24.0 <= items[0]["wait_time_hours"] <= 26.0

    def test_gate1_passed_resolved_from_gate_results(self, db_session):
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.flush()
        gr = SubmissionGateResult(
            id=uuid.uuid4(),
            submission_id=sub.id,
            gate=1,
            result=GateResult.PASSED,
        )
        db_session.add(gr)
        db_session.commit()

        items, _ = get_review_queue(db_session)
        assert items[0]["gate1_passed"] is True

    def test_gate2_score_and_summary_resolved(self, db_session):
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.flush()
        gr = SubmissionGateResult(
            id=uuid.uuid4(),
            submission_id=sub.id,
            gate=2,
            result=GateResult.PASSED,
            score=88,
            findings={"summary": "Looks good"},
        )
        db_session.add(gr)
        db_session.commit()

        items, _ = get_review_queue(db_session)
        assert items[0]["gate2_score"] == 88
        assert items[0]["gate2_summary"] == "Looks good"

    def test_pagination(self, db_session):
        for _ in range(5):
            db_session.add(_make_submission(db_session))
        db_session.commit()

        items, total = get_review_queue(db_session, page=1, per_page=2)
        assert len(items) == 2
        assert total == 5


class TestClaimSubmission:
    def test_claim_sets_reviewer_id(self, db_session):
        reviewer_id = uuid.uuid4()
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        result = claim_submission(db_session, submission_id=sub.id, reviewer_id=reviewer_id)
        assert result["claimed_by"] == reviewer_id
        db_session.refresh(sub)
        assert sub.gate3_reviewer_id == reviewer_id

    def test_claim_does_not_change_status(self, db_session):
        reviewer_id = uuid.uuid4()
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        claim_submission(db_session, submission_id=sub.id, reviewer_id=reviewer_id)
        db_session.refresh(sub)
        assert sub.status == SubmissionStatus.GATE2_PASSED

    def test_self_claim_raises_permission_error(self, db_session):
        submitter_id = uuid.uuid4()
        sub = _make_submission(db_session, submitted_by=submitter_id)
        db_session.add(sub)
        db_session.commit()

        with pytest.raises(PermissionError, match="Cannot approve your own submission"):
            claim_submission(db_session, submission_id=sub.id, reviewer_id=submitter_id)

    def test_claim_non_eligible_status_raises(self, db_session):
        sub = _make_submission(db_session, status=SubmissionStatus.APPROVED)
        db_session.add(sub)
        db_session.commit()

        with pytest.raises(ValueError, match="not eligible"):
            claim_submission(db_session, submission_id=sub.id, reviewer_id=uuid.uuid4())

    def test_claim_nonexistent_submission_raises(self, db_session):
        with pytest.raises(ValueError, match="not found"):
            claim_submission(db_session, submission_id=uuid.uuid4(), reviewer_id=uuid.uuid4())

    def test_claim_writes_audit_log(self, db_session):
        from skillhub_db.models.audit import AuditLog

        reviewer_id = uuid.uuid4()
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        claim_submission(db_session, submission_id=sub.id, reviewer_id=reviewer_id)

        log = db_session.query(AuditLog).filter(
            AuditLog.event_type == "submission.gate3.claimed"
        ).first()
        assert log is not None
        assert log.actor_id == reviewer_id


class TestDecideSubmission:
    def test_approve_transitions_to_approved(self, db_session):
        reviewer_id = uuid.uuid4()
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        result = decide_submission(
            db_session,
            submission_id=sub.id,
            reviewer_id=reviewer_id,
            decision="approve",
        )
        assert result["new_status"] == "approved"
        db_session.refresh(sub)
        assert sub.status == SubmissionStatus.APPROVED

    def test_approve_creates_gate_result_pass(self, db_session):
        reviewer_id = uuid.uuid4()
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        decide_submission(
            db_session,
            submission_id=sub.id,
            reviewer_id=reviewer_id,
            decision="approve",
        )

        gr = (
            db_session.query(SubmissionGateResult)
            .filter(
                SubmissionGateResult.submission_id == sub.id,
                SubmissionGateResult.gate == 3,
            )
            .first()
        )
        assert gr is not None
        assert gr.result == GateResult.PASSED

    def test_reject_transitions_to_rejected(self, db_session):
        reviewer_id = uuid.uuid4()
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        result = decide_submission(
            db_session,
            submission_id=sub.id,
            reviewer_id=reviewer_id,
            decision="reject",
            notes="This skill has security issues and violates policy.",
        )
        assert result["new_status"] == "rejected"

    def test_reject_creates_gate_result_fail(self, db_session):
        reviewer_id = uuid.uuid4()
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        decide_submission(
            db_session,
            submission_id=sub.id,
            reviewer_id=reviewer_id,
            decision="reject",
            notes="This skill has security issues and violates policy.",
        )

        gr = (
            db_session.query(SubmissionGateResult)
            .filter(SubmissionGateResult.submission_id == sub.id, SubmissionGateResult.gate == 3)
            .first()
        )
        assert gr is not None
        assert gr.result == GateResult.FAILED
        assert gr.findings["reason"] == "rejected"

    def test_reject_short_notes_raises(self, db_session):
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        with pytest.raises(ValueError, match="at least 10 characters"):
            decide_submission(
                db_session,
                submission_id=sub.id,
                reviewer_id=uuid.uuid4(),
                decision="reject",
                notes="short",
            )

    def test_request_changes_transitions_correctly(self, db_session):
        reviewer_id = uuid.uuid4()
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        result = decide_submission(
            db_session,
            submission_id=sub.id,
            reviewer_id=reviewer_id,
            decision="request_changes",
        )
        assert result["new_status"] == "gate3_changes_requested"

    def test_request_changes_no_gate_result_row(self, db_session):
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        result = decide_submission(
            db_session,
            submission_id=sub.id,
            reviewer_id=uuid.uuid4(),
            decision="request_changes",
        )
        assert result["gate_result_id"] is None

    def test_self_approve_raises_permission_error(self, db_session):
        submitter_id = uuid.uuid4()
        sub = _make_submission(db_session, submitted_by=submitter_id)
        db_session.add(sub)
        db_session.commit()

        with pytest.raises(PermissionError, match="Cannot approve your own submission"):
            decide_submission(
                db_session,
                submission_id=sub.id,
                reviewer_id=submitter_id,
                decision="approve",
            )

    def test_approve_writes_audit_log(self, db_session):
        from skillhub_db.models.audit import AuditLog

        reviewer_id = uuid.uuid4()
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        decide_submission(
            db_session,
            submission_id=sub.id,
            reviewer_id=reviewer_id,
            decision="approve",
        )

        log = db_session.query(AuditLog).filter(
            AuditLog.event_type == "submission.approved"
        ).first()
        assert log is not None
        assert log.actor_id == reviewer_id

    def test_reject_writes_audit_log(self, db_session):
        from skillhub_db.models.audit import AuditLog

        reviewer_id = uuid.uuid4()
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        decide_submission(
            db_session,
            submission_id=sub.id,
            reviewer_id=reviewer_id,
            decision="reject",
            notes="Violates security policy for external calls.",
        )

        log = db_session.query(AuditLog).filter(
            AuditLog.event_type == "submission.rejected"
        ).first()
        assert log is not None

    def test_unknown_decision_raises(self, db_session):
        sub = _make_submission(db_session)
        db_session.add(sub)
        db_session.commit()

        with pytest.raises(ValueError, match="Unknown decision"):
            decide_submission(
                db_session,
                submission_id=sub.id,
                reviewer_id=uuid.uuid4(),
                decision="banana",
            )
```

**File:** `apps/api/tests/test_review_queue_router.py`

```python
"""Integration tests for the HITL review queue router."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


REVIEWER_TOKEN_PAYLOAD = {
    "user_id": str(uuid.uuid4()),
    "username": "reviewer",
    "is_platform_team": True,
    "is_security_team": False,
}

SUBMITTER_ID = uuid.uuid4()


class TestListReviewQueue:
    def test_returns_200_for_platform_team(self, client: TestClient, platform_team_headers):
        with patch("skillhub.routers.review_queue.get_review_queue") as mock:
            mock.return_value = ([], 0)
            resp = client.get("/api/v1/admin/review-queue", headers=platform_team_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] == 0

    def test_returns_403_for_non_admin(self, client: TestClient, user_headers):
        resp = client.get("/api/v1/admin/review-queue", headers=user_headers)
        assert resp.status_code == 403

    def test_pagination_params_forwarded(self, client: TestClient, platform_team_headers):
        with patch("skillhub.routers.review_queue.get_review_queue") as mock:
            mock.return_value = ([], 0)
            resp = client.get(
                "/api/v1/admin/review-queue?page=2&per_page=5",
                headers=platform_team_headers,
            )
        assert resp.status_code == 200
        mock.assert_called_once()
        _, kwargs = mock.call_args
        assert kwargs["page"] == 2
        assert kwargs["per_page"] == 5


class TestClaimQueueItem:
    def test_claim_returns_200(self, client: TestClient, platform_team_headers):
        sub_id = uuid.uuid4()
        reviewer_id = uuid.UUID(REVIEWER_TOKEN_PAYLOAD["user_id"])
        with patch("skillhub.routers.review_queue.claim_submission") as mock:
            mock.return_value = {
                "submission_id": sub_id,
                "display_id": "SKL-001",
                "claimed_by": reviewer_id,
                "claimed_at": "2026-03-01T12:00:00Z",
            }
            resp = client.post(
                f"/api/v1/admin/review-queue/{sub_id}/claim",
                headers=platform_team_headers,
            )
        assert resp.status_code == 200

    def test_claim_self_submission_returns_403(self, client: TestClient, platform_team_headers):
        sub_id = uuid.uuid4()
        with patch("skillhub.routers.review_queue.claim_submission") as mock:
            mock.side_effect = PermissionError("Cannot approve your own submission")
            resp = client.post(
                f"/api/v1/admin/review-queue/{sub_id}/claim",
                headers=platform_team_headers,
            )
        assert resp.status_code == 403

    def test_claim_not_found_returns_404(self, client: TestClient, platform_team_headers):
        sub_id = uuid.uuid4()
        with patch("skillhub.routers.review_queue.claim_submission") as mock:
            mock.side_effect = ValueError("Submission not found")
            resp = client.post(
                f"/api/v1/admin/review-queue/{sub_id}/claim",
                headers=platform_team_headers,
            )
        assert resp.status_code == 404


class TestDecideQueueItem:
    def test_approve_returns_200(self, client: TestClient, platform_team_headers):
        sub_id = uuid.uuid4()
        reviewer_id = uuid.UUID(REVIEWER_TOKEN_PAYLOAD["user_id"])
        with patch("skillhub.routers.review_queue.decide_submission") as mock:
            mock.return_value = {
                "submission_id": sub_id,
                "display_id": "SKL-001",
                "new_status": "approved",
                "decided_by": reviewer_id,
                "decided_at": "2026-03-01T12:00:00Z",
                "gate_result_id": uuid.uuid4(),
            }
            resp = client.post(
                f"/api/v1/admin/review-queue/{sub_id}/decision",
                json={"decision": "approve", "notes": "", "score": None},
                headers=platform_team_headers,
            )
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "approved"

    def test_reject_without_notes_returns_422(self, client: TestClient, platform_team_headers):
        sub_id = uuid.uuid4()
        with patch("skillhub.routers.review_queue.decide_submission") as mock:
            mock.side_effect = ValueError("Rejection notes must be at least 10 characters")
            resp = client.post(
                f"/api/v1/admin/review-queue/{sub_id}/decision",
                json={"decision": "reject", "notes": "short", "score": None},
                headers=platform_team_headers,
            )
        assert resp.status_code == 422

    def test_self_approve_returns_403(self, client: TestClient, platform_team_headers):
        sub_id = uuid.uuid4()
        with patch("skillhub.routers.review_queue.decide_submission") as mock:
            mock.side_effect = PermissionError("Cannot approve your own submission")
            resp = client.post(
                f"/api/v1/admin/review-queue/{sub_id}/decision",
                json={"decision": "approve", "notes": "", "score": None},
                headers=platform_team_headers,
            )
        assert resp.status_code == 403

    def test_invalid_decision_rejected_by_pydantic(self, client: TestClient, platform_team_headers):
        sub_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "banana", "notes": "", "score": None},
            headers=platform_team_headers,
        )
        assert resp.status_code == 422
```

---

## 15. Testing: Frontend

**File:** `apps/web/src/__tests__/AdminQueueView.test.tsx`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import { AdminQueueView } from '../views/admin/AdminQueueView';
import * as useAdminQueueModule from '../hooks/useAdminQueue';

const REVIEWER_USER_ID = 'reviewer-uuid-001';
const SUBMITTER_USER_ID = 'submitter-uuid-002';

function renderQueue(searchParams = '') {
  return render(
    <MemoryRouter initialEntries={[`/admin/queue${searchParams}`]}>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            <Route path="/admin/queue" element={<AdminQueueView />} />
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>,
  );
}

const mockItem = (overrides = {}): useAdminQueueModule.ReviewQueueItem => ({
  submission_id: 'sub-uuid-001',
  display_id: 'SKL-001',
  skill_name: 'My Test Skill',
  version: '1.0.0',
  submitter_id: SUBMITTER_USER_ID,
  submitter_name: 'Alice Smith',
  submitted_at: new Date(Date.now() - 3600 * 1000 * 30).toISOString(),
  gate1_passed: true,
  gate2_score: 82,
  gate2_summary: 'Solid implementation',
  content_preview: 'This is the skill content preview',
  wait_time_hours: 30,
  gate3_reviewer_id: null,
  ...overrides,
});

const defaultHookReturn: ReturnType<typeof useAdminQueueModule.useAdminQueue> = {
  data: {
    items: [mockItem()],
    total: 1,
    page: 1,
    per_page: 50,
    has_more: false,
  },
  loading: false,
  error: null,
  refetch: vi.fn(),
  claimItem: vi.fn().mockResolvedValue({}),
  decideItem: vi.fn().mockResolvedValue({ new_status: 'approved' }),
};

describe('AdminQueueView', () => {
  beforeEach(() => {
    vi.spyOn(useAdminQueueModule, 'useAdminQueue').mockReturnValue({
      ...defaultHookReturn,
      refetch: vi.fn(),
      claimItem: vi.fn().mockResolvedValue({}),
      decideItem: vi.fn().mockResolvedValue({ new_status: 'approved' }),
    });
  });

  describe('Queue list', () => {
    it('renders queue items', () => {
      renderQueue();
      expect(screen.getByText('My Test Skill')).toBeInTheDocument();
      expect(screen.getByText('SKL-001')).toBeInTheDocument();
    });

    it('renders empty state when queue is empty', () => {
      vi.spyOn(useAdminQueueModule, 'useAdminQueue').mockReturnValue({
        ...defaultHookReturn,
        data: { items: [], total: 0, page: 1, per_page: 50, has_more: false },
      });
      renderQueue();
      expect(screen.getByText('Queue is empty')).toBeInTheDocument();
    });

    it('shows SLA badge for items over 24h', () => {
      renderQueue();
      expect(screen.getByLabelText('SLA at risk')).toBeInTheDocument();
    });

    it('shows SLA breached badge for items over 48h', () => {
      vi.spyOn(useAdminQueueModule, 'useAdminQueue').mockReturnValue({
        ...defaultHookReturn,
        data: {
          items: [mockItem({ wait_time_hours: 50 })],
          total: 1,
          page: 1,
          per_page: 50,
          has_more: false,
        },
      });
      renderQueue();
      expect(screen.getByLabelText('SLA breached')).toBeInTheDocument();
    });

    it('renders grid role for accessibility', () => {
      renderQueue();
      expect(screen.getByRole('grid')).toBeInTheDocument();
    });
  });

  describe('Detail panel', () => {
    it('shows prompt when no item selected', () => {
      renderQueue();
      expect(screen.getByText('Select a submission to review')).toBeInTheDocument();
    });

    it('shows detail when item selected via URL', () => {
      renderQueue('?id=sub-uuid-001');
      expect(screen.getByText('Approve')).toBeInTheDocument();
      expect(screen.getByText('Reject')).toBeInTheDocument();
    });

    it('shows gate 1 and gate 2 results', () => {
      renderQueue('?id=sub-uuid-001');
      expect(screen.getByText(/GATE 1/)).toBeInTheDocument();
      expect(screen.getByText(/GATE 2/)).toBeInTheDocument();
      expect(screen.getByText('82/100')).toBeInTheDocument();
    });
  });

  describe('Self-approval protection', () => {
    it('disables approve button for own submissions via aria-disabled', () => {
      vi.spyOn(useAdminQueueModule, 'useAdminQueue').mockReturnValue({
        ...defaultHookReturn,
        data: {
          items: [mockItem({ submitter_id: REVIEWER_USER_ID })],
          total: 1,
          page: 1,
          per_page: 50,
          has_more: false,
        },
      });
      // Mock auth to return this user
      renderQueue('?id=sub-uuid-001');
      const approveBtn = screen.getByText('Approve');
      expect(approveBtn).toHaveAttribute('aria-disabled', 'true');
    });
  });

  describe('AdminConfirmDialog', () => {
    it('opens confirm dialog on approve click', () => {
      renderQueue('?id=sub-uuid-001');
      fireEvent.click(screen.getByText('Approve'));
      expect(screen.getByRole('dialog', { name: /Approve Submission/i })).toBeInTheDocument();
    });

    it('closes dialog on Cancel click', () => {
      renderQueue('?id=sub-uuid-001');
      fireEvent.click(screen.getByText('Approve'));
      fireEvent.click(screen.getByText('Cancel'));
      expect(screen.queryByRole('dialog', { name: /Approve Submission/i })).not.toBeInTheDocument();
    });

    it('calls claimItem and decideItem on confirm', async () => {
      const claimItem = vi.fn().mockResolvedValue({});
      const decideItem = vi.fn().mockResolvedValue({ new_status: 'approved' });
      vi.spyOn(useAdminQueueModule, 'useAdminQueue').mockReturnValue({
        ...defaultHookReturn,
        claimItem,
        decideItem,
      });

      renderQueue('?id=sub-uuid-001');
      fireEvent.click(screen.getByText('Approve'));
      fireEvent.click(screen.getByText('Approve', { selector: 'button' }));

      await waitFor(() => {
        expect(claimItem).toHaveBeenCalledWith('sub-uuid-001');
        expect(decideItem).toHaveBeenCalledWith('sub-uuid-001', {
          decision: 'approve',
          notes: '',
          score: null,
        });
      });
    });
  });

  describe('Reject flow', () => {
    it('opens reject panel on Reject click', () => {
      renderQueue('?id=sub-uuid-001');
      fireEvent.click(screen.getByText('Reject'));
      expect(screen.getByRole('dialog', { name: /Reject submission/i })).toBeInTheDocument();
    });

    it('reject button disabled when notes too short', () => {
      renderQueue('?id=sub-uuid-001');
      fireEvent.click(screen.getByText('Reject'));
      const textarea = screen.getByRole('textbox');
      fireEvent.change(textarea, { target: { value: 'short' } });
      const rejectBtn = screen.getByText('Reject', { selector: 'button[disabled]' });
      expect(rejectBtn).toBeDisabled();
    });

    it('shows error message when notes too short', () => {
      renderQueue('?id=sub-uuid-001');
      fireEvent.click(screen.getByText('Reject'));
      const textarea = screen.getByRole('textbox');
      fireEvent.change(textarea, { target: { value: 'short' } });
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('Keyboard legend', () => {
    it('opens keyboard legend on ? click', () => {
      renderQueue();
      fireEvent.click(screen.getByLabelText('Show keyboard shortcuts'));
      expect(screen.getByRole('dialog', { name: /Keyboard shortcuts/i })).toBeInTheDocument();
    });
  });

  describe('Loading and error states', () => {
    it('shows loading text while fetching', () => {
      vi.spyOn(useAdminQueueModule, 'useAdminQueue').mockReturnValue({
        ...defaultHookReturn,
        loading: true,
        data: null,
      });
      renderQueue();
      expect(screen.getByText(/Loading review queue/)).toBeInTheDocument();
    });

    it('shows error and retry button on fetch failure', () => {
      vi.spyOn(useAdminQueueModule, 'useAdminQueue').mockReturnValue({
        ...defaultHookReturn,
        loading: false,
        error: 'Network error',
        data: null,
      });
      renderQueue();
      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  describe('Announcer', () => {
    it('renders a live region for announcements', () => {
      renderQueue();
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });
});
```

---

## 16. Verification Checklist

Run after completing all implementation tasks.

```bash
# 1. Apply migration
cd libs/db && alembic upgrade head

# 2. Backend tests
cd apps/api && python -m pytest tests/test_review_queue_service.py tests/test_review_queue_router.py -v

# 3. Full backend test suite (must maintain ≥80% coverage)
cd apps/api && python -m pytest --cov=skillhub --cov-fail-under=80

# 4. Type check backend
cd apps/api && mypy skillhub/ --strict

# 5. Frontend tests
cd apps/web && npx vitest run src/__tests__/AdminQueueView.test.tsx

# 6. Full frontend test suite (must maintain ≥80% coverage)
cd apps/web && npx vitest run --coverage

# 7. TypeScript type check
cd apps/web && npx tsc --noEmit

# 8. Lint
cd apps/api && ruff check skillhub/
cd apps/web && npx eslint src/
```

Expected outcomes:
- All new service tests pass
- All new router tests pass
- All new frontend tests pass
- Coverage gates hold at ≥80%
- No type errors
- No lint errors

---

## 17. SLA Badge Reference

| Wait time | Badge | Color tokens |
|---|---|---|
| < 24 hours | None | — |
| 24–47h 59m | `SLA at risk` | `C.amber` / `C.amberDim` |
| ≥ 48 hours | `SLA breached` | `C.red` / `C.redDim` |

The `SlaBadge` component in `AdminQueueView.tsx` implements this directly. Thresholds are applied to `wait_time_hours` from the `ReviewQueueItem` object.

---

## 18. Accessibility Contract

| Requirement | Implementation |
|---|---|
| Queue container is Application Mode | `role="grid"` on the list container |
| Items are navigable rows | `role="row"`, `aria-rowindex`, `aria-selected` |
| Approve announces outcome | `role="status"` `aria-live="polite"` region with `"Submission approved. N items remaining."` |
| Reject announces outcome | Same live region: `"Submission rejected."` |
| Claim announces outcome | Same live region: `"Submission claimed."` |
| Self-approval button stays focusable | `aria-disabled="true"` (not HTML `disabled`) |
| Self-approval click announces constraint | Live region announces `"You cannot approve your own submission."` |
| Self-approval tooltip linked | `aria-describedby="self-approve-tooltip"` |
| Reject notes validated | `aria-invalid`, `aria-describedby` pointing to error paragraph |
| Error message is live | `role="alert"` on reject error paragraph |
| Confirm dialog is modal | `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus trap |
| Destructive confirm focuses Cancel | `cancelRef.current?.focus()` in `useEffect` |
| Keyboard legend is navigable | `role="dialog"`, `aria-label`, `autoFocus` on Close button |
| Escape closes all modals | Global `keydown` handler, all dialog `onKeyDown` handlers |
