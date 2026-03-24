"""Feedback endpoints — submit, list, upvote, triage."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_current_user, get_db, require_platform_team
from skillhub.schemas.feedback import (
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackResponse,
)
from skillhub.services.feedback import (
    create_feedback,
    list_feedback,
    update_feedback_status,
    upvote_feedback,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])


@router.post("/api/v1/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    body: FeedbackCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> FeedbackResponse:
    """Submit feedback. Any authenticated user."""
    result = create_feedback(
        db,
        user_id=current_user["user_id"],
        category=body.category,
        body=body.body,
        skill_id=str(body.skill_id) if body.skill_id else None,
        allow_contact=body.allow_contact,
    )
    return FeedbackResponse(**result)


@router.get("/api/v1/admin/feedback", response_model=FeedbackListResponse)
def list_feedback_admin(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
    category: str | None = None,
    sentiment: str | None = None,
    feedback_status: str | None = Query(default=None, alias="status"),
    sort: str = Query(default="priority"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> FeedbackListResponse:
    """List all feedback. Admin only, filtered/sorted/paginated."""
    items, total = list_feedback(
        db,
        category=category,
        sentiment=sentiment,
        status=feedback_status,
        sort=sort,
        page=page,
        per_page=per_page,
    )
    return FeedbackListResponse(
        items=[FeedbackResponse(**i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )


@router.post("/api/v1/feedback/{feedback_id}/upvote")
def upvote_feedback_endpoint(
    feedback_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """Upvote a feedback entry. Any authenticated user."""
    try:
        result = upvote_feedback(
            db,
            feedback_id=feedback_id,
            user_id=current_user["user_id"],
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return result


@router.patch("/api/v1/admin/feedback/{feedback_id}/status")
def update_feedback_status_endpoint(
    feedback_id: str,
    body: dict[str, str],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> FeedbackResponse:
    """Update feedback status. Admin only."""
    new_status = body.get("status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="status is required",
        )
    try:
        result = update_feedback_status(
            db,
            feedback_id=feedback_id,
            status=new_status,
            actor_id=current_user["user_id"],
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return FeedbackResponse(**result)
