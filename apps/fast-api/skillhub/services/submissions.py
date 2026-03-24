"""Submission pipeline service — create, gate validation, review."""

from __future__ import annotations

import logging
import random
import re
import string
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from opentelemetry import trace
from skillhub_db.models.audit import AuditLog
from skillhub_db.models.skill import (
    Skill,
    SkillDivision,
    SkillStatus,
    SkillVersion,
    TriggerPhrase,
)
from skillhub_db.models.submission import (
    AccessRequestStatus,
    DivisionAccessRequest,
    GateResult,
    Submission,
    SubmissionGateResult,
    SubmissionStatus,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("skillhub.services.submissions")


def _write_audit(
    db: Session,
    *,
    event_type: str,
    actor_id: UUID,
    target_type: str,
    target_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append a row to the audit log."""
    entry = AuditLog(
        id=uuid.uuid4(),
        event_type=event_type,
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
        metadata_=metadata,
    )
    db.add(entry)


def _generate_display_id() -> str:
    """Generate SKL-{6 random uppercase alphanum}."""
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=6))  # noqa: S311
    return f"SKL-{suffix}"


def _slugify(name: str) -> str:
    """Convert name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _parse_frontmatter(content: str) -> dict[str, Any] | None:
    """Parse YAML-like frontmatter from SKILL.md content.

    Expects content starting with --- and ending with ---.
    Returns parsed key-value pairs or None if no frontmatter found.
    """
    lines = content.strip().split("\n")
    if not lines or lines[0].strip() != "---":
        return None

    frontmatter: dict[str, Any] = {}
    i = 1
    while i < len(lines):
        line = lines[i].strip()
        if line == "---":
            return frontmatter
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            # Handle list values (simple inline YAML)
            if value.startswith("[") and value.endswith("]"):
                items = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
                frontmatter[key] = items
            elif value == "":
                # Could be a multi-line list
                items = []
                i += 1
                while i < len(lines) and lines[i].strip().startswith("- "):
                    items.append(lines[i].strip().removeprefix("- ").strip())
                    i += 1
                frontmatter[key] = items
                continue
            else:
                frontmatter[key] = value.strip("\"'")
        i += 1
    return None  # No closing ---


# Required frontmatter fields for Gate 1
REQUIRED_FRONTMATTER_FIELDS = {"name", "slug", "version", "category", "trigger_phrases"}


def run_gate1(
    db: Session,
    content: str,
    short_desc: str,
) -> tuple[GateResult, list[dict[str, str]]]:
    """Run Gate 1 schema validation on submission content.

    Returns (result, findings).
    """
    with tracer.start_as_current_span("service.submissions.run_gate1") as span:
        findings: list[dict[str, str]] = []

        # Parse frontmatter
        frontmatter = _parse_frontmatter(content)
        if frontmatter is None:
            findings.append({
                "severity": "high",
                "category": "schema",
                "description": "Missing or invalid frontmatter block",
            })
            span.set_attribute("submissions.gate1_result", "failed")
            return GateResult.FAILED, findings

        # Check required fields
        for field in REQUIRED_FRONTMATTER_FIELDS:
            if field not in frontmatter or not frontmatter[field]:
                findings.append({
                    "severity": "high",
                    "category": "schema",
                    "description": f"Required frontmatter field missing: {field}",
                })

        # Check slug uniqueness
        slug_value = frontmatter.get("slug")
        if slug_value:
            existing = db.query(Skill).filter(Skill.slug == slug_value).first()
            if existing:
                findings.append({
                    "severity": "high",
                    "category": "uniqueness",
                    "description": f"Slug '{slug_value}' is already in use",
                })

        # Check min 3 trigger phrases
        trigger_phrases = frontmatter.get("trigger_phrases", [])
        if not isinstance(trigger_phrases, list) or len(trigger_phrases) < 3:
            findings.append({
                "severity": "high",
                "category": "schema",
                "description": "At least 3 trigger phrases required",
            })

        # Short description ≤80 chars
        if len(short_desc) > 80:
            findings.append({
                "severity": "medium",
                "category": "schema",
                "description": f"Short description exceeds 80 characters ({len(short_desc)} chars)",
            })

        # Jaccard similarity check on trigger phrases
        if isinstance(trigger_phrases, list) and len(trigger_phrases) >= 3:
            submitted_words = {w.lower() for phrase in trigger_phrases for w in phrase.split()}
            existing_trigger_phrases = db.query(TriggerPhrase).all()
            # Group phrases by skill_id
            skill_phrases: dict[Any, set[str]] = {}
            for tp in existing_trigger_phrases:
                skill_phrases.setdefault(tp.skill_id, set())
                for w in tp.phrase.lower().split():
                    skill_phrases[tp.skill_id].add(w)
            for skill_id, existing_words in skill_phrases.items():
                intersection = submitted_words & existing_words
                union = submitted_words | existing_words
                if union and len(intersection) / len(union) > 0.7:
                    findings.append({
                        "severity": "high",
                        "category": "uniqueness",
                        "description": f"Trigger phrases are too similar to existing skill {skill_id} (Jaccard > 0.7)",
                    })
                    break

        if findings:
            span.set_attribute("submissions.gate1_result", "failed")
            span.set_attribute("submissions.gate1_findings_count", len(findings))
            return GateResult.FAILED, findings

        span.set_attribute("submissions.gate1_result", "passed")
        return GateResult.PASSED, []


async def run_gate2_scan(
    db: Session,
    submission_id: UUID,
) -> dict[str, Any]:
    """Run Gate 2 scan on a submission (async, feature-flag aware).

    Checks llm_judge_enabled feature flag. If disabled, skips with pass verdict.
    When enabled, calls LLMJudgeService.evaluate() for real LLM evaluation.
    Raises ValueError if submission not found.
    """
    with tracer.start_as_current_span("service.submissions.run_gate2_scan") as span:
        span.set_attribute("submissions.submission_id", str(submission_id))

        from skillhub_db.models.flags import FeatureFlag

        from skillhub.schemas.submission import JudgeVerdict
        from skillhub.services.llm_judge import LLMJudgeService, evaluate_gate2_sync

        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            span.set_attribute("submissions.result", "not_found")
            raise ValueError("Submission not found")

        # Check feature flag
        flag = db.query(FeatureFlag).filter(FeatureFlag.key == "llm_judge_enabled").first()
        llm_enabled = flag.enabled if flag else False
        span.set_attribute("submissions.llm_judge_enabled", llm_enabled)

        if not llm_enabled:
            verdict = JudgeVerdict(
                **{"pass": True},
                score=0,
                findings=[],
                summary="LLM judge disabled — auto-pass",
                skipped=True,
            )
        else:
            from skillhub.config import Settings

            settings = Settings()
            judge = LLMJudgeService(
                router_url=settings.llm_router_url,
                enabled=settings.llm_judge_enabled,
            )
            try:
                verdict = await judge.evaluate(submission.content)
            except Exception:
                logger.exception("Gate 2 LLM judge failed unexpectedly")
                verdict = JudgeVerdict(
                    **{"pass": False},
                    score=0,
                    findings=[],
                    summary="Judge unavailable — flagged for manual review",
                )

        gate2_status, gate2_data = evaluate_gate2_sync(verdict)

        submission.status = SubmissionStatus(gate2_status)

        gate_result = SubmissionGateResult(
            id=uuid.uuid4(),
            submission_id=submission.id,
            gate=2,
            result=GateResult(gate2_data["result"]),
            score=gate2_data["score"],
            findings=gate2_data["findings"] if gate2_data["findings"] else None,
        )
        db.add(gate_result)

        _write_audit(
            db,
            event_type="submission.gate2_scanned",
            actor_id=submission.submitted_by,
            target_type="submission",
            target_id=str(submission.id),
            metadata={"gate2_status": gate2_status, "score": gate2_data["score"]},
        )

        db.commit()

        span.set_attribute("submissions.gate2_status", gate2_status)
        return {
            "submission_id": str(submission.id),
            "gate2_status": gate2_status,
            "score": gate2_data["score"],
            "summary": verdict.summary,
        }


def create_submission(
    db: Session,
    *,
    user_id: UUID,
    name: str,
    short_desc: str,
    category: str,
    content: str,
    declared_divisions: list[str],
    division_justification: str,
    background_tasks: Any | None = None,
) -> dict[str, Any]:
    """Create a new submission and run Gate 1 synchronously.

    If Gate 1 passes and llm_judge_enabled flag is True, enqueues Gate 2
    as a background task (when background_tasks is provided).

    Returns dict with submission_id, display_id, status, gate1_result.
    """
    with tracer.start_as_current_span("service.submissions.create_submission") as span:
        span.set_attribute("submissions.user_id", str(user_id))
        span.set_attribute("submissions.name", name)
        span.set_attribute("submissions.category", category)

        display_id = _generate_display_id()

        submission = Submission(
            id=uuid.uuid4(),
            display_id=display_id,
            submitted_by=user_id,
            name=name,
            short_desc=short_desc,
            category=category,
            content=content,
            declared_divisions=declared_divisions,
            division_justification=division_justification,
            status=SubmissionStatus.SUBMITTED,
        )
        db.add(submission)
        db.flush()

        # Run Gate 1
        gate1_result, gate1_findings = run_gate1(db, content, short_desc)

        if gate1_result == GateResult.PASSED:
            submission.status = SubmissionStatus.GATE1_PASSED
        else:
            submission.status = SubmissionStatus.GATE1_FAILED

        gate_result_row = SubmissionGateResult(
            id=uuid.uuid4(),
            submission_id=submission.id,
            gate=1,
            result=gate1_result,
            findings=gate1_findings if gate1_findings else None,
        )
        db.add(gate_result_row)

        # Audit log
        _write_audit(
            db,
            event_type="submission.created",
            actor_id=user_id,
            target_type="submission",
            target_id=str(submission.id),
            metadata={"display_id": display_id, "gate1_result": gate1_result.value},
        )

        db.commit()
        db.refresh(submission)

        # Auto-trigger Gate 2 if Gate 1 passed and LLM judge is enabled
        if gate1_result == GateResult.PASSED and background_tasks is not None:
            from skillhub_db.models.flags import FeatureFlag

            flag = db.query(FeatureFlag).filter(FeatureFlag.key == "llm_judge_enabled").first()
            if flag and flag.enabled:
                background_tasks.add_task(run_gate2_scan, db, submission.id)

        span.set_attribute("submissions.display_id", display_id)
        span.set_attribute("submissions.status", submission.status.value)
        return {
            "id": submission.id,
            "display_id": submission.display_id,
            "status": submission.status.value,
            "gate1_result": {
                "gate": 1,
                "result": gate1_result.value,
                "findings": gate1_findings if gate1_findings else None,
                "score": None,
            },
        }


def get_submission(
    db: Session,
    submission_id: UUID,
    *,
    user_id: UUID,
    is_platform_team: bool = False,
) -> dict[str, Any] | None:
    """Get submission detail. Only owner or platform team can view."""
    with tracer.start_as_current_span("service.submissions.get_submission") as span:
        span.set_attribute("submissions.submission_id", str(submission_id))
        span.set_attribute("submissions.user_id", str(user_id))

        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            span.set_attribute("submissions.result", "not_found")
            return None

        if not is_platform_team and submission.submitted_by != user_id:
            span.set_attribute("submissions.result", "forbidden")
            raise PermissionError("Not authorized to view this submission")

        gate_results = (
            db.query(SubmissionGateResult)
            .filter(SubmissionGateResult.submission_id == submission.id)
            .order_by(SubmissionGateResult.gate)
            .all()
        )

        span.set_attribute("submissions.result", "success")
        return {
            "id": submission.id,
            "display_id": submission.display_id,
            "name": submission.name,
            "short_desc": submission.short_desc,
            "category": submission.category,
            "content": submission.content,
            "declared_divisions": submission.declared_divisions,
            "division_justification": submission.division_justification,
            "status": submission.status.value,
            "submitted_by": submission.submitted_by,
            "gate_results": [
                {
                    "gate": gr.gate,
                    "result": gr.result.value,
                    "findings": gr.findings,
                    "score": gr.score,
                }
                for gr in gate_results
            ],
            "created_at": submission.created_at,
            "updated_at": submission.updated_at,
        }


def list_admin_submissions(
    db: Session,
    *,
    status_filter: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """List submissions for admin. Filter by status, paginated."""
    with tracer.start_as_current_span("service.submissions.list_admin_submissions") as span:
        span.set_attribute("submissions.status_filter", status_filter or "")
        span.set_attribute("submissions.page", page)

        query = db.query(Submission)
        if status_filter:
            query = query.filter(Submission.status == status_filter)

        total = query.count()
        span.set_attribute("submissions.total", total)

        offset = (page - 1) * per_page
        submissions = query.order_by(Submission.created_at.desc()).offset(offset).limit(per_page).all()

        items = [
            {
                "id": s.id,
                "display_id": s.display_id,
                "name": s.name,
                "short_desc": s.short_desc,
                "category": s.category,
                "status": s.status.value,
                "submitted_by": s.submitted_by,
                "declared_divisions": s.declared_divisions,
                "created_at": s.created_at,
            }
            for s in submissions
        ]
        return items, total


def review_submission(
    db: Session,
    submission_id: UUID,
    *,
    reviewer_id: UUID,
    decision: str,
    notes: str,
) -> dict[str, Any]:
    """Gate 3 human review of a submission.

    Returns dict with updated submission info.
    Raises ValueError for invalid state transitions.
    """
    with tracer.start_as_current_span("service.submissions.review_submission") as span:
        span.set_attribute("submissions.submission_id", str(submission_id))
        span.set_attribute("submissions.reviewer_id", str(reviewer_id))
        span.set_attribute("submissions.decision", decision)

        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            span.set_attribute("submissions.result", "not_found")
            raise ValueError("Submission not found")

        reviewable_states = {"gate2_passed", "gate2_flagged"}
        current_status = submission.status.value if hasattr(submission.status, "value") else str(submission.status)
        if current_status not in reviewable_states:
            raise ValueError(f"Submission is not in a reviewable state: {current_status}")

        if decision == "approved":
            submission.status = SubmissionStatus.APPROVED

            # Create Skill + SkillVersion from submission content
            skill_slug = _slugify(submission.name)
            counter = 1
            while db.query(Skill).filter(Skill.slug == skill_slug).first():
                counter += 1
                skill_slug = f"{_slugify(submission.name)}-{counter}"

            # Parse frontmatter for trigger phrases and version
            frontmatter = _parse_frontmatter(submission.content)
            version = "1.0.0"
            if frontmatter and frontmatter.get("version"):
                version = frontmatter["version"]

            import hashlib

            content_hash = hashlib.sha256(submission.content.encode()).hexdigest()

            skill = Skill(
                id=uuid.uuid4(),
                slug=skill_slug,
                name=submission.name,
                short_desc=submission.short_desc,
                category=submission.category,
                author_id=submission.submitted_by,
                current_version=version,
                status=SkillStatus.PUBLISHED,
                published_at=datetime.now(timezone.utc),
            )
            db.add(skill)
            db.flush()

            # Link submission to skill
            submission.skill_id = skill.id

            # Create version
            skill_version = SkillVersion(
                id=uuid.uuid4(),
                skill_id=skill.id,
                version=version,
                content=submission.content,
                frontmatter=frontmatter,
                content_hash=content_hash,
            )
            db.add(skill_version)

            # Add divisions
            for div in submission.declared_divisions:
                sd = SkillDivision(skill_id=skill.id, division_slug=div)
                db.add(sd)

            # Add trigger phrases from frontmatter
            if frontmatter and isinstance(frontmatter.get("trigger_phrases"), list):
                for phrase in frontmatter["trigger_phrases"]:
                    tp = TriggerPhrase(id=uuid.uuid4(), skill_id=skill.id, phrase=phrase)
                    db.add(tp)

            audit_event = "submission.approved"
        elif decision == "changes_requested":
            submission.status = SubmissionStatus.GATE3_CHANGES_REQUESTED
            audit_event = "submission.changes_requested"
        elif decision == "rejected":
            submission.status = SubmissionStatus.REJECTED
            audit_event = "submission.rejected"
        else:
            raise ValueError(f"Invalid decision: {decision}")

        # Gate 3 result
        gate_result = SubmissionGateResult(
            id=uuid.uuid4(),
            submission_id=submission.id,
            gate=3,
            result=GateResult.PASSED if decision == "approved" else GateResult.FAILED,
            reviewer_id=reviewer_id,
            findings=[{"notes": notes}] if notes else None,
        )
        db.add(gate_result)

        _write_audit(
            db,
            event_type=audit_event,
            actor_id=reviewer_id,
            target_type="submission",
            target_id=str(submission.id),
            metadata={"decision": decision, "notes": notes},
        )

        db.commit()
        db.refresh(submission)

        span.set_attribute("submissions.result", "success")
        return {
            "id": submission.id,
            "display_id": submission.display_id,
            "status": submission.status.value,
            "decision": decision,
        }


def create_access_request(
    db: Session,
    *,
    skill_slug: str,
    user_id: UUID,
    user_division: str,
    reason: str,
) -> dict[str, Any]:
    """Create a division access request.

    Raises ValueError if user is already in an authorized division.
    """
    with tracer.start_as_current_span("service.submissions.create_access_request") as span:
        span.set_attribute("submissions.skill_slug", skill_slug)
        span.set_attribute("submissions.user_id", str(user_id))
        span.set_attribute("submissions.user_division", user_division)

        skill = db.query(Skill).filter(Skill.slug == skill_slug).first()
        if not skill:
            span.set_attribute("submissions.result", "not_found")
            raise ValueError(f"Skill '{skill_slug}' not found")

        # Check if user's division is already authorized
        authorized = (
            db.query(SkillDivision)
            .filter(
                SkillDivision.skill_id == skill.id,
                SkillDivision.division_slug == user_division,
            )
            .first()
        )
        if authorized:
            span.set_attribute("submissions.result", "already_authorized")
            raise ValueError("User's division already has access to this skill")

        request = DivisionAccessRequest(
            id=uuid.uuid4(),
            skill_id=skill.id,
            requested_by=user_id,
            user_division=user_division,
            reason=reason,
        )
        db.add(request)

        _write_audit(
            db,
            event_type="access_request_created",
            actor_id=user_id,
            target_type="division_access_request",
            target_id=str(request.id),
            metadata={"skill_slug": skill_slug, "user_division": user_division},
        )

        db.commit()
        db.refresh(request)

        span.set_attribute("submissions.result", "success")
        return {
            "id": request.id,
            "skill_id": request.skill_id,
            "requested_by": request.requested_by,
            "user_division": request.user_division,
            "reason": request.reason,
            "status": request.status.value,
            "created_at": request.created_at,
        }


def list_access_requests(
    db: Session,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """List all access requests for admin."""
    with tracer.start_as_current_span("service.submissions.list_access_requests") as span:
        span.set_attribute("submissions.page", page)

        query = db.query(DivisionAccessRequest)
        total = query.count()
        span.set_attribute("submissions.total", total)

        offset = (page - 1) * per_page
        requests = query.order_by(DivisionAccessRequest.created_at.desc()).offset(offset).limit(per_page).all()

        items = [
            {
                "id": r.id,
                "skill_id": r.skill_id,
                "requested_by": r.requested_by,
                "user_division": r.user_division,
                "reason": r.reason,
                "status": r.status.value,
                "created_at": r.created_at,
            }
            for r in requests
        ]
        return items, total


def review_access_request(
    db: Session,
    request_id: UUID,
    *,
    reviewer_id: UUID,
    decision: str,
) -> dict[str, Any]:
    """Review a division access request.

    Raises ValueError if request not found or invalid decision.
    """
    with tracer.start_as_current_span("service.submissions.review_access_request") as span:
        span.set_attribute("submissions.request_id", str(request_id))
        span.set_attribute("submissions.decision", decision)

        access_req = db.query(DivisionAccessRequest).filter(DivisionAccessRequest.id == request_id).first()
        if not access_req:
            span.set_attribute("submissions.result", "not_found")
            raise ValueError("Access request not found")

        if decision == "approved":
            access_req.status = AccessRequestStatus.APPROVED
            # Add user's division to skill_divisions
            sd = SkillDivision(skill_id=access_req.skill_id, division_slug=access_req.user_division)
            db.add(sd)
        elif decision == "denied":
            access_req.status = AccessRequestStatus.DENIED
        else:
            raise ValueError(f"Invalid decision: {decision}")

        _write_audit(
            db,
            event_type="access_request_reviewed",
            actor_id=reviewer_id,
            target_type="division_access_request",
            target_id=str(access_req.id),
            metadata={"decision": decision},
        )

        db.commit()
        db.refresh(access_req)

        span.set_attribute("submissions.result", "success")
        return {
            "id": access_req.id,
            "status": access_req.status.value,
            "decision": decision,
        }
