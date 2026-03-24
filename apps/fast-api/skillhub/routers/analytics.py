"""Analytics endpoints — admin only."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from skillhub.dependencies import get_db, require_platform_team
from skillhub.schemas.analytics import (
    AnalyticsSummary,
    FunnelResponse,
    TimeSeriesResponse,
    TopSkillsResponse,
)
from skillhub.services.analytics import (
    get_submission_funnel,
    get_summary,
    get_time_series,
    get_top_skills,
)

router = APIRouter(prefix="/api/v1/admin/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def analytics_summary(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
    division: str = "__all__",
) -> AnalyticsSummary:
    result = get_summary(db, division=division)
    return AnalyticsSummary(**result)


@router.get("/time-series", response_model=TimeSeriesResponse)
def analytics_time_series(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
    days: int = Query(default=30, ge=1, le=365),
    division: str = "__all__",
) -> TimeSeriesResponse:
    series = get_time_series(db, days=days, division=division)
    return TimeSeriesResponse(series=series, days=days, division=division)


@router.get("/submission-funnel", response_model=FunnelResponse)
def analytics_funnel(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
    days: int = Query(default=30, ge=1, le=365),
    division: str = "__all__",
) -> FunnelResponse:
    result = get_submission_funnel(db, days=days, division=division)
    return FunnelResponse(**result)


@router.get("/top-skills", response_model=TopSkillsResponse)
def analytics_top_skills(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(require_platform_team)],
    limit: int = Query(default=10, ge=1, le=50),
) -> TopSkillsResponse:
    items = get_top_skills(db, limit=limit)
    return TopSkillsResponse(items=items)
