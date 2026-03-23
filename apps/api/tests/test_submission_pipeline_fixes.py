"""Tests for submission pipeline fixes — 6 targeted bug fixes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skillhub.schemas.submission import JudgeVerdict
from skillhub.services.llm_judge import LLMJudgeService, evaluate_gate2_sync
from skillhub.services.submissions import (
    _parse_frontmatter,
    create_submission,
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

SIMILAR_CONTENT = """---
name: Similar Skill
slug: similar-skill
version: 1.0.0
category: engineering
trigger_phrases:
- review this PR
- check my code
- analyze this diff
---

# Similar Skill

Body here.
"""

DIFFERENT_CONTENT = """---
name: Different Skill
slug: different-skill
version: 1.0.0
category: engineering
trigger_phrases:
- deploy to production
- run database migration
- configure kubernetes cluster
---

# Different Skill

Body here.
"""


def _mock_db_session() -> MagicMock:
    """Create a mock DB session."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.count.return_value = 0
    db.query.return_value.all.return_value = []
    return db


# =============================================================================
# Fix #1 — asyncio.run() crash: run_gate2_scan is now async
# =============================================================================


class TestFix1AsyncGate2Scan:
    """run_gate2_scan must be an async function using await instead of asyncio.run()."""

    @pytest.mark.asyncio
    async def test_run_gate2_scan_is_async(self) -> None:
        """run_gate2_scan should be a coroutine function."""
        import asyncio
        assert asyncio.iscoroutinefunction(run_gate2_scan)

    @pytest.mark.asyncio
    async def test_gate2_scan_disabled_flag_works_async(self) -> None:
        """Gate 2 scan should work when called with await (flag disabled)."""
        db = _mock_db_session()
        db.commit = MagicMock()
        db.add = MagicMock()

        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.submitted_by = uuid.uuid4()

        # First query: Submission lookup, Second: FeatureFlag lookup
        db.query.return_value.filter.return_value.first.side_effect = [
            submission,  # Submission found
            None,  # No feature flag -> disabled
        ]

        result = await run_gate2_scan(db, submission.id)
        assert result["gate2_status"] == "gate2_passed"

    @pytest.mark.asyncio
    async def test_gate2_scan_no_asyncio_run(self) -> None:
        """run_gate2_scan must not use asyncio.run() — it should be awaitable directly."""
        import inspect

        # Verify it's a coroutine function (async def), not a regular function
        assert inspect.iscoroutinefunction(run_gate2_scan), (
            "run_gate2_scan should be async (no asyncio.run() inside)"
        )

        # Verify we can call it from within an existing event loop (the key bug)
        # This would fail with RuntimeError if asyncio.run() was used internally
        db = _mock_db_session()
        db.commit = MagicMock()
        db.add = MagicMock()

        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.submitted_by = uuid.uuid4()

        db.query.return_value.filter.return_value.first.side_effect = [
            submission,  # Submission found
            None,  # No feature flag -> disabled
        ]

        # This should work without RuntimeError because we're already in an event loop
        result = await run_gate2_scan(db, submission.id)
        assert "gate2_status" in result

    @pytest.mark.asyncio
    async def test_gate2_scan_not_found_raises(self) -> None:
        """run_gate2_scan should raise ValueError if submission not found."""
        db = _mock_db_session()
        with pytest.raises(ValueError, match="not found"):
            await run_gate2_scan(db, uuid.uuid4())


# =============================================================================
# Fix #3 — published_at never set on approval
# =============================================================================


class TestFix3PublishedAtSetOnApproval:
    """review_submission must set published_at when approving."""

    def test_published_at_set_on_approval(self) -> None:
        """When a submission is approved, the created Skill should have published_at set."""
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
            None,  # slug uniqueness check (no existing skill)
        ]

        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="approved"))
        )

        before = datetime.now(timezone.utc)
        review_submission(
            db,
            submission.id,
            reviewer_id=uuid.uuid4(),
            decision="approved",
            notes="Looks good",
        )
        after = datetime.now(timezone.utc)

        # Find the Skill object that was added to the session
        added_objects = [call.args[0] for call in db.add.call_args_list]
        from skillhub_db.models.skill import Skill

        skills_added = [obj for obj in added_objects if isinstance(obj, Skill)]
        assert len(skills_added) == 1, "Expected exactly one Skill to be added"
        skill = skills_added[0]
        assert skill.published_at is not None, "published_at should be set"
        assert before <= skill.published_at <= after, "published_at should be recent"

    def test_published_at_not_set_on_rejection(self) -> None:
        """When a submission is rejected, no Skill is created (no published_at)."""
        db = _mock_db_session()
        db.commit = MagicMock()
        db.add = MagicMock()

        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.display_id = "SKL-XYZ789"
        submission.status = MagicMock(value="gate2_passed")
        # Only one lookup needed for rejection (submission lookup, no slug check)
        db.query.return_value.filter.return_value.first.return_value = submission

        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="rejected"))
        )

        review_submission(
            db,
            submission.id,
            reviewer_id=uuid.uuid4(),
            decision="rejected",
            notes="Not ready",
        )

        # No Skill object should have been added
        added_objects = [call.args[0] for call in db.add.call_args_list]
        from skillhub_db.models.skill import Skill

        skills_added = [obj for obj in added_objects if isinstance(obj, Skill)]
        assert len(skills_added) == 0


# =============================================================================
# Fix #4 — actor_id=None in audit log for review_access_request
# =============================================================================


class TestFix4ActorIdInAuditLog:
    """review_access_request must pass reviewer_id as actor_id to audit log."""

    def test_reviewer_id_in_audit_log(self) -> None:
        """The audit log should contain the reviewer's ID, not None."""
        db = _mock_db_session()
        db.commit = MagicMock()
        db.add = MagicMock()

        reviewer_id = uuid.uuid4()

        access_req = MagicMock()
        access_req.id = uuid.uuid4()
        access_req.skill_id = uuid.uuid4()
        access_req.user_division = "marketing"
        db.query.return_value.filter.return_value.first.return_value = access_req

        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="approved"))
        )

        result = review_access_request(
            db, access_req.id, reviewer_id=reviewer_id, decision="approved"
        )
        assert result["status"] == "approved"

        # Check audit log entry
        from skillhub_db.models.audit import AuditLog

        added_objects = [call.args[0] for call in db.add.call_args_list]
        audit_entries = [obj for obj in added_objects if isinstance(obj, AuditLog)]
        assert len(audit_entries) == 1, "Expected exactly one audit log entry"
        assert audit_entries[0].actor_id == reviewer_id, "actor_id should be reviewer_id"

    def test_reviewer_id_required(self) -> None:
        """review_access_request should require reviewer_id parameter."""
        import inspect

        sig = inspect.signature(review_access_request)
        assert "reviewer_id" in sig.parameters

    def test_denied_also_records_reviewer(self) -> None:
        """Denied decisions should also record the reviewer."""
        db = _mock_db_session()
        db.commit = MagicMock()
        db.add = MagicMock()

        reviewer_id = uuid.uuid4()

        access_req = MagicMock()
        access_req.id = uuid.uuid4()
        access_req.skill_id = uuid.uuid4()
        access_req.user_division = "marketing"
        db.query.return_value.filter.return_value.first.return_value = access_req

        db.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "status", MagicMock(value="denied"))
        )

        review_access_request(
            db, access_req.id, reviewer_id=reviewer_id, decision="denied"
        )

        from skillhub_db.models.audit import AuditLog

        added_objects = [call.args[0] for call in db.add.call_args_list]
        audit_entries = [obj for obj in added_objects if isinstance(obj, AuditLog)]
        assert len(audit_entries) == 1
        assert audit_entries[0].actor_id == reviewer_id


# =============================================================================
# Fix #11 — No Gate 1->2 auto-trigger
# =============================================================================


class TestFix11Gate1ToGate2AutoTrigger:
    """After Gate 1 passes and llm_judge_enabled is True, Gate 2 should auto-trigger."""

    def test_auto_trigger_when_flag_enabled(self) -> None:
        """Gate 2 should be enqueued when Gate 1 passes and flag is enabled."""
        db = _mock_db_session()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.add = MagicMock()
        # For the TriggerPhrase query in Jaccard check
        db.query.return_value.all.return_value = []

        flag = MagicMock()
        flag.enabled = True

        # After commit, the flag query should return the enabled flag
        # We need to handle multiple query().filter().first() calls:
        # 1. Slug check in run_gate1 -> None (no existing skill)
        # 2. FeatureFlag check after gate1 passes -> flag
        db.query.return_value.filter.return_value.first.side_effect = [
            None,  # slug check
            flag,  # llm_judge_enabled flag
        ]

        background_tasks = MagicMock()
        user_id = uuid.uuid4()

        create_submission(
            db,
            user_id=user_id,
            name="Test Skill",
            short_desc="A test skill",
            category="engineering",
            content=VALID_CONTENT,
            declared_divisions=["engineering"],
            division_justification="Needed",
            background_tasks=background_tasks,
        )

        background_tasks.add_task.assert_called_once()
        call_args = background_tasks.add_task.call_args
        assert call_args[0][0] is run_gate2_scan

    def test_no_auto_trigger_when_flag_disabled(self) -> None:
        """Gate 2 should NOT be enqueued when flag is disabled."""
        db = _mock_db_session()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.add = MagicMock()
        db.query.return_value.all.return_value = []

        flag = MagicMock()
        flag.enabled = False

        db.query.return_value.filter.return_value.first.side_effect = [
            None,  # slug check
            flag,  # llm_judge_enabled flag (disabled)
        ]

        background_tasks = MagicMock()

        create_submission(
            db,
            user_id=uuid.uuid4(),
            name="Test Skill",
            short_desc="A test skill",
            category="engineering",
            content=VALID_CONTENT,
            declared_divisions=["engineering"],
            division_justification="Needed",
            background_tasks=background_tasks,
        )

        background_tasks.add_task.assert_not_called()

    def test_no_auto_trigger_when_gate1_fails(self) -> None:
        """Gate 2 should NOT be enqueued when Gate 1 fails."""
        db = _mock_db_session()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.add = MagicMock()

        background_tasks = MagicMock()

        result = create_submission(
            db,
            user_id=uuid.uuid4(),
            name="Bad Skill",
            short_desc="A" * 81,  # Too long -> gate1 fails
            category="engineering",
            content=VALID_CONTENT,
            declared_divisions=["engineering"],
            division_justification="Needed",
            background_tasks=background_tasks,
        )

        assert result["status"] == "gate1_failed"
        background_tasks.add_task.assert_not_called()

    def test_no_auto_trigger_when_no_background_tasks(self) -> None:
        """Gate 2 should NOT be triggered when background_tasks is None."""
        db = _mock_db_session()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.add = MagicMock()
        db.query.return_value.all.return_value = []

        # This should not raise even without background_tasks
        result = create_submission(
            db,
            user_id=uuid.uuid4(),
            name="Test Skill",
            short_desc="A test skill",
            category="engineering",
            content=VALID_CONTENT,
            declared_divisions=["engineering"],
            division_justification="Needed",
        )

        assert result["status"] == "gate1_passed"


# =============================================================================
# Fix #12 — Jaccard similarity duplicate check
# =============================================================================


class TestFix12JaccardSimilarity:
    """Cosine similarity stub replaced with Jaccard similarity on trigger phrases."""

    def test_similar_triggers_flagged(self) -> None:
        """Submissions with >0.7 Jaccard similarity should be flagged."""
        db = _mock_db_session()

        # Set up existing trigger phrases
        existing_tp1 = MagicMock()
        existing_tp1.skill_id = uuid.uuid4()
        existing_tp1.phrase = "review this PR"

        existing_tp2 = MagicMock()
        existing_tp2.skill_id = existing_tp1.skill_id
        existing_tp2.phrase = "check my code"

        existing_tp3 = MagicMock()
        existing_tp3.skill_id = existing_tp1.skill_id
        existing_tp3.phrase = "analyze this diff"

        db.query.return_value.all.return_value = [existing_tp1, existing_tp2, existing_tp3]

        result, findings = run_gate1(db, SIMILAR_CONTENT, "Short desc")
        assert result.value == "failed"
        assert any("Jaccard" in f["description"] for f in findings)

    def test_different_triggers_pass(self) -> None:
        """Submissions with low Jaccard similarity should pass."""
        db = _mock_db_session()

        existing_tp1 = MagicMock()
        existing_tp1.skill_id = uuid.uuid4()
        existing_tp1.phrase = "review this PR"

        existing_tp2 = MagicMock()
        existing_tp2.skill_id = existing_tp1.skill_id
        existing_tp2.phrase = "check my code"

        existing_tp3 = MagicMock()
        existing_tp3.skill_id = existing_tp1.skill_id
        existing_tp3.phrase = "analyze this diff"

        db.query.return_value.all.return_value = [existing_tp1, existing_tp2, existing_tp3]

        result, findings = run_gate1(db, DIFFERENT_CONTENT, "Short desc")
        assert result.value == "passed"
        assert not any("Jaccard" in f.get("description", "") for f in findings)

    def test_no_existing_skills_passes(self) -> None:
        """When there are no existing trigger phrases, similarity check passes."""
        db = _mock_db_session()
        db.query.return_value.all.return_value = []

        result, findings = run_gate1(db, VALID_CONTENT, "Short desc")
        assert result.value == "passed"

    def test_exact_duplicate_triggers_flagged(self) -> None:
        """Exact duplicate trigger phrases should have Jaccard = 1.0 > 0.7."""
        db = _mock_db_session()

        skill_id = uuid.uuid4()
        phrases = ["review this PR", "check my code", "analyze this diff"]
        existing_tps = []
        for phrase in phrases:
            tp = MagicMock()
            tp.skill_id = skill_id
            tp.phrase = phrase
            existing_tps.append(tp)

        db.query.return_value.all.return_value = existing_tps

        # Submit content with identical trigger phrases
        result, findings = run_gate1(db, VALID_CONTENT, "Short desc")
        assert result.value == "failed"
        similarity_findings = [f for f in findings if "Jaccard" in f["description"]]
        assert len(similarity_findings) == 1


# =============================================================================
# Fix #14 — LLM judge returns fake score=85 when disabled
# =============================================================================


class TestFix14LLMJudgeSkippedResponse:
    """LLM judge should return score=0, skipped=True when disabled."""

    @pytest.mark.asyncio
    async def test_disabled_returns_score_zero(self) -> None:
        """When disabled, score should be 0, not 85."""
        judge = LLMJudgeService(router_url="", enabled=False)
        verdict = await judge.evaluate("some content")
        assert verdict.score == 0
        assert verdict.pass_ is True

    @pytest.mark.asyncio
    async def test_disabled_returns_skipped_true(self) -> None:
        """When disabled, skipped should be True."""
        judge = LLMJudgeService(router_url="", enabled=False)
        verdict = await judge.evaluate("some content")
        assert verdict.skipped is True

    @pytest.mark.asyncio
    async def test_disabled_clear_message(self) -> None:
        """When disabled, summary should indicate auto-pass."""
        judge = LLMJudgeService(router_url="", enabled=False)
        verdict = await judge.evaluate("some content")
        assert "auto-pass" in verdict.summary.lower() or "disabled" in verdict.summary.lower()

    @pytest.mark.asyncio
    async def test_disabled_no_router_url(self) -> None:
        """When router_url is empty, should return skipped verdict."""
        judge = LLMJudgeService(router_url="", enabled=True)
        verdict = await judge.evaluate("some content")
        assert verdict.skipped is True
        assert verdict.score == 0

    def test_skipped_field_on_verdict_schema(self) -> None:
        """JudgeVerdict should have a skipped field defaulting to False."""
        verdict = JudgeVerdict(**{"pass": True}, score=90, findings=[], summary="Real eval")
        assert verdict.skipped is False

    def test_skipped_field_true_on_verdict(self) -> None:
        """JudgeVerdict with skipped=True should serialize correctly."""
        verdict = JudgeVerdict(
            **{"pass": True}, score=0, findings=[], summary="Skipped", skipped=True
        )
        assert verdict.skipped is True
        assert verdict.score == 0

    @pytest.mark.asyncio
    async def test_gate2_scan_disabled_returns_score_zero(self) -> None:
        """Gate 2 scan with disabled flag should return score=0 (not 85)."""
        db = _mock_db_session()
        db.commit = MagicMock()
        db.add = MagicMock()

        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.submitted_by = uuid.uuid4()

        db.query.return_value.filter.return_value.first.side_effect = [
            submission,  # Submission found
            None,  # No feature flag -> disabled
        ]

        result = await run_gate2_scan(db, submission.id)
        # score should be 0 now, not the old fake 85
        assert result["score"] == 0
        assert result["gate2_status"] == "gate2_passed"
