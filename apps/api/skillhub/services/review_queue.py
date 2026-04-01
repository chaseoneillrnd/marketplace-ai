"""Review queue service — HITL approval workflow."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from skillhub_db.models.audit import AuditLog
from skillhub_db.models.submission import Submission, SubmissionGateResult, SubmissionStatus
from skillhub_db.models.user import User

logger = logging.getLogger(__name__)

REVIEWABLE_STATUSES = {SubmissionStatus.GATE2_PASSED, SubmissionStatus.GATE2_FLAGGED}


def get_review_queue(
    db: Session, *, page: int = 1, per_page: int = 20
) -> tuple[list[dict[str, Any]], int]:
    """Get submissions awaiting human review, ordered by oldest first."""
    query = db.query(Submission).filter(Submission.status.in_(REVIEWABLE_STATUSES))
    total = query.count()
    submissions = (
        query.order_by(Submission.created_at.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Batch resolve submitter names
    submitter_ids = {s.submitted_by for s in submissions}
    name_map: dict[Any, str] = {}
    if submitter_ids:
        users = db.query(User.id, User.name).filter(User.id.in_(submitter_ids)).all()
        name_map = {u.id: u.name for u in users}

    now = datetime.now(timezone.utc)
    items: list[dict[str, Any]] = []
    for s in submissions:
        # Get gate results
        gate_results = (
            db.query(SubmissionGateResult)
            .filter(SubmissionGateResult.submission_id == s.id)
            .all()
        )
        gate1 = next((g for g in gate_results if g.gate == 1), None)
        gate2 = next((g for g in gate_results if g.gate == 2), None)

        if s.created_at:
            ca = s.created_at if s.created_at.tzinfo else s.created_at.replace(tzinfo=timezone.utc)
            wait_hours = (now - ca).total_seconds() / 3600
        else:
            wait_hours = 0.0

        items.append(
            {
                "submission_id": str(s.id),
                "display_id": s.display_id,
                "skill_name": s.name,
                "short_desc": s.short_desc or "",
                "category": s.category or "",
                "submitter_name": name_map.get(s.submitted_by),
                "submitted_at": s.created_at,
                "gate1_passed": gate1.result == "passed" if gate1 else False,
                "gate2_score": (
                    float(gate2.findings.get("score", 0))
                    if gate2 and gate2.findings
                    else None
                ),
                "gate2_summary": (
                    gate2.findings.get("summary") if gate2 and gate2.findings else None
                ),
                "content_preview": (s.content or "")[:500],
                "wait_time_hours": round(wait_hours, 1),
                "divisions": s.declared_divisions or [],
            }
        )
    return items, total


def claim_submission(
    db: Session, *, submission_id: uuid.UUID, reviewer_id: uuid.UUID
) -> dict[str, Any]:
    """Claim a submission for review. Sets gate3_reviewer_id."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise ValueError("Submission not found")
    if submission.status not in REVIEWABLE_STATUSES:
        raise ValueError(f"Submission not reviewable (status: {submission.status})")

    submission.gate3_reviewer_id = reviewer_id

    claimed_at = datetime.now(timezone.utc)
    audit = AuditLog(
        id=uuid.uuid4(),
        event_type="submission.claimed",
        actor_id=reviewer_id,
        target_type="submission",
        target_id=str(submission.id),
        metadata_={"submission_id": str(submission.id)},
    )
    db.add(audit)
    db.commit()

    return {
        "submission_id": str(submission.id),
        "reviewer_id": str(reviewer_id),
        "claimed_at": claimed_at,
    }


def decide_submission(
    db: Session,
    *,
    submission_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    decision: str,
    notes: str = "",
    score: int | None = None,
) -> dict[str, Any]:
    """Approve, reject, or request changes on a submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise ValueError("Submission not found")
    if submission.status not in REVIEWABLE_STATUSES:
        raise ValueError(f"Submission not reviewable (status: {submission.status})")

    # Self-approval prevention
    if submission.submitted_by == reviewer_id:
        raise PermissionError("Cannot review your own submission")

    now = datetime.now(timezone.utc)

    if decision == "approve":
        submission.status = "approved"
        gate_result = "passed"
    elif decision == "reject":
        submission.status = "rejected"
        gate_result = "failed"
    elif decision == "request_changes":
        submission.status = "gate3_changes_requested"
        gate_result = "failed"
    else:
        raise ValueError(f"Invalid decision: {decision}")

    submission.gate3_reviewer_id = reviewer_id
    submission.gate3_reviewed_at = now
    submission.gate3_notes = notes

    # Create gate result
    gr = SubmissionGateResult(
        id=uuid.uuid4(),
        submission_id=submission.id,
        gate=3,
        result=gate_result,
        findings={"decision": decision, "notes": notes, "score": score},
    )
    db.add(gr)

    # Audit log — use explicit mapping to avoid f-string suffix bugs
    _event_map = {
        "approve": "submission.approved",
        "reject": "submission.rejected",
        "request_changes": "submission.changes_requested",
    }
    event_type = _event_map[decision]
    audit = AuditLog(
        id=uuid.uuid4(),
        event_type=event_type,
        actor_id=reviewer_id,
        target_type="submission",
        target_id=str(submission.id),
        metadata_={"decision": decision, "notes": notes},
    )
    db.add(audit)
    db.commit()

    return {
        "submission_id": str(submission.id),
        "decision": decision,
        "reviewer_id": str(reviewer_id),
        "reviewed_at": now,
    }
