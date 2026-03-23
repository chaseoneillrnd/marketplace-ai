"""Export endpoints — admin only."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_db, require_platform_team
from skillhub.services.exports import get_export_status, request_export

router = APIRouter(prefix="/api/v1/admin/exports", tags=["exports"])


@router.post("")
def create_export(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[dict[str, Any], Depends(require_platform_team)],
    scope: str = "installs",
    format: str = "csv",
) -> dict[str, Any]:
    """Request a new data export job."""
    try:
        return request_export(db, user_id=UUID(user["user_id"]), scope=scope, format=format)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))


@router.get("/{job_id}")
def export_status(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> dict[str, Any]:
    """Get the status of an export job."""
    result = get_export_status(db, UUID(job_id))
    if not result:
        raise HTTPException(status_code=404, detail="Export job not found")
    return result
