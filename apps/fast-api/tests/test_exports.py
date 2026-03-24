"""Tests for export service and router."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from tests.conftest import _make_settings, make_token


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


def _make_export_job(**overrides: Any) -> MagicMock:
    defaults = {
        "id": uuid.uuid4(),
        "requested_by": uuid.uuid4(),
        "scope": "installs",
        "format": "csv",
        "filters": {},
        "status": "queued",
        "row_count": None,
        "file_path": None,
        "error": None,
        "created_at": datetime.now(UTC),
        "completed_at": None,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


class TestExportService:
    """Tests for the export service functions."""

    def test_request_export_creates_job(self) -> None:
        """request_export creates an ExportJob and returns dict."""
        from skillhub.services.exports import request_export

        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        user_id = uuid.uuid4()

        # Mock the job after commit/refresh
        job_id = uuid.uuid4()

        def fake_refresh(job: Any) -> None:
            job.id = job_id
            job.status = "queued"

        db.refresh.side_effect = fake_refresh

        result = request_export(db, user_id=user_id, scope="installs", format="csv")
        assert result["status"] == "queued"
        assert result["scope"] == "installs"
        assert result["format"] == "csv"
        assert "id" in result
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_rate_limit_enforcement(self) -> None:
        """6th export in 24h raises ValueError."""
        from skillhub.services.exports import request_export

        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 5
        user_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Rate limit exceeded"):
            request_export(db, user_id=user_id, scope="installs")

    def test_get_export_status_not_found(self) -> None:
        """get_export_status returns None for unknown job."""
        from skillhub.services.exports import get_export_status

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_export_status(db, uuid.uuid4())
        assert result is None


# ---------------------------------------------------------------------------
# Router tests
# ---------------------------------------------------------------------------


def _make_client(db_mock: MagicMock | None = None) -> TestClient:
    settings = _make_settings()
    app = create_app(settings=settings)
    if db_mock is not None:
        app.dependency_overrides[get_db] = lambda: db_mock
    return TestClient(app)


class TestExportRouter:
    """Tests for the export router endpoints."""

    def test_create_export_requires_auth(self) -> None:
        """POST /api/v1/admin/exports without token => 401."""
        client = _make_client()
        resp = client.post("/api/v1/admin/exports")
        assert resp.status_code == 401

    def test_create_export_requires_platform_team(self) -> None:
        """POST /api/v1/admin/exports with non-platform user => 403."""
        client = _make_client()
        token = make_token({"user_id": str(uuid.uuid4()), "is_platform_team": False})
        resp = client.post(
            "/api/v1/admin/exports",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @patch("skillhub.routers.exports.request_export")
    def test_create_export_returns_job(self, mock_request: MagicMock) -> None:
        """POST /api/v1/admin/exports with platform user => 200."""
        job_id = str(uuid.uuid4())
        mock_request.return_value = {
            "id": job_id,
            "status": "queued",
            "scope": "installs",
            "format": "csv",
        }
        db_mock = MagicMock()
        client = _make_client(db_mock)
        token = make_token({"user_id": str(uuid.uuid4()), "is_platform_team": True})
        resp = client.post(
            "/api/v1/admin/exports?scope=installs&format=csv",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == job_id
        assert data["status"] == "queued"

    @patch("skillhub.routers.exports.get_export_status")
    def test_export_status_not_found(self, mock_status: MagicMock) -> None:
        """GET /api/v1/admin/exports/{id} for missing job => 404."""
        mock_status.return_value = None
        db_mock = MagicMock()
        client = _make_client(db_mock)
        token = make_token({"user_id": str(uuid.uuid4()), "is_platform_team": True})
        resp = client.get(
            f"/api/v1/admin/exports/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
