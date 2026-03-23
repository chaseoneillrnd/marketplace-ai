"""Submission pipeline endpoints — create, view, admin review."""

from __future__ import annotations

import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_current_user, get_db, require_platform_team
from skillhub.schemas.submission import (
    AccessRequestCreateRequest,
    AccessRequestDetail,
    AccessRequestReviewRequest,
    AccessRequestsResponse,
    AdminSubmissionsResponse,
    ReviewDecisionRequest,
    SubmissionCreateRequest,
    SubmissionCreateResponse,
    SubmissionDetail,
)
from skillhub.services.submissions import (
    create_access_request,
    create_submission,
    get_submission,
    list_access_requests,
    list_admin_submissions,
    review_access_request,
    review_submission,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["submissions"])


@router.post(
    "/api/v1/submissions",
    response_model=SubmissionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_submission(
    body: SubmissionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    background_tasks: BackgroundTasks,
) -> SubmissionCreateResponse:
    """Create a new skill submission and run Gate 1 validation."""
    user_id = uuid.UUID(current_user["user_id"])

    result = create_submission(
        db,
        user_id=user_id,
        name=body.name,
        short_desc=body.short_desc,
        category=body.category,
        content=body.content,
        declared_divisions=body.declared_divisions,
        division_justification=body.division_justification,
        background_tasks=background_tasks,
    )

    return SubmissionCreateResponse(**result)


@router.get("/api/v1/submissions/{submission_id}", response_model=SubmissionDetail)
def get_submission_detail(
    submission_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> SubmissionDetail:
    """Get submission detail. Owner or platform team only."""
    user_id = uuid.UUID(current_user["user_id"])
    is_platform_team = current_user.get("is_platform_team", False)

    try:
        sub_uuid = uuid.UUID(submission_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid submission ID",
        ) from err

    try:
        result = get_submission(
            db,
            sub_uuid,
            user_id=user_id,
            is_platform_team=is_platform_team,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    return SubmissionDetail(**result)


# --- Admin endpoints ---


@router.post("/api/v1/admin/submissions/{submission_id}/scan")
async def scan_submission(
    submission_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> dict[str, Any]:
    """Trigger Gate 2 LLM scan on a submission. Platform/Security team only."""
    from skillhub.services.submissions import run_gate2_scan

    try:
        sub_uuid = uuid.UUID(submission_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid submission ID",
        ) from err

    try:
        result = await run_gate2_scan(db, sub_uuid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return result


@router.get("/api/v1/admin/submissions", response_model=AdminSubmissionsResponse)
def list_submissions_admin(
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
    status_filter: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> AdminSubmissionsResponse:
    """List all submissions. Platform team only."""
    items, total = list_admin_submissions(
        db,
        status_filter=status_filter,
        page=page,
        per_page=per_page,
    )
    has_more = (page * per_page) < total
    return AdminSubmissionsResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.post("/api/v1/admin/submissions/{submission_id}/review")
def review_submission_endpoint(
    submission_id: str,
    body: ReviewDecisionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> dict[str, Any]:
    """Gate 3 human review. Platform team only."""
    reviewer_id = uuid.UUID(current_user["user_id"])

    try:
        sub_uuid = uuid.UUID(submission_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid submission ID",
        ) from err

    try:
        result = review_submission(
            db,
            sub_uuid,
            reviewer_id=reviewer_id,
            decision=body.decision,
            notes=body.notes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return result


# --- Division Access Request endpoints ---


@router.post(
    "/api/v1/skills/{slug}/access-request",
    response_model=AccessRequestDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_skill_access_request(
    slug: str,
    body: AccessRequestCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> AccessRequestDetail:
    """Request access to a skill from a different division."""
    user_id = uuid.UUID(current_user["user_id"])
    user_division = current_user.get("division", "")

    try:
        result = create_access_request(
            db,
            skill_slug=slug,
            user_id=user_id,
            user_division=user_division,
            reason=body.reason,
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        ) from e

    return AccessRequestDetail(**result)


@router.get("/api/v1/admin/access-requests", response_model=AccessRequestsResponse)
def list_access_requests_admin(
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> AccessRequestsResponse:
    """List all access requests. Platform team only."""
    items, total = list_access_requests(db, page=page, per_page=per_page)
    has_more = (page * per_page) < total
    return AccessRequestsResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.post("/api/v1/admin/access-requests/{request_id}/review")
def review_access_request_endpoint(
    request_id: str,
    body: AccessRequestReviewRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> dict[str, Any]:
    """Review a division access request. Platform team only."""
    reviewer_id = uuid.UUID(current_user["user_id"])

    try:
        req_uuid = uuid.UUID(request_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID",
        ) from err

    try:
        result = review_access_request(db, req_uuid, reviewer_id=reviewer_id, decision=body.decision)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return result
