"""Tests for version_submission service function."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from skillhub.services.submissions import version_submission


def _make_skill(author_id: uuid.UUID, **overrides: Any) -> MagicMock:
    """Create a mock Skill ORM object."""
    skill = MagicMock()
    skill.id = overrides.get("id", uuid.uuid4())
    skill.name = overrides.get("name", "Test Skill")
    skill.short_desc = overrides.get("short_desc", "A test skill")
    skill.category = overrides.get("category", "code-review")
    skill.author_id = author_id
    skill.slug = overrides.get("slug", "test-skill")
    return skill


def _make_submission_mock() -> MagicMock:
    """Create a mock Submission returned after refresh."""
    sub = MagicMock()
    sub.id = uuid.uuid4()
    sub.display_id = "SKL-ABC123"
    sub.name = "Test Skill"
    sub.short_desc = "A test skill"
    sub.category = "code-review"
    sub.content = "# Updated content"
    sub.declared_divisions = ["engineering"]
    sub.division_justification = "Useful for engineers"
    sub.status = MagicMock(value="submitted")
    sub.submitted_by = uuid.uuid4()
    sub.target_skill_id = uuid.uuid4()
    sub.content_hash = "abc123"
    sub.created_at = datetime.now(timezone.utc)
    sub.updated_at = datetime.now(timezone.utc)
    return sub


class TestVersionSubmission:
    """Tests for version_submission service function."""

    def test_success_creates_submission_with_target_skill_id(self) -> None:
        """version_submission should create a submission linked to the target skill."""
        author_id = uuid.uuid4()
        skill = _make_skill(author_id)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = skill

        # After commit+refresh, the submission object is the one we added
        mock_sub = _make_submission_mock()
        mock_sub.submitted_by = author_id
        mock_sub.target_skill_id = skill.id

        def _refresh(obj: Any) -> None:
            # Copy attributes from mock_sub to the actual submission
            for attr in ("id", "display_id", "name", "short_desc", "category",
                         "content", "declared_divisions", "division_justification",
                         "status", "submitted_by", "target_skill_id", "content_hash",
                         "created_at", "updated_at"):
                setattr(obj, attr, getattr(mock_sub, attr))

        db.refresh.side_effect = _refresh

        result = version_submission(
            db,
            skill_id=skill.id,
            user_id=author_id,
            content="# Updated SKILL.md",
            changelog="Fixed a bug",
            declared_divisions=["engineering"],
            division_justification="Useful for engineers",
        )

        assert result["target_skill_id"] == skill.id
        assert result["status"] == "submitted"
        db.add.assert_called()
        db.commit.assert_called_once()

    def test_not_author_raises_permission_error(self) -> None:
        """version_submission should raise PermissionError for non-authors."""
        author_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        skill = _make_skill(author_id)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = skill

        with pytest.raises(PermissionError, match="Only the skill author"):
            version_submission(
                db,
                skill_id=skill.id,
                user_id=other_user_id,
                content="# New content",
                changelog="Updated",
                declared_divisions=["engineering"],
                division_justification="Reason",
            )

    def test_skill_not_found_raises_value_error(self) -> None:
        """version_submission should raise ValueError when skill does not exist."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Skill not found"):
            version_submission(
                db,
                skill_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                content="# Content",
                changelog="Changelog",
                declared_divisions=["engineering"],
                division_justification="Reason",
            )

    def test_creates_submission_with_correct_fields(self) -> None:
        """version_submission should populate name/category from the skill."""
        author_id = uuid.uuid4()
        skill = _make_skill(author_id, name="My Cool Skill", category="testing")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = skill

        captured_submissions: list[Any] = []

        def _capture_add(obj: Any) -> None:
            captured_submissions.append(obj)

        db.add.side_effect = _capture_add

        mock_sub = _make_submission_mock()
        mock_sub.name = "My Cool Skill"
        mock_sub.category = "testing"
        mock_sub.target_skill_id = skill.id
        db.refresh.side_effect = lambda obj: [
            setattr(obj, attr, getattr(mock_sub, attr))
            for attr in ("id", "display_id", "name", "short_desc", "category",
                         "content", "declared_divisions", "division_justification",
                         "status", "submitted_by", "target_skill_id", "content_hash",
                         "created_at", "updated_at")
        ]

        version_submission(
            db,
            skill_id=skill.id,
            user_id=author_id,
            content="# New content",
            changelog="Version bump",
            declared_divisions=["engineering"],
            division_justification="For engineers",
        )

        # The first add call should be the Submission (before AuditLog)
        from skillhub_db.models.submission import Submission
        subs = [s for s in captured_submissions if isinstance(s, Submission)]
        assert len(subs) == 1
        sub = subs[0]
        assert sub.name == "My Cool Skill"
        assert sub.category == "testing"
        assert sub.target_skill_id == skill.id
