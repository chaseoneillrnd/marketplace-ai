"""Tests for Submission pipeline router endpoints."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from tests.conftest import _make_settings, make_token

# Test user IDs
USER_ID = str(uuid.uuid4())
ADMIN_USER_ID = str(uuid.uuid4())

VALID_CONTENT = """---
name: Test Skill
slug: test-skill
version: 1.0.0
category: engineering
trigger_phrases:
- review this PR
- check my code
- analyze this diff
---

# Test Skill

This is the body of the skill.
"""


def _auth_header(
    user_id: str = USER_ID,
    is_platform_team: bool = False,
    division: str = "engineering",
) -> dict[str, str]:
    """Create an auth header with a valid JWT."""
    token = make_token({
        "sub": "test-user",
        "user_id": user_id,
        "division": division,
        "role": "user",
        "is_platform_team": is_platform_team,
        "is_security_team": False,
        "name": "Test User",
    })
    return {"Authorization": f"Bearer {token}"}


def _admin_header() -> dict[str, str]:
    """Create an auth header for a platform team admin."""
    return _auth_header(user_id=ADMIN_USER_ID, is_platform_team=True)


def _make_client(db_mock: MagicMock | None = None) -> TestClient:
    """Create a test client with optional DB mock."""
    settings = _make_settings()
    app = create_app(settings=settings)
    if db_mock is not None:
        app.dependency_overrides[get_db] = lambda: db_mock
    return TestClient(app)


# --- POST /api/v1/submissions ---


class TestCreateSubmission:
    @patch("skillhub.routers.submissions.create_submission")
    def test_valid_returns_201(self, mock_create: MagicMock) -> None:
        sub_id = uuid.uuid4()
        mock_create.return_value = {
            "id": sub_id,
            "display_id": "SKL-ABC123",
            "status": "gate1_passed",
            "gate1_result": {
                "gate": 1,
                "result": "passed",
                "findings": None,
                "score": None,
            },
        }

        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/submissions",
            json={
                "name": "Test Skill",
                "short_desc": "A test skill",
                "category": "engineering",
                "content": VALID_CONTENT,
                "declared_divisions": ["engineering"],
                "division_justification": "Needed for eng team",
            },
            headers=_auth_header(),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["display_id"] == "SKL-ABC123"
        assert data["status"] == "gate1_passed"

    def test_empty_divisions_returns_422(self) -> None:
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/submissions",
            json={
                "name": "Test Skill",
                "short_desc": "A test",
                "category": "eng",
                "content": "content",
                "declared_divisions": [],
                "division_justification": "reason",
            },
            headers=_auth_header(),
        )
        assert response.status_code == 422

    def test_empty_justification_returns_422(self) -> None:
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/submissions",
            json={
                "name": "Test Skill",
                "short_desc": "A test",
                "category": "eng",
                "content": "content",
                "declared_divisions": ["eng"],
                "division_justification": "",
            },
            headers=_auth_header(),
        )
        assert response.status_code == 422

    def test_no_auth_returns_401(self) -> None:
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/submissions",
            json={
                "name": "Test",
                "short_desc": "Test",
                "category": "eng",
                "content": "content",
                "declared_divisions": ["eng"],
                "division_justification": "reason",
            },
        )
        assert response.status_code == 401

    @patch("skillhub.routers.submissions.create_submission")
    def test_display_id_format(self, mock_create: MagicMock) -> None:
        sub_id = uuid.uuid4()
        mock_create.return_value = {
            "id": sub_id,
            "display_id": "SKL-XY9Z1A",
            "status": "gate1_passed",
            "gate1_result": {"gate": 1, "result": "passed", "findings": None, "score": None},
        }

        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/submissions",
            json={
                "name": "Test",
                "short_desc": "Short",
                "category": "eng",
                "content": VALID_CONTENT,
                "declared_divisions": ["eng"],
                "division_justification": "reason",
            },
            headers=_auth_header(),
        )

        assert response.status_code == 201
        did = response.json()["display_id"]
        assert did.startswith("SKL-")
        assert len(did) == 10

    @patch("skillhub.routers.submissions.create_submission")
    def test_gate1_failed_content(self, mock_create: MagicMock) -> None:
        sub_id = uuid.uuid4()
        mock_create.return_value = {
            "id": sub_id,
            "display_id": "SKL-FAIL01",
            "status": "gate1_failed",
            "gate1_result": {
                "gate": 1,
                "result": "failed",
                "findings": [
                    {"severity": "high", "category": "schema", "description": "Missing frontmatter"}
                ],
                "score": None,
            },
        }

        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/submissions",
            json={
                "name": "Bad",
                "short_desc": "Bad skill",
                "category": "eng",
                "content": "no frontmatter",
                "declared_divisions": ["eng"],
                "division_justification": "reason",
            },
            headers=_auth_header(),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "gate1_failed"
        assert data["gate1_result"]["result"] == "failed"


# --- GET /api/v1/submissions/{id} ---


class TestGetSubmission:
    @patch("skillhub.routers.submissions.get_submission")
    def test_owner_can_view(self, mock_get: MagicMock) -> None:
        sub_id = uuid.uuid4()
        mock_get.return_value = {
            "id": sub_id,
            "display_id": "SKL-ABC123",
            "name": "Test",
            "short_desc": "Desc",
            "category": "eng",
            "content": "content",
            "declared_divisions": ["eng"],
            "division_justification": "reason",
            "status": "gate1_passed",
            "submitted_by": uuid.UUID(USER_ID),
            "gate_results": [],
            "created_at": "2026-01-01T00:00:00",
            "updated_at": None,
        }

        client = _make_client(MagicMock())
        response = client.get(
            f"/api/v1/submissions/{sub_id}",
            headers=_auth_header(),
        )

        assert response.status_code == 200

    @patch("skillhub.routers.submissions.get_submission")
    def test_not_found_returns_404(self, mock_get: MagicMock) -> None:
        mock_get.return_value = None
        client = _make_client(MagicMock())
        response = client.get(
            f"/api/v1/submissions/{uuid.uuid4()}",
            headers=_auth_header(),
        )
        assert response.status_code == 404


# --- Admin endpoints ---


class TestAdminEndpoints:
    def test_non_platform_team_returns_403(self) -> None:
        client = _make_client(MagicMock())
        response = client.get(
            "/api/v1/admin/submissions",
            headers=_auth_header(),  # Regular user
        )
        assert response.status_code == 403

    @patch("skillhub.routers.submissions.list_admin_submissions")
    def test_admin_list_submissions(self, mock_list: MagicMock) -> None:
        mock_list.return_value = ([], 0)
        client = _make_client(MagicMock())
        response = client.get(
            "/api/v1/admin/submissions",
            headers=_admin_header(),
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    @patch("skillhub.routers.submissions.review_submission")
    def test_review_approved(self, mock_review: MagicMock) -> None:
        sub_id = uuid.uuid4()
        mock_review.return_value = {
            "id": sub_id,
            "display_id": "SKL-ABC123",
            "status": "approved",
            "decision": "approved",
        }

        client = _make_client(MagicMock())
        response = client.post(
            f"/api/v1/admin/submissions/{sub_id}/review",
            json={"decision": "approved", "notes": "LGTM"},
            headers=_admin_header(),
        )

        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    def test_review_non_admin_returns_403(self) -> None:
        client = _make_client(MagicMock())
        response = client.post(
            f"/api/v1/admin/submissions/{uuid.uuid4()}/review",
            json={"decision": "approved", "notes": "test"},
            headers=_auth_header(),
        )
        assert response.status_code == 403


# --- Gate 2 scan endpoint ---


class TestGate2Scan:
    def test_non_admin_returns_403(self) -> None:
        client = _make_client(MagicMock())
        response = client.post(
            f"/api/v1/admin/submissions/{uuid.uuid4()}/scan",
            headers=_auth_header(),
        )
        assert response.status_code == 403

    @patch("skillhub.services.submissions.run_gate2_scan")
    def test_scan_returns_result(self, mock_scan: MagicMock) -> None:
        sub_id = uuid.uuid4()
        mock_scan.return_value = {
            "submission_id": str(sub_id),
            "gate2_status": "gate2_passed",
            "score": 85,
            "summary": "Skipped — LLM judge disabled",
        }

        client = _make_client(MagicMock())
        response = client.post(
            f"/api/v1/admin/submissions/{sub_id}/scan",
            headers=_admin_header(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["gate2_status"] == "gate2_passed"
        assert data["score"] == 85

    @patch("skillhub.services.submissions.run_gate2_scan")
    def test_scan_not_found_returns_404(self, mock_scan: MagicMock) -> None:
        mock_scan.side_effect = ValueError("Submission not found")
        client = _make_client(MagicMock())
        response = client.post(
            f"/api/v1/admin/submissions/{uuid.uuid4()}/scan",
            headers=_admin_header(),
        )
        assert response.status_code == 404


# --- Access Request endpoints ---


class TestAccessRequests:
    @patch("skillhub.routers.submissions.create_access_request")
    def test_create_access_request(self, mock_create: MagicMock) -> None:
        req_id = uuid.uuid4()
        skill_id = uuid.uuid4()
        mock_create.return_value = {
            "id": req_id,
            "skill_id": skill_id,
            "requested_by": uuid.UUID(USER_ID),
            "user_division": "marketing",
            "reason": "Need access",
            "status": "pending",
            "created_at": "2026-01-01T00:00:00",
        }

        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/skills/test-skill/access-request",
            json={"reason": "Need access"},
            headers=_auth_header(division="marketing"),
        )

        assert response.status_code == 201
        assert response.json()["status"] == "pending"

    @patch("skillhub.routers.submissions.create_access_request")
    def test_already_authorized_returns_400(self, mock_create: MagicMock) -> None:
        mock_create.side_effect = ValueError("User's division already has access to this skill")

        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/skills/test-skill/access-request",
            json={"reason": "I want it"},
            headers=_auth_header(),
        )

        assert response.status_code == 400

    def test_admin_access_requests_non_admin_403(self) -> None:
        client = _make_client(MagicMock())
        response = client.get(
            "/api/v1/admin/access-requests",
            headers=_auth_header(),
        )
        assert response.status_code == 403

    @patch("skillhub.routers.submissions.list_access_requests")
    def test_admin_list_access_requests(self, mock_list: MagicMock) -> None:
        mock_list.return_value = ([], 0)
        client = _make_client(MagicMock())
        response = client.get(
            "/api/v1/admin/access-requests",
            headers=_admin_header(),
        )
        assert response.status_code == 200

    @patch("skillhub.routers.submissions.review_access_request")
    def test_approve_access_request(self, mock_review: MagicMock) -> None:
        req_id = uuid.uuid4()
        mock_review.return_value = {
            "id": req_id,
            "status": "approved",
            "decision": "approved",
        }

        client = _make_client(MagicMock())
        response = client.post(
            f"/api/v1/admin/access-requests/{req_id}/review",
            json={"decision": "approved"},
            headers=_admin_header(),
        )

        assert response.status_code == 200
        assert response.json()["status"] == "approved"
