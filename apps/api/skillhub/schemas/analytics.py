"""Pydantic schemas for analytics endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    dau: int
    new_installs_7d: int
    active_installs: int
    published_skills: int
    pending_reviews: int
    submission_pass_rate: float
    period: str


class TimeSeriesPoint(BaseModel):
    date: str
    installs: int
    users: int
    submissions: int
    reviews: int


class TimeSeriesResponse(BaseModel):
    series: list[TimeSeriesPoint]
    days: int
    division: str


class FunnelResponse(BaseModel):
    submitted: int
    gate1_passed: int
    gate2_passed: int
    approved: int
    published: int
    gate1_rate: float
    gate2_rate: float
    approval_rate: float
    period_days: int


class TopSkill(BaseModel):
    slug: str
    name: str
    installs: int
    rating: float


class TopSkillsResponse(BaseModel):
    items: list[TopSkill]
