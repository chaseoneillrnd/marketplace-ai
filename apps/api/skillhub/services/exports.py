"""Export service — request, rate-limit, generate."""

from __future__ import annotations

import csv
import io
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from skillhub_db.models.analytics import DailyMetrics, ExportJob
from skillhub_db.models.social import Install
from skillhub_db.models.submission import Submission
from skillhub_db.models.user import User

logger = logging.getLogger(__name__)

MAX_EXPORTS_PER_DAY = 5


def _query_scope_rows(db: Session, scope: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Query the appropriate table based on scope, applying optional date filters."""
    start_date: datetime | None = None
    end_date: datetime | None = None

    if filters.get("start_date"):
        start_date = datetime.fromisoformat(str(filters["start_date"])).replace(tzinfo=timezone.utc)
    if filters.get("end_date"):
        # Make end_date inclusive by advancing to end of day
        end_date = datetime.fromisoformat(str(filters["end_date"])).replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )

    if scope == "installs":
        q = db.query(Install)
        if start_date:
            q = q.filter(Install.installed_at >= start_date)
        if end_date:
            q = q.filter(Install.installed_at <= end_date)
        return [
            {
                "id": str(r.id),
                "skill_id": str(r.skill_id),
                "user_id": str(r.user_id),
                "version": r.version,
                "method": r.method,
                "installed_at": r.installed_at.isoformat() if r.installed_at else None,
                "uninstalled_at": r.uninstalled_at.isoformat() if r.uninstalled_at else None,
            }
            for r in q.all()
        ]

    if scope == "submissions":
        q = db.query(Submission)
        if start_date:
            q = q.filter(Submission.created_at >= start_date)
        if end_date:
            q = q.filter(Submission.created_at <= end_date)
        return [
            {
                "id": str(r.id),
                "display_id": r.display_id,
                "name": r.name,
                "category": r.category,
                "status": str(r.status),
                "submitted_by": str(r.submitted_by),
                "revision_number": r.revision_number,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in q.all()
        ]

    if scope == "users":
        q = db.query(User)
        if start_date:
            q = q.filter(User.created_at >= start_date)
        if end_date:
            q = q.filter(User.created_at <= end_date)
        return [
            {
                "id": str(r.id),
                "username": r.username,
                "email": r.email,
                "name": r.name,
                "division": r.division,
                "role": r.role,
                "is_platform_team": r.is_platform_team,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in q.all()
        ]

    if scope == "analytics":
        q = db.query(DailyMetrics)
        if start_date:
            q = q.filter(DailyMetrics.metric_date >= start_date.date())
        if end_date:
            q = q.filter(DailyMetrics.metric_date <= end_date.date())
        return [
            {
                "metric_date": str(r.metric_date),
                "division_slug": r.division_slug,
                "new_installs": r.new_installs,
                "active_installs": r.active_installs,
                "uninstalls": r.uninstalls,
                "dau": r.dau,
                "new_users": r.new_users,
                "new_submissions": r.new_submissions,
                "published_skills": r.published_skills,
                "funnel_submitted": r.funnel_submitted,
                "funnel_approved": r.funnel_approved,
            }
            for r in q.all()
        ]

    return []


def _rows_to_content(rows: list[dict[str, Any]], fmt: str) -> str:
    """Serialize rows to CSV or JSON string."""
    if fmt == "json":
        return json.dumps(rows, default=str)

    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def run_export_sync(db: Session, job_id: uuid.UUID) -> None:
    """Execute an export job synchronously, writing content into file_path and marking done."""
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job:
        logger.error("run_export_sync: job %s not found", job_id)
        return

    job.status = "processing"
    db.commit()

    try:
        rows = _query_scope_rows(db, job.scope, job.filters or {})
        content = _rows_to_content(rows, job.format)

        job.status = "done"
        job.row_count = len(rows)
        # Store inline content in file_path (prefixed so callers can detect it)
        job.file_path = f"inline:{content}"
        job.completed_at = datetime.now(timezone.utc)
    except Exception:
        logger.exception("run_export_sync: export failed for job %s", job_id)
        job.status = "failed"
        job.error = "Export generation failed"
        job.completed_at = datetime.now(timezone.utc)

    db.commit()


def request_export(
    db: Session,
    *,
    user_id: uuid.UUID,
    scope: str,
    format: str = "csv",
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an export job. Rate-limited to 5/user/24hr."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_count = (
        db.query(ExportJob)
        .filter(
            ExportJob.requested_by == user_id,
            ExportJob.created_at >= cutoff,
        )
        .count()
    )
    if recent_count >= MAX_EXPORTS_PER_DAY:
        raise ValueError(f"Rate limit exceeded: {MAX_EXPORTS_PER_DAY} exports per 24 hours")

    job = ExportJob(
        id=uuid.uuid4(),
        requested_by=user_id,
        scope=scope,
        format=format,
        filters=filters or {},
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"id": str(job.id), "status": "pending", "scope": scope, "format": format}


def get_export_status(db: Session, job_id: uuid.UUID) -> dict[str, Any] | None:
    """Get export job status."""
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job:
        return None
    # Map internal status names to the frontend contract.
    # DB stores "queued" → client sees "pending"; "done" → "complete".
    _status_map = {"queued": "pending", "processing": "processing", "done": "complete", "failed": "failed"}
    client_status = _status_map.get(job.status, job.status)

    return {
        "id": str(job.id),
        "status": client_status,
        "scope": job.scope,
        "format": job.format,
        "row_count": job.row_count,
        # Expose as download_url to match frontend ExportStatus interface.
        # file_path is an internal filesystem path; callers should not depend on it.
        "download_url": job.file_path,
        "error": job.error,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }
