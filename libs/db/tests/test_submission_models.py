"""Tests for Submission domain models."""

from sqlalchemy.orm import Session

from skillhub_db.models.submission import (
    AccessRequestStatus,
    DivisionAccessRequest,
    GateResult,
    Submission,
    SubmissionGateResult,
    SubmissionStatus,
)


class TestSubmission:
    def test_submission_status_defaults_to_submitted(self, db: Session, user):
        s = Submission(
            display_id="SKL-ABC123",
            submitted_by=user.id,
            name="Test Skill",
            short_desc="A test",
            category="engineering",
            content="# Test Skill",
            declared_divisions=["engineering-org"],
            division_justification="For engineering use",
        )
        db.add(s)
        db.commit()
        assert s.status == SubmissionStatus.SUBMITTED

    def test_submission_declared_divisions_json(self, db: Session, user):
        s = Submission(
            display_id="SKL-XYZ789",
            submitted_by=user.id,
            name="Test",
            short_desc="Test",
            category="engineering",
            content="content",
            declared_divisions=["engineering-org", "product-org"],
            division_justification="Multi-division",
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        assert len(s.declared_divisions) == 2


class TestSubmissionGateResult:
    def test_gate_result(self, db: Session, user):
        sub = Submission(
            display_id="SKL-GATE01",
            submitted_by=user.id,
            name="Gate Test",
            short_desc="Test",
            category="engineering",
            content="content",
            declared_divisions=["engineering-org"],
            division_justification="Test",
        )
        db.add(sub)
        db.commit()

        result = SubmissionGateResult(
            submission_id=sub.id,
            gate=1,
            result=GateResult.PASSED,
            findings={"issues": []},
            score=100,
        )
        db.add(result)
        db.commit()
        assert result.gate == 1
        assert result.result == GateResult.PASSED


class TestDivisionAccessRequest:
    def test_access_request_default_pending(self, db: Session, skill, user):
        req = DivisionAccessRequest(
            skill_id=skill.id,
            requested_by=user.id,
            user_division="product-org",
            reason="Need for product work",
        )
        db.add(req)
        db.commit()
        assert req.status == AccessRequestStatus.PENDING
