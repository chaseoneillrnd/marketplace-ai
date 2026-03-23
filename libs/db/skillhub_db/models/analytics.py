"""Analytics domain models."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from skillhub_db.base import Base


class DailyMetrics(Base):
    """Aggregated daily metrics per division (or platform-wide with '__all__')."""

    __tablename__ = "daily_metrics"

    metric_date: Mapped[date] = mapped_column(Date, primary_key=True)
    division_slug: Mapped[str] = mapped_column(String(100), primary_key=True)

    new_installs: Mapped[int] = mapped_column(Integer, default=0)
    active_installs: Mapped[int] = mapped_column(Integer, default=0)
    uninstalls: Mapped[int] = mapped_column(Integer, default=0)
    dau: Mapped[int] = mapped_column(Integer, default=0)
    new_users: Mapped[int] = mapped_column(Integer, default=0)
    new_submissions: Mapped[int] = mapped_column(Integer, default=0)
    published_skills: Mapped[int] = mapped_column(Integer, default=0)
    new_reviews: Mapped[int] = mapped_column(Integer, default=0)

    funnel_submitted: Mapped[int] = mapped_column(Integer, default=0)
    funnel_g1_pass: Mapped[int] = mapped_column(Integer, default=0)
    funnel_g2_pass: Mapped[int] = mapped_column(Integer, default=0)
    funnel_approved: Mapped[int] = mapped_column(Integer, default=0)
    funnel_published: Mapped[int] = mapped_column(Integer, default=0)

    gate3_median_wait: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ExportJob(Base):
    """Async data-export job tracker."""

    __tablename__ = "export_jobs"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[str] = mapped_column(String(10), default="csv")
    filters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
