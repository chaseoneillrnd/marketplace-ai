"""Tests for Platform domain models: FeatureFlag, AuditLog."""

import uuid

from sqlalchemy.orm import Session

from skillhub_db.models.audit import AuditLog
from skillhub_db.models.flags import FeatureFlag


class TestFeatureFlag:
    def test_feature_flag_key_is_pk(self, db: Session):
        flag = FeatureFlag(
            key="test_flag",
            enabled=True,
            description="A test flag",
        )
        db.add(flag)
        db.commit()
        assert db.get(FeatureFlag, "test_flag") is not None

    def test_feature_flag_division_overrides_json(self, db: Session):
        flag = FeatureFlag(
            key="div_flag",
            enabled=False,
            division_overrides={"engineering-org": True},
        )
        db.add(flag)
        db.commit()
        db.refresh(flag)
        assert flag.division_overrides["engineering-org"] is True


class TestAuditLog:
    def test_audit_log_creates(self, db: Session):
        log = AuditLog(
            event_type="skill.installed",
            actor_id=uuid.uuid4(),
            target_type="skill",
            target_id="some-skill-id",
            metadata_={"method": "mcp"},
        )
        db.add(log)
        db.commit()
        assert log.id is not None
        assert log.event_type == "skill.installed"

    def test_audit_log_repr(self):
        log = AuditLog(event_type="test.event")
        assert repr(log) == "<AuditLog 'test.event'>"
