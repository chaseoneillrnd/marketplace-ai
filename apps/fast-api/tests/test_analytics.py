"""Tests for analytics service and router."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from skillhub.services.analytics import (
    get_submission_funnel,
    get_summary,
    get_time_series,
    get_top_skills,
)
from tests.conftest import _make_settings, make_token

ADMIN_USER_ID = str(uuid.uuid4())
REGULAR_USER_ID = str(uuid.uuid4())


def _admin_headers() -> dict[str, str]:
    token = make_token(
        {
            "sub": "admin",
            "user_id": ADMIN_USER_ID,
            "division": "engineering",
            "role": "admin",
            "is_platform_team": True,
            "is_security_team": False,
            "name": "Admin User",
        }
    )
    return {"Authorization": f"Bearer {token}"}


def _regular_headers() -> dict[str, str]:
    token = make_token(
        {
            "sub": "regular",
            "user_id": REGULAR_USER_ID,
            "division": "engineering",
            "role": "user",
            "is_platform_team": False,
            "is_security_team": False,
            "name": "Regular User",
        }
    )
    return {"Authorization": f"Bearer {token}"}


def _make_client(db_mock: MagicMock | None = None) -> TestClient:
    settings = _make_settings()
    app = create_app(settings=settings)
    if db_mock is not None:
        app.dependency_overrides[get_db] = lambda: db_mock
    return TestClient(app)


def _mock_metrics_row(**overrides: Any) -> MagicMock:
    row = MagicMock()
    row.metric_date = overrides.get("metric_date", date.today())
    row.division_slug = overrides.get("division_slug", "__all__")
    row.new_installs = overrides.get("new_installs", 10)
    row.active_installs = overrides.get("active_installs", 50)
    row.dau = overrides.get("dau", 25)
    row.published_skills = overrides.get("published_skills", 30)
    row.new_submissions = overrides.get("new_submissions", 3)
    row.new_reviews = overrides.get("new_reviews", 2)
    row.funnel_submitted = overrides.get("funnel_submitted", 5)
    row.funnel_g1_pass = overrides.get("funnel_g1_pass", 4)
    row.funnel_g2_pass = overrides.get("funnel_g2_pass", 3)
    row.funnel_approved = overrides.get("funnel_approved", 3)
    row.funnel_published = overrides.get("funnel_published", 2)
    return row


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestGetSummary:
    def test_empty_db_returns_zeros(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )
        result = get_summary(db)
        assert result["dau"] == 0
        assert result["new_installs_7d"] == 0
        assert result["active_installs"] == 0
        assert result["submission_pass_rate"] == 0.0

    def test_with_data_returns_metrics(self) -> None:
        db = MagicMock()
        latest = _mock_metrics_row(dau=25, active_installs=50, published_skills=30)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            latest
        )
        week_rows = [
            _mock_metrics_row(new_installs=10, funnel_submitted=5, funnel_approved=3),
            _mock_metrics_row(new_installs=8, funnel_submitted=4, funnel_approved=2),
        ]
        db.query.return_value.filter.return_value.all.return_value = week_rows
        result = get_summary(db)
        assert result["dau"] == 25
        assert result["active_installs"] == 50
        assert result["new_installs_7d"] == 18
        assert result["submission_pass_rate"] == round(5 / 9 * 100, 1)

    def test_pass_rate_zero_when_no_submissions(self) -> None:
        db = MagicMock()
        latest = _mock_metrics_row()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            latest
        )
        week_rows = [_mock_metrics_row(funnel_submitted=0, funnel_approved=0)]
        db.query.return_value.filter.return_value.all.return_value = week_rows
        result = get_summary(db)
        assert result["submission_pass_rate"] == 0.0


class TestGetTimeSeries:
    def test_empty_returns_empty_list(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )
        result = get_time_series(db, days=7)
        assert result == []

    def test_returns_formatted_rows(self) -> None:
        db = MagicMock()
        row = _mock_metrics_row(
            metric_date=date(2026, 3, 20),
            new_installs=15,
            dau=30,
            new_submissions=4,
            new_reviews=2,
        )
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            row
        ]
        result = get_time_series(db, days=7)
        assert len(result) == 1
        assert result[0]["date"] == "2026-03-20"
        assert result[0]["installs"] == 15
        assert result[0]["users"] == 30


class TestGetSubmissionFunnel:
    def test_empty_returns_zeros(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_submission_funnel(db)
        assert result["submitted"] == 0
        assert result["gate1_rate"] == 0
        assert result["gate2_rate"] == 0

    def test_calculates_rates(self) -> None:
        db = MagicMock()
        rows = [
            _mock_metrics_row(
                funnel_submitted=10,
                funnel_g1_pass=8,
                funnel_g2_pass=6,
                funnel_approved=5,
                funnel_published=4,
            )
        ]
        db.query.return_value.filter.return_value.all.return_value = rows
        result = get_submission_funnel(db)
        assert result["submitted"] == 10
        assert result["gate1_passed"] == 8
        assert result["gate1_rate"] == 80.0
        assert result["gate2_rate"] == 75.0
        assert result["approval_rate"] == round(5 / 6 * 100, 1)


class TestGetTopSkills:
    def test_empty_returns_empty_list(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )
        result = get_top_skills(db)
        assert result == []

    def test_returns_skill_dicts(self) -> None:
        db = MagicMock()
        skill = MagicMock()
        skill.slug = "cool-skill"
        skill.name = "Cool Skill"
        skill.install_count = 100
        skill.avg_rating = 4.5
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            skill
        ]
        result = get_top_skills(db)
        assert len(result) == 1
        assert result[0]["slug"] == "cool-skill"
        assert result[0]["installs"] == 100
        assert result[0]["rating"] == 4.5


# ---------------------------------------------------------------------------
# Router tests
# ---------------------------------------------------------------------------


class TestAnalyticsRouter:
    def test_summary_requires_auth(self) -> None:
        client = _make_client()
        resp = client.get("/api/v1/admin/analytics/summary")
        assert resp.status_code == 401

    def test_summary_requires_platform_team(self) -> None:
        client = _make_client()
        resp = client.get(
            "/api/v1/admin/analytics/summary", headers=_regular_headers()
        )
        assert resp.status_code == 403

    @patch("skillhub.routers.analytics.get_summary")
    def test_summary_returns_200(self, mock_summary: MagicMock) -> None:
        mock_summary.return_value = {
            "dau": 25,
            "new_installs_7d": 18,
            "active_installs": 50,
            "published_skills": 30,
            "pending_reviews": 0,
            "submission_pass_rate": 55.6,
            "period": "7d",
        }
        db_mock = MagicMock()
        client = _make_client(db_mock)
        resp = client.get(
            "/api/v1/admin/analytics/summary", headers=_admin_headers()
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["dau"] == 25
        assert data["new_installs_7d"] == 18

    def test_time_series_requires_auth(self) -> None:
        client = _make_client()
        resp = client.get("/api/v1/admin/analytics/time-series")
        assert resp.status_code == 401

    @patch("skillhub.routers.analytics.get_time_series")
    def test_time_series_returns_200(self, mock_ts: MagicMock) -> None:
        mock_ts.return_value = [
            {
                "date": "2026-03-20",
                "installs": 10,
                "users": 20,
                "submissions": 3,
                "reviews": 1,
            }
        ]
        db_mock = MagicMock()
        client = _make_client(db_mock)
        resp = client.get(
            "/api/v1/admin/analytics/time-series", headers=_admin_headers()
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["days"] == 30
        assert len(data["series"]) == 1

    @patch("skillhub.routers.analytics.get_time_series")
    def test_time_series_custom_days(self, mock_ts: MagicMock) -> None:
        mock_ts.return_value = []
        db_mock = MagicMock()
        client = _make_client(db_mock)
        resp = client.get(
            "/api/v1/admin/analytics/time-series?days=7", headers=_admin_headers()
        )
        assert resp.status_code == 200
        assert resp.json()["days"] == 7

    def test_funnel_requires_auth(self) -> None:
        client = _make_client()
        resp = client.get("/api/v1/admin/analytics/submission-funnel")
        assert resp.status_code == 401

    @patch("skillhub.routers.analytics.get_submission_funnel")
    def test_funnel_returns_200(self, mock_funnel: MagicMock) -> None:
        mock_funnel.return_value = {
            "submitted": 10,
            "gate1_passed": 8,
            "gate2_passed": 6,
            "approved": 5,
            "published": 4,
            "gate1_rate": 80.0,
            "gate2_rate": 75.0,
            "approval_rate": 83.3,
            "period_days": 30,
        }
        db_mock = MagicMock()
        client = _make_client(db_mock)
        resp = client.get(
            "/api/v1/admin/analytics/submission-funnel", headers=_admin_headers()
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["submitted"] == 10

    def test_top_skills_requires_auth(self) -> None:
        client = _make_client()
        resp = client.get("/api/v1/admin/analytics/top-skills")
        assert resp.status_code == 401

    @patch("skillhub.routers.analytics.get_top_skills")
    def test_top_skills_returns_200(self, mock_top: MagicMock) -> None:
        mock_top.return_value = [
            {"slug": "cool-skill", "name": "Cool", "installs": 100, "rating": 4.5}
        ]
        db_mock = MagicMock()
        client = _make_client(db_mock)
        resp = client.get(
            "/api/v1/admin/analytics/top-skills", headers=_admin_headers()
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["slug"] == "cool-skill"

    def test_top_skills_requires_platform_team(self) -> None:
        client = _make_client()
        resp = client.get(
            "/api/v1/admin/analytics/top-skills", headers=_regular_headers()
        )
        assert resp.status_code == 403
