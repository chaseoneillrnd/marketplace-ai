"""Tier 1 RED tests: every POST endpoint must return 422 on empty body, never 500.

These tests are written to FAIL against the current codebase where bare
Pydantic Model(**request.get_json()) raises unhandled ValidationError → 500.
They drive the fix: a global @app.errorhandler(ValidationError) in app.py.
"""
from __future__ import annotations

import uuid
from typing import Any

import pytest

from tests.conftest import make_token


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_token(**extra: Any) -> str:
    payload = {"sub": "test-user", "user_id": str(uuid.uuid4()), "division": "engineering"}
    payload.update(extra)
    return make_token(payload=payload)


def _platform_token(**extra: Any) -> str:
    payload = {
        "sub": "admin-user",
        "user_id": str(uuid.uuid4()),
        "division": "platform",
        "is_platform_team": True,
    }
    payload.update(extra)
    return make_token(payload=payload)


# ---------------------------------------------------------------------------
# Endpoints accessible by regular authenticated users
# ---------------------------------------------------------------------------

USER_POST_ENDPOINTS = [
    "/api/v1/submissions",
    "/api/v1/feedback",
]

# Endpoints requiring platform_team
PLATFORM_POST_ENDPOINTS = [
    "/api/v1/admin/flags",
    "/api/v1/admin/platform-updates",
]


class TestEmptyBodyReturns422:
    """POST with empty JSON body must return 422, never 500."""

    @pytest.mark.parametrize("endpoint", USER_POST_ENDPOINTS)
    def test_user_endpoint_empty_body_422(self, client: Any, endpoint: str) -> None:
        headers = _auth_headers(_user_token())
        resp = client.post(endpoint, json={}, headers=headers)
        assert resp.status_code != 500, f"{endpoint} returned 500 on empty body"
        assert resp.status_code == 422, f"{endpoint} expected 422, got {resp.status_code}"

    @pytest.mark.parametrize("endpoint", PLATFORM_POST_ENDPOINTS)
    def test_platform_endpoint_empty_body_422(self, client: Any, endpoint: str) -> None:
        headers = _auth_headers(_platform_token())
        resp = client.post(endpoint, json={}, headers=headers)
        assert resp.status_code != 500, f"{endpoint} returned 500 on empty body"
        assert resp.status_code == 422, f"{endpoint} expected 422, got {resp.status_code}"


class TestSubmissionValidation:
    """Specific submission validation edge cases."""

    def test_empty_declared_divisions_returns_422(self, client: Any) -> None:
        """SubmissionCreateRequest.declared_divisions has min_length=1."""
        headers = _auth_headers(_user_token())
        resp = client.post(
            "/api/v1/submissions",
            json={
                "name": "My Skill",
                "short_desc": "A test skill",
                "category": "code-review",
                "content": "# Skill content here",
                "declared_divisions": [],
                "division_justification": "reason",
            },
            headers=headers,
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"

    def test_missing_division_justification_returns_422(self, client: Any) -> None:
        headers = _auth_headers(_user_token())
        resp = client.post(
            "/api/v1/submissions",
            json={
                "name": "My Skill",
                "short_desc": "A test skill",
                "category": "code-review",
                "content": "# content",
                "declared_divisions": ["engineering"],
            },
            headers=headers,
        )
        assert resp.status_code == 422
