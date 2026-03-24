"""Tests that flag CRUD operations write AuditLog entries."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from tests.conftest import make_token


def _platform_team_headers() -> dict[str, str]:
    token = make_token(payload={
        "sub": "admin-user",
        "user_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "division": "platform",
        "is_platform_team": True,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Service-layer tests: verify AuditLog creation
# ---------------------------------------------------------------------------

class TestCreateFlagAudit:
    """create_flag should add an AuditLog entry after creating the flag."""

    def test_audit_log_written_on_create(self) -> None:
        from skillhub.services.flags import create_flag

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        actor = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        create_flag(db, "test.flag", enabled=True, description="A test", actor_id=actor)

        # db.add is called twice: once for the flag, once for the audit log
        assert db.add.call_count == 2
        audit_obj = db.add.call_args_list[1][0][0]
        assert audit_obj.event_type == "flag.created"
        assert audit_obj.actor_id == actor
        assert audit_obj.target_type == "feature_flag"
        assert audit_obj.target_id == "test.flag"
        assert "after" in audit_obj.metadata_

    def test_audit_log_commit_called(self) -> None:
        from skillhub.services.flags import create_flag

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        create_flag(db, "test.flag", enabled=True)

        # Two commits: one for the flag, one for the audit
        assert db.commit.call_count == 2


class TestUpdateFlagAudit:
    """update_flag should add an AuditLog entry with before/after state."""

    def test_audit_log_written_on_update(self) -> None:
        from skillhub.services.flags import update_flag

        mock_flag = MagicMock()
        mock_flag.key = "test.flag"
        mock_flag.enabled = True
        mock_flag.description = "Original"
        mock_flag.division_overrides = None

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_flag

        actor = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        update_flag(db, "test.flag", enabled=False, actor_id=actor)

        # db.add called once for the audit log (flag update is in-place)
        assert db.add.call_count == 1
        audit_obj = db.add.call_args_list[0][0][0]
        assert audit_obj.event_type == "flag.updated"
        assert audit_obj.actor_id == actor
        assert audit_obj.target_id == "test.flag"
        assert "before" in audit_obj.metadata_
        assert "after" in audit_obj.metadata_


class TestDeleteFlagAudit:
    """delete_flag should add an AuditLog entry with before state."""

    def test_audit_log_written_on_delete(self) -> None:
        from skillhub.services.flags import delete_flag

        mock_flag = MagicMock()
        mock_flag.key = "test.flag"
        mock_flag.enabled = True
        mock_flag.description = "To delete"
        mock_flag.division_overrides = None

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_flag

        actor = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        delete_flag(db, "test.flag", actor_id=actor)

        # db.add called once for the audit log
        assert db.add.call_count == 1
        audit_obj = db.add.call_args_list[0][0][0]
        assert audit_obj.event_type == "flag.deleted"
        assert audit_obj.actor_id == actor
        assert audit_obj.target_id == "test.flag"
        assert "before" in audit_obj.metadata_

    def test_audit_log_commit_after_delete(self) -> None:
        from skillhub.services.flags import delete_flag

        mock_flag = MagicMock()
        mock_flag.key = "test.flag"
        mock_flag.enabled = False
        mock_flag.description = None
        mock_flag.division_overrides = None

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_flag

        delete_flag(db, "test.flag")

        # Two commits: one for the delete, one for the audit
        assert db.commit.call_count == 2


# ---------------------------------------------------------------------------
# Blueprint-layer tests: verify actor_id is passed through
# ---------------------------------------------------------------------------

class TestBlueprintPassesActorId:
    """Admin flag endpoints should extract user_id from JWT and pass as actor_id."""

    @patch("skillhub_flask.blueprints.flags.create_flag")
    def test_create_passes_actor_id(self, mock_create: MagicMock, client: Any) -> None:
        mock_create.return_value = {
            "key": "new_flag",
            "enabled": True,
            "description": None,
            "division_overrides": None,
        }

        resp = client.post(
            "/api/v1/admin/flags",
            json={"key": "new_flag", "enabled": True},
            headers=_platform_team_headers(),
        )
        assert resp.status_code == 201

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["actor_id"] == UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    @patch("skillhub_flask.blueprints.flags.update_flag")
    def test_update_passes_actor_id(self, mock_update: MagicMock, client: Any) -> None:
        mock_update.return_value = {
            "key": "existing_flag",
            "enabled": False,
            "description": None,
            "division_overrides": None,
        }

        resp = client.patch(
            "/api/v1/admin/flags/existing_flag",
            json={"enabled": False},
            headers=_platform_team_headers(),
        )
        assert resp.status_code == 200

        call_kwargs = mock_update.call_args[1]
        assert call_kwargs["actor_id"] == UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    @patch("skillhub_flask.blueprints.flags.delete_flag")
    def test_delete_passes_actor_id(self, mock_delete: MagicMock, client: Any) -> None:
        resp = client.delete(
            "/api/v1/admin/flags/old_flag",
            headers=_platform_team_headers(),
        )
        assert resp.status_code == 204

        call_kwargs = mock_delete.call_args[1]
        assert call_kwargs["actor_id"] == UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
