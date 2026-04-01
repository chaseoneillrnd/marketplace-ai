"""Review queue schemas — HITL approval workflow."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ReviewQueueItem(BaseModel):
    """Single item in the review queue."""

    submission_id: str
    display_id: str | None = None
    skill_name: str
    short_desc: str
    category: str
    submitter_name: str | None = None
    submitted_at: datetime | None = None
    gate1_passed: bool
    gate2_score: float | None = None
    gate2_summary: str | None = None
    content_preview: str
    wait_time_hours: float
    divisions: list[str]


class ReviewQueueResponse(BaseModel):
    """Paginated review queue response."""

    items: list[ReviewQueueItem]
    total: int
    page: int
    per_page: int
    has_more: bool


class ClaimResponse(BaseModel):
    """Response after claiming a submission for review."""

    submission_id: str
    reviewer_id: str
    claimed_at: datetime


class DecisionRequest(BaseModel):
    """Request body for a review decision."""

    decision: str  # "approve" | "reject" | "request_changes"
    notes: str = ""
    score: int | None = None


class DecisionResponse(BaseModel):
    """Response after making a review decision."""

    submission_id: str
    decision: str
    reviewer_id: str
    reviewed_at: datetime
