"""Tests for analytics blueprint — all routes require platform_team."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tests.conftest import make_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _platform_token() -> str:
    return make_token(
        payload={
            "sub": "admin",
            "user_id": str(uuid4()),
            "division": "eng",
            "is_platform_team": True,
            "is_security_team": False,
        }
    )


def _regular_token() -> str:
    return make_token(
        payload={
            "sub": "user",
            "user_id": str(uuid4()),
            "division": "eng",
            "is_platform_team": False,
            "is_security_team": False,
        }
    )


# ---------------------------------------------------------------------------
# GET /api/v1/admin/analytics/summary
# ---------------------------------------------------------------------------


class TestAnalyticsSummary:
    """GET /admin/analytics/summary — platform team only."""

    def test_summary_401_no_token(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/analytics/summary")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.analytics.get_summary")
    def test_summary_200_platform(self, mock_gs: MagicMock, client: Any) -> None:
        mock_gs.return_value = {
            "dau": 150,
            "new_installs_7d": 320,
            "active_installs": 5000,
            "published_skills": 100,
            "pending_reviews": 12,
            "submission_pass_rate": 0.85,
            "period": "all_time",
        }
        resp = client.get(
            "/api/v1/admin/analytics/summary",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["dau"] == 150
        assert data["published_skills"] == 100
        mock_gs.assert_called_once()

    @patch("skillhub_flask.blueprints.analytics.get_summary")
    def test_summary_with_division_filter(self, mock_gs: MagicMock, client: Any) -> None:
        mock_gs.return_value = {
            "dau": 30,
            "new_installs_7d": 50,
            "active_installs": 1500,
            "published_skills": 30,
            "pending_reviews": 3,
            "submission_pass_rate": 0.9,
            "period": "all_time",
        }
        resp = client.get(
            "/api/v1/admin/analytics/summary?division=eng",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        mock_gs.assert_called_once()
        call_kwargs = mock_gs.call_args
        assert call_kwargs[1]["division"] == "eng"

    def test_summary_403_regular(self, client: Any) -> None:
        resp = client.get(
            "/api/v1/admin/analytics/summary",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/admin/analytics/time-series
# ---------------------------------------------------------------------------


class TestAnalyticsTimeSeries:
    """GET /admin/analytics/time-series — platform team only."""

    def test_time_series_401_no_token(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/analytics/time-series")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.analytics.get_time_series")
    def test_time_series_200_platform(self, mock_ts: MagicMock, client: Any) -> None:
        mock_ts.return_value = [
            {"date": "2026-03-01", "installs": 10, "users": 5, "submissions": 2, "reviews": 1},
            {"date": "2026-03-02", "installs": 15, "users": 8, "submissions": 3, "reviews": 2},
        ]
        resp = client.get(
            "/api/v1/admin/analytics/time-series",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["days"] == 30  # default
        assert len(data["series"]) == 2
        mock_ts.assert_called_once()

    @patch("skillhub_flask.blueprints.analytics.get_time_series")
    def test_time_series_custom_days(self, mock_ts: MagicMock, client: Any) -> None:
        mock_ts.return_value = []
        resp = client.get(
            "/api/v1/admin/analytics/time-series?days=7",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["days"] == 7
        call_kwargs = mock_ts.call_args
        assert call_kwargs[1]["days"] == 7

    def test_time_series_403_regular(self, client: Any) -> None:
        resp = client.get(
            "/api/v1/admin/analytics/time-series",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/admin/analytics/submission-funnel
# ---------------------------------------------------------------------------


class TestAnalyticsFunnel:
    """GET /admin/analytics/submission-funnel — platform team only."""

    def test_funnel_401_no_token(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/analytics/submission-funnel")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.analytics.get_submission_funnel")
    def test_funnel_200_platform(self, mock_sf: MagicMock, client: Any) -> None:
        mock_sf.return_value = {
            "submitted": 100,
            "gate1_passed": 80,
            "gate2_passed": 60,
            "approved": 50,
            "published": 45,
            "gate1_rate": 0.8,
            "gate2_rate": 0.75,
            "approval_rate": 0.83,
            "period_days": 30,
        }
        resp = client.get(
            "/api/v1/admin/analytics/submission-funnel",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["submitted"] == 100
        assert data["approval_rate"] == 0.83
        mock_sf.assert_called_once()

    @patch("skillhub_flask.blueprints.analytics.get_submission_funnel")
    def test_funnel_custom_days(self, mock_sf: MagicMock, client: Any) -> None:
        mock_sf.return_value = {
            "submitted": 20,
            "gate1_passed": 18,
            "gate2_passed": 15,
            "approved": 12,
            "published": 10,
            "gate1_rate": 0.9,
            "gate2_rate": 0.83,
            "approval_rate": 0.8,
            "period_days": 7,
        }
        resp = client.get(
            "/api/v1/admin/analytics/submission-funnel?days=7",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["period_days"] == 7
        call_kwargs = mock_sf.call_args
        assert call_kwargs[1]["days"] == 7

    def test_funnel_403_regular(self, client: Any) -> None:
        resp = client.get(
            "/api/v1/admin/analytics/submission-funnel",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/admin/analytics/top-skills
# ---------------------------------------------------------------------------


class TestAnalyticsTopSkills:
    """GET /admin/analytics/top-skills — platform team only."""

    def test_top_skills_401_no_token(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/analytics/top-skills")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.analytics.get_top_skills")
    def test_top_skills_200_platform(self, mock_top: MagicMock, client: Any) -> None:
        mock_top.return_value = [
            {"slug": "cool-skill", "name": "Cool Skill", "installs": 500, "rating": 4.5},
            {"slug": "nice-skill", "name": "Nice Skill", "installs": 300, "rating": 4.2},
        ]
        resp = client.get(
            "/api/v1/admin/analytics/top-skills",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["items"]) == 2
        assert data["items"][0]["slug"] == "cool-skill"
        mock_top.assert_called_once()

    @patch("skillhub_flask.blueprints.analytics.get_top_skills")
    def test_top_skills_custom_limit(self, mock_top: MagicMock, client: Any) -> None:
        mock_top.return_value = []
        resp = client.get(
            "/api/v1/admin/analytics/top-skills?limit=5",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        call_kwargs = mock_top.call_args
        assert call_kwargs[1]["limit"] == 5

    def test_top_skills_403_regular(self, client: Any) -> None:
        resp = client.get(
            "/api/v1/admin/analytics/top-skills",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403
