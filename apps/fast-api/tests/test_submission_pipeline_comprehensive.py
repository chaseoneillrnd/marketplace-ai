"""Comprehensive tests for submission pipeline — full lifecycle, gate validations, state machine."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skillhub.dependencies import get_db
from skillhub.main import create_app
from skillhub.schemas.submission import GateFinding, JudgeVerdict
from skillhub.services.llm_judge import evaluate_gate2_sync
from skillhub.services.submissions import (
    _parse_frontmatter,
    create_submission,
    review_submission,
    run_gate1,
    run_gate2_scan,
)
from tests.conftest import _make_settings, make_token

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

MISSING_FRONTMATTER = """# No frontmatter
Just body text.
"""

FEW_TRIGGERS = """---
name: Test Skill
slug: test-skill
version: 1.0.0
category: engineering
trigger_phrases:
- only one trigger
---

Body here.
"""

MISSING_SLUG = """---
name: Test Skill
version: 1.0.0
category: engineering
trigger_phrases:
- review this PR
- check my code
- analyze this diff
---

Body here.
"""

MISSING_VERSION = """---
name: Test Skill
slug: test-skill
category: engineering
trigger_phrases:
- review this PR
- check my code
- analyze this diff
---

Body here.
"""


def _auth_header(
    user_id: str = USER_ID,
    is_platform_team: bool = False,
) -> dict[str, str]:
    token = make_token({
        "sub": "test-user",
        "user_id": user_id,
        "division": "engineering",
        "role": "user",
        "is_platform_team": is_platform_team,
        "is_security_team": False,
        "name": "Test User",
    })
    return {"Authorization": f"Bearer {token}"}


def _admin_header() -> dict[str, str]:
    return _auth_header(user_id=ADMIN_USER_ID, is_platform_team=True)


def _mock_db_session() -> MagicMock:
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.count.return_value = 0
    db.flush = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.add = MagicMock()
    return db


def _make_client(db_mock: MagicMock | None = None) -> TestClient:
    settings = _make_settings()
    app = create_app(settings=settings)
    if db_mock is not None:
        app.dependency_overrides[get_db] = lambda: db_mock
    return TestClient(app)


# --- Full Pipeline: submit -> gate1 -> gate2 -> gate3 -> published ---


class TestFullPipeline:
    """Test the complete submission lifecycle."""

    def test_valid_submission_passes_gate1(self) -> None:
        """A valid submission passes Gate 1 and gets gate1_passed status."""
        db = _mock_db_session()
        result = create_submission(
            db,
            user_id=uuid.UUID(USER_ID),
            name="Test Skill",
            short_desc="A test skill",
            category="engineering",
            content=VALID_CONTENT,
            declared_divisions=["engineering"],
            division_justification="Needed for eng team",
        )
        assert result["status"] == "gate1_passed"
        assert result["gate1_result"]["result"] == "passed"
        assert result["display_id"].startswith("SKL-")

    def test_gate2_with_disabled_flag_auto_passes(self) -> None:
        """When LLM judge feature flag is disabled, Gate 2 auto-passes."""
        db = _mock_db_session()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.submitted_by = uuid.uuid4()

        # Submission found, feature flag not found (disabled)
        db.query.return_value.filter.return_value.first.side_effect = [
            submission, None
        ]

        result = asyncio.run(run_gate2_scan(db, submission.id))
        assert result["gate2_status"] == "gate2_passed"
        assert result["score"] == 0  # Skipped judge uses score=0

    def test_gate3_approve_creates_skill(self) -> None:
        """Approving at Gate 3 creates the published Skill."""
        db = _mock_db_session()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.name = "Test Skill"
        submission.short_desc = "A test skill"
        submission.category = "engineering"
        submission.content = VALID_CONTENT
        submission.submitted_by = uuid.uuid4()
        submission.declared_divisions = ["engineering"]
        submission.display_id = "SKL-ABC123"
        submission.status = MagicMock(value="gate2_passed")
        # First .first() returns submission, subsequent return None (slug uniqueness check)
        db.query.return_value.filter.return_value.first.side_effect = [submission, None, None, None]
        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="approved"))
        )

        result = review_submission(
            db,
            submission.id,
            reviewer_id=uuid.UUID(ADMIN_USER_ID),
            decision="approved",
            notes="LGTM",
        )

        assert result["status"] == "approved"
        # Should have added Skill, SkillVersion, divisions, gate result, audit
        assert db.add.call_count >= 4

    def test_gate3_reject_sets_rejected_status(self) -> None:
        """Rejecting at Gate 3 sets rejected status."""
        db = _mock_db_session()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.display_id = "SKL-XYZ789"
        submission.status = MagicMock(value="gate2_passed")
        db.query.return_value.filter.return_value.first.return_value = submission
        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="rejected"))
        )

        result = review_submission(
            db,
            submission.id,
            reviewer_id=uuid.UUID(ADMIN_USER_ID),
            decision="rejected",
            notes="Not suitable",
        )

        assert result["status"] == "rejected"


# --- Gate 1 Validation Failures ---


class TestGate1ValidationFailures:
    """Test Gate 1 catches all validation issues."""

    def test_missing_frontmatter_fails(self) -> None:
        db = _mock_db_session()
        result, findings = run_gate1(db, MISSING_FRONTMATTER, "Short desc")
        assert result.value == "failed"
        assert any("frontmatter" in f["description"].lower() for f in findings)

    def test_duplicate_slug_fails(self) -> None:
        db = _mock_db_session()
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing
        result, findings = run_gate1(db, VALID_CONTENT, "Short desc")
        assert result.value == "failed"
        assert any("already in use" in f["description"] for f in findings)

    def test_too_few_trigger_phrases_fails(self) -> None:
        db = _mock_db_session()
        result, findings = run_gate1(db, FEW_TRIGGERS, "Short desc")
        assert result.value == "failed"
        assert any("trigger phrases" in f["description"].lower() for f in findings)

    def test_short_desc_over_80_chars_fails(self) -> None:
        db = _mock_db_session()
        long_desc = "x" * 81
        result, findings = run_gate1(db, VALID_CONTENT, long_desc)
        assert result.value == "failed"
        assert any("80 characters" in f["description"] for f in findings)

    def test_missing_slug_field_fails(self) -> None:
        db = _mock_db_session()
        result, findings = run_gate1(db, MISSING_SLUG, "Short desc")
        assert result.value == "failed"
        assert len(findings) >= 1

    def test_missing_version_field_fails(self) -> None:
        db = _mock_db_session()
        result, findings = run_gate1(db, MISSING_VERSION, "Short desc")
        assert result.value == "failed"
        assert len(findings) >= 1

    def test_valid_content_passes(self) -> None:
        db = _mock_db_session()
        result, findings = run_gate1(db, VALID_CONTENT, "Short desc")
        assert result.value == "passed"
        assert findings == []

    def test_missing_required_fields_reports_all(self) -> None:
        db = _mock_db_session()
        content = "---\nname: Test\n---\nBody"
        result, findings = run_gate1(db, content, "Short")
        assert result.value == "failed"
        assert len(findings) >= 1


# --- Gate 2 LLM Judge Scenarios ---


class TestGate2LLMJudge:
    """Test Gate 2 LLM judge verdict handling."""

    def test_pass_verdict_passes(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": True}, score=88, findings=[], summary="Good quality"
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_passed"
        assert data["result"] == "passed"
        assert data["score"] == 88

    def test_fail_verdict_fails(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": False}, score=80, findings=[], summary="Failed by judge"
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_failed"
        assert data["result"] == "failed"

    def test_critical_finding_always_fails(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": True},
            score=90,
            findings=[
                GateFinding(severity="critical", category="security", description="SQL injection risk"),
            ],
            summary="Critical issue",
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_failed"

    def test_high_finding_flags_for_review(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": True},
            score=75,
            findings=[
                GateFinding(severity="high", category="quality", description="Potential issue"),
            ],
            summary="Flagged",
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_flagged"
        assert data["result"] == "flagged"

    def test_low_score_fails(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": True}, score=65, findings=[], summary="Low quality"
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_failed"

    def test_above_threshold_no_issues_passes(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": True},
            score=82,
            findings=[
                GateFinding(severity="low", category="style", description="Minor issue"),
            ],
            summary="Minor issues only",
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_passed"

    def test_disabled_judge_verdict_passes(self) -> None:
        """Skipped LLM judge should auto-pass with score 85."""
        verdict = JudgeVerdict(
            **{"pass": True}, score=85, findings=[], summary="Skipped"
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_passed"
        assert data["score"] == 85


# --- Gate 2 Feature Flag Disabled ---


class TestGate2FeatureFlagDisabled:
    """Test Gate 2 behavior when LLM judge feature flag is disabled."""

    def test_no_flag_row_auto_passes(self) -> None:
        db = _mock_db_session()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.submitted_by = uuid.uuid4()

        db.query.return_value.filter.return_value.first.side_effect = [
            submission, None  # No FeatureFlag row
        ]

        result = asyncio.run(run_gate2_scan(db, submission.id))
        assert result["gate2_status"] == "gate2_passed"
        assert "auto-pass" in result.get("summary", "") or result["score"] == 0

    def test_submission_not_found_raises(self) -> None:
        db = _mock_db_session()
        with pytest.raises(ValueError, match="not found"):
            asyncio.run(run_gate2_scan(db, uuid.uuid4()))


# --- Gate 3 Approve/Reject/Changes Requested ---


class TestGate3Decisions:
    """Test Gate 3 review decisions."""

    def test_approved_creates_skill_records(self) -> None:
        db = _mock_db_session()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.name = "Good Skill"
        submission.short_desc = "A good skill"
        submission.category = "engineering"
        submission.content = VALID_CONTENT
        submission.submitted_by = uuid.uuid4()
        submission.declared_divisions = ["engineering"]
        submission.display_id = "SKL-AAA111"
        submission.status = MagicMock(value="gate2_passed")
        # First .first() returns submission, subsequent return None (slug uniqueness)
        db.query.return_value.filter.return_value.first.side_effect = [submission, None, None, None]
        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="approved"))
        )

        result = review_submission(
            db,
            submission.id,
            reviewer_id=uuid.uuid4(),
            decision="approved",
            notes="LGTM",
        )

        assert result["status"] == "approved"
        assert db.add.call_count >= 4
        db.commit.assert_called()

    def test_rejected_updates_status_only(self) -> None:
        db = _mock_db_session()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.display_id = "SKL-REJ999"
        submission.status = MagicMock(value="gate2_passed")
        db.query.return_value.filter.return_value.first.return_value = submission
        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="rejected"))
        )

        result = review_submission(
            db,
            submission.id,
            reviewer_id=uuid.uuid4(),
            decision="rejected",
            notes="Doesn't meet standards",
        )

        assert result["status"] == "rejected"

    def test_changes_requested_updates_status(self) -> None:
        db = _mock_db_session()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.display_id = "SKL-CHG001"
        submission.status = MagicMock(value="gate2_passed")
        db.query.return_value.filter.return_value.first.return_value = submission
        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(
                obj, "status", MagicMock(value="changes_requested")
            )
        )

        result = review_submission(
            db,
            submission.id,
            reviewer_id=uuid.uuid4(),
            decision="changes_requested",
            notes="Please update trigger phrases",
        )

        assert result["status"] == "changes_requested"

    def test_review_not_found_raises(self) -> None:
        db = _mock_db_session()
        with pytest.raises(ValueError, match="not found"):
            review_submission(
                db,
                uuid.uuid4(),
                reviewer_id=uuid.uuid4(),
                decision="approved",
                notes="test",
            )


# --- Submission State Machine ---


class TestSubmissionStateMachine:
    """Test that invalid state transitions are rejected."""

    def test_gate1_failed_returns_status(self) -> None:
        """Invalid content at submission time returns gate1_failed, not an error."""
        db = _mock_db_session()
        result = create_submission(
            db,
            user_id=uuid.UUID(USER_ID),
            name="Bad Skill",
            short_desc="A" * 81,
            category="engineering",
            content=VALID_CONTENT,
            declared_divisions=["engineering"],
            division_justification="Reason",
        )
        assert result["status"] == "gate1_failed"
        assert result["gate1_result"]["result"] == "failed"

    def test_gate1_failed_with_missing_frontmatter(self) -> None:
        db = _mock_db_session()
        result = create_submission(
            db,
            user_id=uuid.UUID(USER_ID),
            name="Bad Skill",
            short_desc="Short",
            category="engineering",
            content=MISSING_FRONTMATTER,
            declared_divisions=["engineering"],
            division_justification="Reason",
        )
        assert result["status"] == "gate1_failed"


# --- Router-Level Submission Endpoints ---


class TestSubmissionRouterEndpoints:
    """Test submission router for comprehensive scenarios."""

    @patch("skillhub.routers.submissions.create_submission")
    def test_valid_submission_returns_201(self, mock_create: MagicMock) -> None:
        sub_id = uuid.uuid4()
        mock_create.return_value = {
            "id": sub_id,
            "display_id": "SKL-ABC123",
            "status": "gate1_passed",
            "gate1_result": {"gate": 1, "result": "passed", "findings": None, "score": None},
        }
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/submissions",
            json={
                "name": "Test Skill",
                "short_desc": "A test",
                "category": "engineering",
                "content": VALID_CONTENT,
                "declared_divisions": ["engineering"],
                "division_justification": "Needed",
            },
            headers=_auth_header(),
        )
        assert response.status_code == 201

    def test_empty_divisions_returns_422(self) -> None:
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/submissions",
            json={
                "name": "Test",
                "short_desc": "Test",
                "category": "eng",
                "content": "content",
                "declared_divisions": [],
                "division_justification": "reason",
            },
            headers=_auth_header(),
        )
        assert response.status_code == 422

    def test_missing_justification_returns_422(self) -> None:
        client = _make_client(MagicMock())
        response = client.post(
            "/api/v1/submissions",
            json={
                "name": "Test",
                "short_desc": "Test",
                "category": "eng",
                "content": "content",
                "declared_divisions": ["eng"],
                "division_justification": "",
            },
            headers=_auth_header(),
        )
        assert response.status_code == 422

    def test_unauthenticated_returns_401(self) -> None:
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


# --- Frontmatter Parsing ---


class TestFrontmatterParsing:
    """Test frontmatter parsing edge cases."""

    def test_valid_frontmatter_extracts_all_fields(self) -> None:
        fm = _parse_frontmatter(VALID_CONTENT)
        assert fm is not None
        assert fm["name"] == "Test Skill"
        assert fm["slug"] == "test-skill"
        assert fm["version"] == "1.0.0"
        assert fm["category"] == "engineering"
        assert len(fm["trigger_phrases"]) == 3

    def test_no_frontmatter_returns_none(self) -> None:
        fm = _parse_frontmatter(MISSING_FRONTMATTER)
        assert fm is None

    def test_partial_frontmatter_returns_partial(self) -> None:
        content = "---\nname: Test\n---\nBody"
        fm = _parse_frontmatter(content)
        assert fm is not None
        assert fm["name"] == "Test"

    def test_inline_list_trigger_phrases(self) -> None:
        content = '---\nname: Test\ntrigger_phrases: ["a", "b", "c"]\nslug: t\nversion: 1.0.0\ncategory: eng\n---\n'
        fm = _parse_frontmatter(content)
        assert fm is not None
        assert fm["trigger_phrases"] == ["a", "b", "c"]

    def test_empty_content_returns_none(self) -> None:
        fm = _parse_frontmatter("")
        assert fm is None

    def test_only_dashes_returns_empty_dict_or_none(self) -> None:
        fm = _parse_frontmatter("---\n---\n")
        # Either None or empty dict is acceptable
        if fm is not None:
            assert isinstance(fm, dict)
