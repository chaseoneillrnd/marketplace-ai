"""Review queue endpoints — admin HITL review."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_db, require_platform_team
from skillhub.schemas.review_queue import (
    ClaimResponse,
    DecisionRequest,
    DecisionResponse,
    ReviewQueueItem,
    ReviewQueueResponse,
)
from skillhub.services.review_queue import (
    claim_submission,
    decide_submission,
    get_review_queue,
)

router = APIRouter(prefix="/api/v1/admin/review-queue", tags=["review-queue"])


@router.get("", response_model=ReviewQueueResponse)
def list_review_queue(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> ReviewQueueResponse:
    """List submissions awaiting human review."""
    items, total = get_review_queue(db, page=page, per_page=per_page)
    return ReviewQueueResponse(
        items=[ReviewQueueItem(**i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )


@router.post("/{submission_id}/claim", response_model=ClaimResponse)
def claim(
    submission_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> ClaimResponse:
    """Claim a submission for review."""
    try:
        result = claim_submission(
            db,
            submission_id=UUID(submission_id),
            reviewer_id=UUID(user["user_id"]),
        )
        return ClaimResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


@router.post("/{submission_id}/decision", response_model=DecisionResponse)
def decide(
    submission_id: str,
    body: DecisionRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> DecisionResponse:
    """Make a review decision on a submission."""
    try:
        result = decide_submission(
            db,
            submission_id=UUID(submission_id),
            reviewer_id=UUID(user["user_id"]),
            decision=body.decision,
            notes=body.notes,
            score=body.score,
        )
        return DecisionResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        ) from e
