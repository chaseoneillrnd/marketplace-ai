"""Tests for the feature flags endpoint."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from tests.conftest import _make_settings, make_token


def _make_flag(key: str, enabled: bool, division_overrides: dict | None = None) -> MagicMock:
    """Create a mock FeatureFlag object."""
    flag = MagicMock()
    flag.key = key
    flag.enabled = enabled
    flag.description = f"Description for {key}"
    flag.division_overrides = division_overrides
    return flag


class TestListFlags:
    """GET /api/v1/flags tests."""

    def _create_client(self, mock_db: MagicMock) -> TestClient:
        """Create a test client with mocked DB."""
        settings = _make_settings()
        application = create_app(settings=settings)
        application.dependency_overrides[get_db] = lambda: mock_db
        return TestClient(application)

    def test_returns_flags_unauthenticated(self) -> None:
        """Unauthenticated request returns all flags with default values."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_a", True),
            _make_flag("feature_b", False),
        ]
        client = self._create_client(mock_db)

        response = client.get("/api/v1/flags")
        assert response.status_code == 200
        data = response.json()
        assert data["flags"]["feature_a"] is True
        assert data["flags"]["feature_b"] is False

    def test_returns_flags_with_division_override(self) -> None:
        """Authenticated request applies division override."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_a", False, division_overrides={"engineering": True}),
        ]
        client = self._create_client(mock_db)

        token = make_token(
            {
                "sub": "test-user",
                "division": "engineering",
                "exp": 9999999999,
            }
        )
        response = client.get(
            "/api/v1/flags",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Flag is globally disabled but enabled for engineering division
        assert data["flags"]["feature_a"] is True

    def test_disabled_flag_returns_false(self) -> None:
        """Disabled flag returns false when no override applies."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [
            _make_flag("feature_a", False, division_overrides={"sales": True}),
        ]
        client = self._create_client(mock_db)

        token = make_token(
            {
                "sub": "test-user",
                "division": "engineering",
                "exp": 9999999999,
            }
        )
        response = client.get(
            "/api/v1/flags",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # engineering is not in overrides, so flag stays disabled
        assert data["flags"]["feature_a"] is False

    def test_no_flags_returns_empty(self) -> None:
        """Empty flags table returns empty dict."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []
        client = self._create_client(mock_db)

        response = client.get("/api/v1/flags")
        assert response.status_code == 200
        data = response.json()
        assert data["flags"] == {}
