"""Tests for Submission pipeline service — Gate 1, create, review, access requests."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from skillhub.services.submissions import (
    _generate_display_id,
    _parse_frontmatter,
    _slugify,
    create_access_request,
    create_submission,
    get_submission,
    list_access_requests,
    list_admin_submissions,
    review_access_request,
    review_submission,
    run_gate1,
    run_gate2_scan,
)


# --- Helpers ---

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

MISSING_FRONTMATTER_CONTENT = """# No frontmatter
Just body text.
"""

FEW_TRIGGERS_CONTENT = """---
name: Test Skill
slug: test-skill
version: 1.0.0
category: engineering
trigger_phrases:
- only one trigger
---

Body here.
"""


def _mock_db_session() -> MagicMock:
    """Create a mock DB session."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


# --- display_id tests ---


class TestDisplayId:
    def test_format(self) -> None:
        display_id = _generate_display_id()
        assert display_id.startswith("SKL-")
        assert len(display_id) == 10  # SKL- + 6 chars

    def test_alphanum(self) -> None:
        display_id = _generate_display_id()
        suffix = display_id[4:]
        assert suffix.isalnum()
        assert suffix.isupper() or suffix.isdigit()


# --- slugify tests ---


class TestSlugify:
    def test_basic(self) -> None:
        assert _slugify("PR Review Assistant") == "pr-review-assistant"

    def test_special_chars(self) -> None:
        assert _slugify("My Skill! (v2)") == "my-skill-v2"

    def test_multiple_spaces(self) -> None:
        assert _slugify("  Multiple   Spaces  ") == "multiple-spaces"


# --- frontmatter parsing ---


class TestParseFrontmatter:
    def test_valid_frontmatter(self) -> None:
        fm = _parse_frontmatter(VALID_CONTENT)
        assert fm is not None
        assert fm["name"] == "Test Skill"
        assert fm["slug"] == "test-skill"
        assert fm["version"] == "1.0.0"
        assert len(fm["trigger_phrases"]) == 3

    def test_no_frontmatter(self) -> None:
        fm = _parse_frontmatter(MISSING_FRONTMATTER_CONTENT)
        assert fm is None

    def test_inline_list(self) -> None:
        content = '---\nname: Test\ntrigger_phrases: ["a", "b", "c"]\nslug: t\nversion: 1.0.0\ncategory: eng\n---\n'
        fm = _parse_frontmatter(content)
        assert fm is not None
        assert fm["trigger_phrases"] == ["a", "b", "c"]


# --- Gate 1 ---


class TestGate1:
    def test_missing_frontmatter_fails(self) -> None:
        db = _mock_db_session()
        result, findings = run_gate1(db, MISSING_FRONTMATTER_CONTENT, "Short desc")
        assert result.value == "failed"
        assert any("frontmatter" in f["description"].lower() for f in findings)

    def test_short_desc_over_80_fails(self) -> None:
        db = _mock_db_session()
        long_desc = "x" * 81
        result, findings = run_gate1(db, VALID_CONTENT, long_desc)
        assert result.value == "failed"
        assert any("80 characters" in f["description"] for f in findings)

    def test_fewer_than_3_triggers_fails(self) -> None:
        db = _mock_db_session()
        result, findings = run_gate1(db, FEW_TRIGGERS_CONTENT, "Short desc")
        assert result.value == "failed"
        assert any("trigger phrases" in f["description"].lower() for f in findings)

    def test_valid_submission_passes(self) -> None:
        db = _mock_db_session()
        result, findings = run_gate1(db, VALID_CONTENT, "Short desc")
        assert result.value == "passed"
        assert findings == []

    def test_duplicate_slug_fails(self) -> None:
        db = _mock_db_session()
        # Make slug lookup return an existing skill
        existing_skill = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing_skill
        result, findings = run_gate1(db, VALID_CONTENT, "Short desc")
        assert result.value == "failed"
        assert any("already in use" in f["description"] for f in findings)

    def test_missing_required_fields_fails(self) -> None:
        db = _mock_db_session()
        content = "---\nname: Test\n---\nBody"
        result, findings = run_gate1(db, content, "Short")
        assert result.value == "failed"
        # Should report multiple missing fields
        assert len(findings) >= 1


# --- create_submission ---


class TestCreateSubmission:
    def test_valid_returns_201_data(self) -> None:
        db = _mock_db_session()
        # Ensure flush and commit don't error
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.add = MagicMock()

        user_id = uuid.uuid4()
        result = create_submission(
            db,
            user_id=user_id,
            name="Test Skill",
            short_desc="A test skill",
            category="engineering",
            content=VALID_CONTENT,
            declared_divisions=["engineering"],
            division_justification="Needed for eng team",
        )

        assert result["display_id"].startswith("SKL-")
        assert result["status"] == "gate1_passed"
        assert result["gate1_result"]["gate"] == 1
        assert result["gate1_result"]["result"] == "passed"

    def test_invalid_content_returns_gate1_failed(self) -> None:
        db = _mock_db_session()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.add = MagicMock()

        user_id = uuid.uuid4()
        result = create_submission(
            db,
            user_id=user_id,
            name="Bad Skill",
            short_desc="A" * 81,  # Too long
            category="engineering",
            content=VALID_CONTENT,
            declared_divisions=["engineering"],
            division_justification="Reason",
        )

        assert result["status"] == "gate1_failed"
        assert result["gate1_result"]["result"] == "failed"


# --- get_submission ---


class TestGetSubmission:
    def test_not_found_returns_none(self) -> None:
        db = _mock_db_session()
        result = get_submission(db, uuid.uuid4(), user_id=uuid.uuid4())
        assert result is None

    def test_wrong_user_raises_permission_error(self) -> None:
        db = _mock_db_session()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.submitted_by = uuid.uuid4()
        submission.status.value = "submitted"
        submission.declared_divisions = []
        db.query.return_value.filter.return_value.first.return_value = submission
        with pytest.raises(PermissionError, match="Not authorized"):
            get_submission(db, submission.id, user_id=uuid.uuid4())

    def test_platform_team_can_view_any(self) -> None:
        db = _mock_db_session()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.submitted_by = uuid.uuid4()
        submission.status.value = "gate1_passed"
        submission.declared_divisions = ["eng"]
        submission.created_at = "2026-01-01"
        submission.updated_at = None

        # First query for submission, second for gate results
        db.query.return_value.filter.return_value.first.return_value = submission
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_submission(
            db,
            submission.id,
            user_id=uuid.uuid4(),
            is_platform_team=True,
        )
        assert result is not None


# --- review_submission (Gate 3) ---


class TestReviewSubmission:
    def test_approved_creates_skill(self) -> None:
        db = _mock_db_session()
        db.commit = MagicMock()
        db.flush = MagicMock()
        db.add = MagicMock()

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

        # First call returns submission (lookup), second returns None (slug uniqueness)
        db.query.return_value.filter.return_value.first.side_effect = [
            submission,  # submission lookup
            None,  # slug uniqueness check
        ]

        db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "status", MagicMock(value="approved")))

        result = review_submission(
            db,
            submission.id,
            reviewer_id=uuid.uuid4(),
            decision="approved",
            notes="Looks good",
        )

        assert result["status"] == "approved"
        # Should have called db.add for Skill, SkillVersion, divisions, gate result, audit
        assert db.add.call_count >= 4

    def test_rejected_sets_status(self) -> None:
        db = _mock_db_session()
        db.commit = MagicMock()
        db.add = MagicMock()

        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.display_id = "SKL-XYZ789"
        submission.status = MagicMock(value="gate2_passed")
        db.query.return_value.filter.return_value.first.return_value = submission

        db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "status", MagicMock(value="rejected")))

        result = review_submission(
            db,
            submission.id,
            reviewer_id=uuid.uuid4(),
            decision="rejected",
            notes="Not ready",
        )

        assert result["status"] == "rejected"

    def test_not_found_raises(self) -> None:
        db = _mock_db_session()
        with pytest.raises(ValueError, match="not found"):
            review_submission(
                db,
                uuid.uuid4(),
                reviewer_id=uuid.uuid4(),
                decision="approved",
                notes="test",
            )


# --- Gate 2 scan ---


class TestRunGate2Scan:
    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = _mock_db_session()
        with pytest.raises(ValueError, match="not found"):
            await run_gate2_scan(db, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_disabled_flag_passes(self) -> None:
        db = _mock_db_session()
        db.commit = MagicMock()
        db.add = MagicMock()

        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.submitted_by = uuid.uuid4()

        # First query: Submission lookup, Second: FeatureFlag lookup
        db.query.return_value.filter.return_value.first.side_effect = [
            submission,  # Submission found
            None,  # No feature flag → disabled
        ]

        result = await run_gate2_scan(db, submission.id)
        assert result["gate2_status"] == "gate2_passed"
        assert result["score"] == 0


# --- Access request tests ---


class TestAccessRequests:
    def test_authorized_division_returns_error(self) -> None:
        db = _mock_db_session()
        skill = MagicMock()
        skill.id = uuid.uuid4()

        # Skill found
        db.query.return_value.filter.return_value.first.side_effect = [
            skill,  # skill lookup
            MagicMock(),  # division already authorized
        ]

        with pytest.raises(ValueError, match="already has access"):
            create_access_request(
                db,
                skill_slug="test",
                user_id=uuid.uuid4(),
                user_division="engineering",
                reason="Need access",
            )

    def test_skill_not_found_raises(self) -> None:
        db = _mock_db_session()
        with pytest.raises(ValueError, match="not found"):
            create_access_request(
                db,
                skill_slug="nonexistent",
                user_id=uuid.uuid4(),
                user_division="marketing",
                reason="Need it",
            )

    def test_approved_access_adds_division(self) -> None:
        db = _mock_db_session()
        db.commit = MagicMock()
        db.add = MagicMock()

        access_req = MagicMock()
        access_req.id = uuid.uuid4()
        access_req.skill_id = uuid.uuid4()
        access_req.user_division = "marketing"
        db.query.return_value.filter.return_value.first.return_value = access_req

        db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "status", MagicMock(value="approved")))

        result = review_access_request(db, access_req.id, reviewer_id=uuid.uuid4(), decision="approved")
        assert result["status"] == "approved"
        # Should add SkillDivision
        assert db.add.called
