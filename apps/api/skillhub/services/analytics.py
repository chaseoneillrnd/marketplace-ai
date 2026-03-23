"""Analytics service — aggregation, summary, time-series."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from skillhub_db.models.analytics import DailyMetrics

logger = logging.getLogger(__name__)


def get_summary(db: Session, division: str = "__all__") -> dict[str, Any]:
    """Get dashboard summary: totals + 7-day deltas."""
    today = date.today()
    week_ago = today - timedelta(days=7)

    # Current totals (latest row)
    latest = (
        db.query(DailyMetrics)
        .filter(DailyMetrics.division_slug == division)
        .order_by(DailyMetrics.metric_date.desc())
        .first()
    )

    if not latest:
        return {
            "dau": 0,
            "new_installs_7d": 0,
            "active_installs": 0,
            "published_skills": 0,
            "pending_reviews": 0,
            "submission_pass_rate": 0.0,
            "period": "7d",
        }

    # Sum last 7 days
    week_rows = (
        db.query(DailyMetrics)
        .filter(
            DailyMetrics.division_slug == division,
            DailyMetrics.metric_date >= week_ago,
        )
        .all()
    )

    installs_7d = sum(r.new_installs for r in week_rows)
    submissions_7d = sum(r.funnel_submitted for r in week_rows)
    approved_7d = sum(r.funnel_approved for r in week_rows)
    pass_rate = (approved_7d / submissions_7d * 100) if submissions_7d > 0 else 0.0

    return {
        "dau": latest.dau,
        "new_installs_7d": installs_7d,
        "active_installs": latest.active_installs,
        "published_skills": latest.published_skills,
        "pending_reviews": 0,  # Would need submission query
        "submission_pass_rate": round(pass_rate, 1),
        "period": "7d",
    }


def get_time_series(
    db: Session, days: int = 30, division: str = "__all__"
) -> list[dict[str, Any]]:
    """Get daily metrics time series for charts."""
    start = date.today() - timedelta(days=days)
    rows = (
        db.query(DailyMetrics)
        .filter(
            DailyMetrics.division_slug == division,
            DailyMetrics.metric_date >= start,
        )
        .order_by(DailyMetrics.metric_date.asc())
        .all()
    )
    return [
        {
            "date": str(r.metric_date),
            "installs": r.new_installs,
            "users": r.dau,
            "submissions": r.new_submissions,
            "reviews": r.new_reviews,
        }
        for r in rows
    ]


def get_submission_funnel(
    db: Session, days: int = 30, division: str = "__all__"
) -> dict[str, Any]:
    """Get submission funnel conversion rates."""
    start = date.today() - timedelta(days=days)
    rows = (
        db.query(DailyMetrics)
        .filter(
            DailyMetrics.division_slug == division,
            DailyMetrics.metric_date >= start,
        )
        .all()
    )

    submitted = sum(r.funnel_submitted for r in rows)
    g1 = sum(r.funnel_g1_pass for r in rows)
    g2 = sum(r.funnel_g2_pass for r in rows)
    approved = sum(r.funnel_approved for r in rows)
    published = sum(r.funnel_published for r in rows)

    return {
        "submitted": submitted,
        "gate1_passed": g1,
        "gate2_passed": g2,
        "approved": approved,
        "published": published,
        "gate1_rate": round(g1 / submitted * 100, 1) if submitted else 0,
        "gate2_rate": round(g2 / g1 * 100, 1) if g1 else 0,
        "approval_rate": round(approved / g2 * 100, 1) if g2 else 0,
        "period_days": days,
    }


def get_top_skills(db: Session, limit: int = 10) -> list[dict[str, Any]]:
    """Get top skills by install count."""
    from skillhub_db.models.skill import Skill

    skills = (
        db.query(Skill)
        .filter(Skill.status == "published")
        .order_by(Skill.install_count.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "slug": s.slug,
            "name": s.name,
            "installs": s.install_count,
            "rating": float(s.avg_rating),
        }
        for s in skills
    ]
