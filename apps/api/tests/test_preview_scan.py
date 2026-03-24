"""Tests for the preview-scan endpoint."""

from __future__ import annotations

import uuid
from typing import Any

from tests.conftest import make_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_token(**extra: Any) -> str:
    payload = {"sub": "test-user", "user_id": str(uuid.uuid4()), "division": "engineering"}
    payload.update(extra)
    return make_token(payload=payload)


class TestPreviewScan:
    """Tests for POST /api/v1/submissions/preview-scan."""

    def test_returns_suggestions_with_valid_content(self, client: Any) -> None:
        token = _user_token()
        resp = client.post(
            "/api/v1/submissions/preview-scan",
            json={
                "name": "My Skill",
                "content": "A" * 200,
                "category": "coding",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["category_recommendation"] == "coding"
        assert data["quality_score"] == 20
        assert data["tags_suggested"] == ["productivity", "automation"]
        assert data["issues"] == []

    def test_flags_short_content(self, client: Any) -> None:
        token = _user_token()
        resp = client.post(
            "/api/v1/submissions/preview-scan",
            json={
                "name": "Short",
                "content": "Brief",
                "category": "coding",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert any("short" in issue.lower() for issue in data["issues"])

    def test_flags_missing_name(self, client: Any) -> None:
        token = _user_token()
        resp = client.post(
            "/api/v1/submissions/preview-scan",
            json={
                "content": "A" * 200,
                "category": "coding",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert any("Name is required" in issue for issue in data["issues"])

    def test_defaults_category_when_empty(self, client: Any) -> None:
        token = _user_token()
        resp = client.post(
            "/api/v1/submissions/preview-scan",
            json={
                "name": "My Skill",
                "content": "A" * 200,
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["category_recommendation"] == "engineering"

    def test_returns_401_without_auth(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/submissions/preview-scan",
            json={"name": "Test", "content": "Hello", "category": "coding"},
        )
        assert resp.status_code == 401

    def test_quality_score_capped_at_100(self, client: Any) -> None:
        token = _user_token()
        resp = client.post(
            "/api/v1/submissions/preview-scan",
            json={
                "name": "Big Skill",
                "content": "A" * 2000,
                "category": "coding",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["quality_score"] == 100
