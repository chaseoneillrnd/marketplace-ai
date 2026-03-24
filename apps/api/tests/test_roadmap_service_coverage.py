"""Coverage tests for skillhub.services.roadmap — CRUD and status transitions."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from skillhub.services.roadmap import (
    VALID_TRANSITIONS,
    create_update,
    delete_update,
    list_updates,
    reorder_updates,
    ship_update,
    update_status,
)


def _mock_platform_update(status: str = "planned") -> MagicMock:
    u = MagicMock()
    u.id = uuid.uuid4()
    u.title = "Add dark mode"
    u.body = "We will add dark mode"
    u.status = status
    u.author_id = uuid.uuid4()
    u.target_quarter = "Q1 2026"
    u.linked_feedback_ids = []
    u.shipped_at = None
    u.sort_order = 0
    u.created_at = None
    u.updated_at = None
    return u


class TestCreateUpdate:
    def test_create_success(self) -> None:
        author_id = uuid.uuid4()
        update_obj = _mock_platform_update()

        db = MagicMock()

        with __import__("unittest.mock", fromlist=["patch"]).patch(
            "skillhub.services.roadmap.PlatformUpdate"
        ) as MockPU:
            MockPU.return_value = update_obj
            result = create_update(
                db,
                title="Add dark mode",
                body="We will add dark mode",
                author_id=str(author_id),
                status="planned",
                target_quarter="Q1 2026",
            )

        db.add.assert_called_once_with(update_obj)
        db.commit.assert_called_once()
        assert result["title"] == "Add dark mode"
        assert result["status"] == "planned"


class TestListUpdates:
    def test_list_all_updates(self) -> None:
        u1 = _mock_platform_update("planned")
        u2 = _mock_platform_update("in_progress")

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 2
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = [u1, u2]
        db.query.return_value = q

        items, total = list_updates(db)

        assert total == 2
        assert len(items) == 2

    def test_list_with_status_filter(self) -> None:
        u1 = _mock_platform_update("shipped")

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 1
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = [u1]
        db.query.return_value = q

        items, total = list_updates(db, status="shipped")
        assert total == 1
        assert items[0]["status"] == "shipped"


class TestUpdateStatus:
    def test_valid_transition_planned_to_in_progress(self) -> None:
        u = _mock_platform_update("planned")
        actor_id = uuid.uuid4()

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = u

        result = update_status(db, update_id=str(u.id), new_status="in_progress", actor_id=str(actor_id))

        assert u.status == "in_progress"
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_valid_transition_planned_to_cancelled(self) -> None:
        u = _mock_platform_update("planned")
        actor_id = uuid.uuid4()

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = u

        result = update_status(db, update_id=str(u.id), new_status="cancelled", actor_id=str(actor_id))
        assert u.status == "cancelled"

    def test_invalid_transition_raises(self) -> None:
        u = _mock_platform_update("shipped")  # terminal state
        actor_id = uuid.uuid4()

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = u

        with pytest.raises(ValueError, match="Invalid transition"):
            update_status(db, update_id=str(u.id), new_status="planned", actor_id=str(actor_id))

    def test_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Platform update not found"):
            update_status(db, update_id=str(uuid.uuid4()), new_status="in_progress", actor_id=str(uuid.uuid4()))

    def test_cancelled_can_reopen_to_planned(self) -> None:
        u = _mock_platform_update("cancelled")
        actor_id = uuid.uuid4()

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = u

        result = update_status(db, update_id=str(u.id), new_status="planned", actor_id=str(actor_id))
        assert u.status == "planned"


class TestShipUpdate:
    def test_ship_from_in_progress(self) -> None:
        u = _mock_platform_update("in_progress")
        u.linked_feedback_ids = []
        actor_id = uuid.uuid4()

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = u

        result = ship_update(
            db,
            update_id=str(u.id),
            version_tag="v1.2.0",
            changelog_body="Added dark mode",
            actor_id=str(actor_id),
        )

        assert u.status == "shipped"
        assert u.shipped_at is not None
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_ship_from_planned(self) -> None:
        u = _mock_platform_update("planned")
        u.linked_feedback_ids = []
        actor_id = uuid.uuid4()

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = u

        result = ship_update(
            db,
            update_id=str(u.id),
            version_tag="v1.1.0",
            changelog_body="Bug fixes",
            actor_id=str(actor_id),
        )

        assert u.status == "shipped"

    def test_ship_wrong_status_raises(self) -> None:
        u = _mock_platform_update("shipped")  # already shipped

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = u

        with pytest.raises(ValueError, match="Cannot ship from status"):
            ship_update(db, update_id=str(u.id), version_tag="v2.0.0", changelog_body="stuff", actor_id=str(uuid.uuid4()))

    def test_ship_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Platform update not found"):
            ship_update(db, update_id=str(uuid.uuid4()), version_tag="v1.0.0", changelog_body="x", actor_id=str(uuid.uuid4()))

    def test_ship_resolves_linked_feedback(self) -> None:
        u = _mock_platform_update("in_progress")
        fid = uuid.uuid4()
        u.linked_feedback_ids = [str(fid)]
        actor_id = uuid.uuid4()

        fb = MagicMock()
        fb.status = "open"

        db = MagicMock()
        q_update = MagicMock()
        q_update.filter.return_value = q_update
        q_update.first.side_effect = [u, fb]

        q_audit = MagicMock()

        db.query.return_value = q_update

        result = ship_update(
            db,
            update_id=str(u.id),
            version_tag="v2.0.0",
            changelog_body="Ships linked feedback",
            actor_id=str(actor_id),
        )

        assert fb.status == "archived"


class TestReorderUpdates:
    def test_reorder_sets_sort_order(self) -> None:
        u1 = _mock_platform_update()
        u2 = _mock_platform_update()
        uid1 = uuid.uuid4()
        uid2 = uuid.uuid4()
        u1.id = uid1
        u2.id = uid2

        call_count = 0

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.side_effect = [u1, u2]
        db.query.return_value = q

        reorder_updates(db, ordered_ids=[str(uid1), str(uid2)])

        assert u1.sort_order == 0
        assert u2.sort_order == 1
        db.commit.assert_called_once()

    def test_reorder_skips_missing_updates(self) -> None:
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        # Should not raise even if updates not found
        reorder_updates(db, ordered_ids=[str(uuid.uuid4())])
        db.commit.assert_called_once()


class TestDeleteUpdate:
    def test_soft_delete_sets_cancelled(self) -> None:
        u = _mock_platform_update("in_progress")
        actor_id = uuid.uuid4()

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = u

        result = delete_update(db, update_id=str(u.id), actor_id=str(actor_id))

        assert u.status == "cancelled"
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_not_found_raises(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Platform update not found"):
            delete_update(db, update_id=str(uuid.uuid4()), actor_id=str(uuid.uuid4()))
