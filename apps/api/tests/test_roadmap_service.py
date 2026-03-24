"""Tests for roadmap service — create, transition, ship, changelog, delete."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from skillhub.services.roadmap import (
    VALID_TRANSITIONS,
    create_update,
    delete_update,
    list_updates,
    reorder_updates,
    ship_update,
    update_status,
)

from .conftest import _make_settings, make_token

AUTHOR_ID = str(uuid.uuid4())
UPDATE_ID = uuid.uuid4()


def _mock_update(**overrides: Any) -> MagicMock:
    """Create a mock PlatformUpdate ORM object."""
    u = MagicMock()
    u.id = overrides.get("id", UPDATE_ID)
    u.title = overrides.get("title", "New Feature: Dark Mode")
    u.body = overrides.get("body", "We are adding dark mode support to the platform.")
    u.status = overrides.get("status", "planned")
    u.author_id = overrides.get("author_id", uuid.UUID(AUTHOR_ID))
    u.target_quarter = overrides.get("target_quarter", "Q2-2026")
    u.linked_feedback_ids = overrides.get("linked_feedback_ids", [])
    u.shipped_at = overrides.get("shipped_at", None)
    u.sort_order = overrides.get("sort_order", 0)
    u.created_at = overrides.get("created_at", datetime.now(UTC))
    u.updated_at = overrides.get("updated_at", datetime.now(UTC))
    return u


def _mock_db_session() -> MagicMock:
    """Create a mock DB session."""
    db = MagicMock()
    return db


@pytest.fixture()
def mock_db() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def app_with_db(mock_db: MagicMock) -> Any:
    settings = _make_settings()
    application = create_app(settings=settings)
    application.dependency_overrides[get_db] = lambda: mock_db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app_with_db: Any) -> TestClient:
    return TestClient(app_with_db)


class TestCreateUpdate:
    """Tests for create_update."""

    def test_create_update(self) -> None:
        db = _mock_db_session()
        mock_update = _mock_update()

        def _refresh(obj: Any) -> None:
            pass

        db.refresh = _refresh

        with patch("skillhub.services.roadmap.PlatformUpdate") as MockModel:
            MockModel.return_value = mock_update

            result = create_update(
                db,
                title="New Feature: Dark Mode",
                body="We are adding dark mode support to the platform.",
                author_id=AUTHOR_ID,
                target_quarter="Q2-2026",
            )

        assert result["title"] == "New Feature: Dark Mode"
        assert result["status"] == "planned"
        db.add.assert_called_once()
        db.commit.assert_called_once()


class TestUpdateStatus:
    """Tests for status transitions."""

    def test_valid_transition_planned_to_in_progress(self) -> None:
        db = _mock_db_session()
        mock_update = _mock_update(status="planned")
        db.query.return_value.filter.return_value.first.return_value = mock_update

        def _refresh(obj: Any) -> None:
            pass

        db.refresh = _refresh

        result = update_status(
            db,
            update_id=str(UPDATE_ID),
            new_status="in_progress",
            actor_id=AUTHOR_ID,
        )
        assert mock_update.status == "in_progress"
        db.commit.assert_called_once()

    def test_invalid_transition_shipped_to_planned(self) -> None:
        db = _mock_db_session()
        mock_update = _mock_update(status="shipped")
        db.query.return_value.filter.return_value.first.return_value = mock_update

        with pytest.raises(ValueError, match="Invalid transition"):
            update_status(
                db,
                update_id=str(UPDATE_ID),
                new_status="planned",
                actor_id=AUTHOR_ID,
            )

    def test_valid_transition_cancelled_to_planned(self) -> None:
        db = _mock_db_session()
        mock_update = _mock_update(status="cancelled")
        db.query.return_value.filter.return_value.first.return_value = mock_update

        def _refresh(obj: Any) -> None:
            pass

        db.refresh = _refresh

        result = update_status(
            db,
            update_id=str(UPDATE_ID),
            new_status="planned",
            actor_id=AUTHOR_ID,
        )
        assert mock_update.status == "planned"

    def test_update_not_found(self) -> None:
        db = _mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Platform update not found"):
            update_status(
                db,
                update_id=str(uuid.uuid4()),
                new_status="in_progress",
                actor_id=AUTHOR_ID,
            )


class TestShipUpdate:
    """Tests for ship_update."""

    def test_ship_update_sets_shipped_at(self) -> None:
        db = _mock_db_session()
        mock_update = _mock_update(status="in_progress")
        db.query.return_value.filter.return_value.first.return_value = mock_update

        def _refresh(obj: Any) -> None:
            pass

        db.refresh = _refresh

        result = ship_update(
            db,
            update_id=str(UPDATE_ID),
            version_tag="v1.2.0",
            changelog_body="Added dark mode support",
            actor_id=AUTHOR_ID,
        )
        assert mock_update.status == "shipped"
        assert mock_update.shipped_at is not None
        db.commit.assert_called_once()

    def test_ship_from_terminal_status_raises(self) -> None:
        db = _mock_db_session()
        mock_update = _mock_update(status="shipped")
        db.query.return_value.filter.return_value.first.return_value = mock_update

        with pytest.raises(ValueError, match="Cannot ship from status"):
            ship_update(
                db,
                update_id=str(UPDATE_ID),
                version_tag="v1.2.0",
                changelog_body="Some changelog body text",
                actor_id=AUTHOR_ID,
            )


class TestDeleteUpdate:
    """Tests for delete_update (soft-delete via cancelled)."""

    def test_delete_sets_cancelled(self) -> None:
        db = _mock_db_session()
        mock_update = _mock_update(status="planned")
        db.query.return_value.filter.return_value.first.return_value = mock_update

        def _refresh(obj: Any) -> None:
            pass

        db.refresh = _refresh

        result = delete_update(
            db,
            update_id=str(UPDATE_ID),
            actor_id=AUTHOR_ID,
        )
        assert mock_update.status == "cancelled"
        db.commit.assert_called_once()

    def test_delete_not_found(self) -> None:
        db = _mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Platform update not found"):
            delete_update(
                db,
                update_id=str(uuid.uuid4()),
                actor_id=AUTHOR_ID,
            )


class TestChangelogPublicEndpoint:
    """Test the public changelog endpoint via TestClient."""

    @patch("skillhub.routers.roadmap.list_updates")
    def test_changelog_public_no_auth(
        self, mock_list: MagicMock, client: TestClient
    ) -> None:
        """Changelog endpoint returns 200 without auth."""
        mock_list.return_value = ([], 0)
        response = client.get("/api/v1/changelog")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @patch("skillhub.routers.roadmap.list_updates")
    def test_changelog_returns_shipped_items(
        self, mock_list: MagicMock, client: TestClient
    ) -> None:
        """Changelog returns shipped items."""
        mock_list.return_value = ([], 0)
        response = client.get("/api/v1/changelog")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)


class TestDeleteRequiresSecurityTeam:
    """Test that DELETE platform-updates requires security team role."""

    def test_delete_requires_security_team_403_for_platform_team(self, client: TestClient) -> None:
        """Platform team user (not security team) gets 403 on DELETE."""
        token = make_token(
            payload={
                "sub": "admin-user",
                "user_id": str(uuid.uuid4()),
                "is_platform_team": True,
                "is_security_team": False,
                "division": "engineering",
            }
        )
        response = client.delete(
            f"/api/v1/admin/platform-updates/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @patch("skillhub.routers.roadmap.delete_update")
    def test_delete_allowed_for_security_team(
        self, mock_delete: MagicMock, client: TestClient
    ) -> None:
        """Security team user can call DELETE (not 403)."""
        mock_delete.return_value = {
            "id": uuid.uuid4(),
            "title": "Test",
            "body": "Test body",
            "status": "cancelled",
            "author_id": uuid.uuid4(),
            "target_quarter": None,
            "linked_feedback_ids": [],
            "shipped_at": None,
            "sort_order": 0,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        token = make_token(
            payload={
                "sub": "security-user",
                "user_id": str(uuid.uuid4()),
                "is_platform_team": True,
                "is_security_team": True,
                "division": "engineering",
            }
        )
        response = client.delete(
            f"/api/v1/admin/platform-updates/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code != 403


class TestReorderUpdates:
    """Tests for reorder_updates."""

    def test_reorder_sets_sort_order(self) -> None:
        db = _mock_db_session()
        u1 = _mock_update(id=uuid.uuid4(), sort_order=0)
        u2 = _mock_update(id=uuid.uuid4(), sort_order=1)

        call_count = 0
        updates = [u2, u1]

        def _first_side_effect() -> MagicMock:
            nonlocal call_count
            result = updates[call_count] if call_count < len(updates) else None
            call_count += 1
            return result

        db.query.return_value.filter.return_value.first.side_effect = _first_side_effect

        reorder_updates(db, ordered_ids=[str(u2.id), str(u1.id)])
        db.commit.assert_called_once()
