"""Tests for the POST /api/v1/skills/<slug>/versions endpoint."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import make_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_token(user_id: str | None = None, **extra: Any) -> str:
    payload = {
        "sub": "test-user",
        "user_id": user_id or str(uuid.uuid4()),
        "division": "engineering",
    }
    payload.update(extra)
    return make_token(payload=payload)


_VERSION_BODY = {
    "content": "# Updated SKILL.md\nNew content here",
    "changelog": "Fixed critical bug in prompt",
    "declared_divisions": ["engineering"],
    "division_justification": "Engineers use this daily",
}


class TestCreateVersionEndpoint:
    """POST /api/v1/skills/<slug>/versions."""

    @patch("skillhub_flask.blueprints.skills.version_submission")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_success_returns_201(
        self, mock_get_db: MagicMock, mock_version: MagicMock, client: Any
    ) -> None:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock skill lookup
        mock_skill = MagicMock()
        mock_skill.id = uuid.uuid4()
        mock_skill.slug = "my-skill"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_skill

        mock_version.return_value = {
            "id": str(uuid.uuid4()),
            "display_id": "SKL-XYZ789",
            "status": "submitted",
            "target_skill_id": str(mock_skill.id),
        }

        token = _user_token()
        resp = client.post(
            "/api/v1/skills/my-skill/versions",
            json=_VERSION_BODY,
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "submitted"
        mock_version.assert_called_once()

    def test_no_auth_returns_401(self, client: Any) -> None:
        resp = client.post("/api/v1/skills/my-skill/versions", json=_VERSION_BODY)
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.skills.version_submission")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_not_author_returns_403(
        self, mock_get_db: MagicMock, mock_version: MagicMock, client: Any
    ) -> None:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_skill = MagicMock()
        mock_skill.id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_skill

        mock_version.side_effect = PermissionError("Only the skill author can submit new versions")

        token = _user_token()
        resp = client.post(
            "/api/v1/skills/my-skill/versions",
            json=_VERSION_BODY,
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert "author" in data["detail"].lower()

    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_skill_not_found_returns_404(
        self, mock_get_db: MagicMock, client: Any
    ) -> None:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        token = _user_token()
        resp = client.post(
            "/api/v1/skills/nonexistent-skill/versions",
            json=_VERSION_BODY,
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404
