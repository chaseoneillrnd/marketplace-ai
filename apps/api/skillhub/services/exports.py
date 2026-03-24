"""Export service — request, rate-limit, generate."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from skillhub_db.models.analytics import ExportJob

logger = logging.getLogger(__name__)

MAX_EXPORTS_PER_DAY = 5


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
