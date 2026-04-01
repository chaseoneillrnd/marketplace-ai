"""Tests for exports blueprint — verifies bug fixes for body, status, and download_url."""

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
# POST /api/v1/admin/exports
# ---------------------------------------------------------------------------


class TestCreateExport:
    """POST /admin/exports — bug fixes: JSON body, status='pending'."""

    @patch("skillhub_flask.blueprints.exports.get_export_status")
    @patch("skillhub_flask.blueprints.exports.run_export_sync")
    @patch("skillhub_flask.blueprints.exports.request_export")
    def test_create_export_accepts_json_body(self, mock_re: MagicMock, mock_sync: MagicMock, mock_status: MagicMock, client: Any) -> None:
        """Bug #1: endpoint accepts JSON body (not query params)."""
        job_id = str(uuid4())
        mock_re.return_value = {
            "id": job_id,
            "status": "queued",
            "scope": "installs",
            "format": "csv",
        }
        mock_status.return_value = {
            "id": job_id,
            "status": "done",
            "scope": "installs",
            "format": "csv",
            "download_url": f"/exports/{job_id}.csv",
        }
        resp = client.post(
            "/api/v1/admin/exports",
            json={"scope": "installs", "format": "csv"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["id"] == job_id
        mock_re.assert_called_once()

    @patch("skillhub_flask.blueprints.exports.get_export_status")
    @patch("skillhub_flask.blueprints.exports.run_export_sync")
    @patch("skillhub_flask.blueprints.exports.request_export")
    def test_create_export_status_pending_not_queued(self, mock_re: MagicMock, mock_sync: MagicMock, mock_status: MagicMock, client: Any) -> None:
        """Bug #3: response status is 'pending', not 'queued'."""
        job_id = str(uuid4())
        mock_re.return_value = {
            "id": job_id,
            "status": "queued",
            "scope": "installs",
            "format": "csv",
        }
        # Simulate sync export failing to complete — status stays queued
        mock_status.return_value = None
        resp = client.post(
            "/api/v1/admin/exports",
            json={"scope": "installs", "format": "csv"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "pending"
        assert data["status"] != "queued"

    @patch("skillhub_flask.blueprints.exports.get_export_status")
    @patch("skillhub_flask.blueprints.exports.run_export_sync")
    @patch("skillhub_flask.blueprints.exports.request_export")
    def test_create_export_with_dates(self, mock_re: MagicMock, mock_sync: MagicMock, mock_status: MagicMock, client: Any) -> None:
        """JSON body can include optional start_date and end_date."""
        job_id = str(uuid4())
        mock_re.return_value = {
            "id": job_id,
            "status": "pending",
            "scope": "installs",
            "format": "csv",
        }
        mock_status.return_value = {
            "id": job_id,
            "status": "done",
            "scope": "installs",
            "format": "csv",
        }
        resp = client.post(
            "/api/v1/admin/exports",
            json={
                "scope": "installs",
                "format": "csv",
                "start_date": "2026-01-01",
                "end_date": "2026-03-01",
            },
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 201

    def test_create_export_403_regular(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/admin/exports",
            json={"scope": "installs", "format": "csv"},
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403

    def test_create_export_401_no_token(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/admin/exports",
            json={"scope": "installs", "format": "csv"},
        )
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.exports.request_export")
    def test_create_export_rate_limit_429(self, mock_re: MagicMock, client: Any) -> None:
        """ValueError from service layer maps to 429."""
        mock_re.side_effect = ValueError("Rate limit exceeded")
        resp = client.post(
            "/api/v1/admin/exports",
            json={"scope": "installs", "format": "csv"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 429


# ---------------------------------------------------------------------------
# GET /api/v1/admin/exports/<job_id>
# ---------------------------------------------------------------------------


class TestExportStatus:
    """GET /admin/exports/<id> — bug fixes: download_url, status='pending'."""

    @patch("skillhub_flask.blueprints.exports.get_export_status")
    def test_export_status_download_url_not_file_path(self, mock_gs: MagicMock, client: Any) -> None:
        """Bug #2: response has 'download_url' not 'file_path'."""
        job_id = str(uuid4())
        mock_gs.return_value = {
            "id": job_id,
            "status": "completed",
            "file_path": "/exports/data.csv",  # service returns file_path
        }
        resp = client.get(
            f"/api/v1/admin/exports/{job_id}",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "download_url" in data
        assert "file_path" not in data
        assert data["download_url"] == "/exports/data.csv"

    @patch("skillhub_flask.blueprints.exports.get_export_status")
    def test_export_status_pending_not_queued(self, mock_gs: MagicMock, client: Any) -> None:
        """Bug #3: status 'queued' is normalized to 'pending'."""
        job_id = str(uuid4())
        mock_gs.return_value = {
            "id": job_id,
            "status": "queued",
        }
        resp = client.get(
            f"/api/v1/admin/exports/{job_id}",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "pending"

    @patch("skillhub_flask.blueprints.exports.get_export_status")
    def test_export_status_404_not_found(self, mock_gs: MagicMock, client: Any) -> None:
        mock_gs.return_value = None
        job_id = str(uuid4())
        resp = client.get(
            f"/api/v1/admin/exports/{job_id}",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 404

    def test_export_status_403_regular(self, client: Any) -> None:
        job_id = str(uuid4())
        resp = client.get(
            f"/api/v1/admin/exports/{job_id}",
            headers=_auth_headers(_regular_token()),
        )
        assert resp.status_code == 403
