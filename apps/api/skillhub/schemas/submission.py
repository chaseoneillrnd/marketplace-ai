"""Pydantic v2 schemas for the Submission pipeline domain."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SubmissionCreateRequest(BaseModel):
    """Request body for creating a new submission."""

    name: str = Field(..., min_length=1, max_length=255)
    short_desc: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, description="SKILL.md text")
    declared_divisions: list[str] = Field(..., min_length=1)
    division_justification: str = Field(..., min_length=1)


class GateFinding(BaseModel):
    """A single finding from a gate check."""

    severity: str
    category: str
    description: str


class GateResultResponse(BaseModel):
    """Gate result summary."""

    model_config = ConfigDict(from_attributes=True)

    gate: int
    result: str
    findings: list[GateFinding] | None = None
    score: int | None = None


class SubmissionCreateResponse(BaseModel):
    """Response after creating a submission."""

    id: UUID
    display_id: str
    status: str
    gate1_result: GateResultResponse


class SubmissionDetail(BaseModel):
    """Full submission detail."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_id: str
    name: str
    short_desc: str
    category: str
    content: str
    declared_divisions: list[str]
    division_justification: str
    status: str
    submitted_by: UUID
    gate_results: list[GateResultResponse] = []
    created_at: datetime | str
    updated_at: datetime | str | None = None


class AdminSubmissionSummary(BaseModel):
    """Submission summary for admin listing."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_id: str
    name: str
    short_desc: str
    category: str
    status: str
    submitted_by: UUID
    declared_divisions: list[str]
    created_at: datetime | str


class AdminSubmissionsResponse(BaseModel):
    """Paginated admin submissions list."""

    items: list[AdminSubmissionSummary]
    total: int
    page: int
    per_page: int
    has_more: bool


class ReviewDecisionRequest(BaseModel):
    """Request body for Gate 3 human review."""

    decision: str = Field(..., pattern="^(approved|changes_requested|rejected)$")
    notes: str = Field(..., min_length=1)


class AccessRequestCreateRequest(BaseModel):
    """Request body for division access request."""

    reason: str = Field(..., min_length=1)


class AccessRequestDetail(BaseModel):
    """Division access request detail."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    skill_id: UUID
    requested_by: UUID
    user_division: str
    reason: str
    status: str
    created_at: datetime | str


class AccessRequestReviewRequest(BaseModel):
    """Request body for reviewing an access request."""

    decision: str = Field(..., pattern="^(approved|denied)$")


class AccessRequestsResponse(BaseModel):
    """Paginated access requests list."""

    items: list[AccessRequestDetail]
    total: int
    page: int
    per_page: int
    has_more: bool


class JudgeVerdict(BaseModel):
    """LLM judge verdict."""

    pass_: bool = Field(..., alias="pass")
    score: int
    findings: list[GateFinding] = []
    summary: str
    skipped: bool = False

    model_config = ConfigDict(populate_by_name=True)
