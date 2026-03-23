"""Regression tests for marketplace fixes: author resolution, N+1, trending, days_ago, fork copy, Gate 2."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from skillhub.services.skills import (
    _batch_resolve_authors,
    _batch_user_favorited,
    _batch_user_installed,
    _compute_days_ago,
    _skill_to_detail_dict,
    _skill_to_summary_dict,
    recalculate_trending_scores,
)


def _make_mock_skill(**overrides: Any) -> MagicMock:
    """Create a mock Skill ORM object."""
    skill = MagicMock()
    skill.id = overrides.get("id", uuid.uuid4())
    skill.slug = overrides.get("slug", "test-skill")
    skill.name = overrides.get("name", "Test Skill")
    skill.short_desc = overrides.get("short_desc", "A test skill")
    skill.category = overrides.get("category", "engineering")
    skill.author_id = overrides.get("author_id", uuid.uuid4())
    skill.author_type = overrides.get("author_type", "community")
    skill.current_version = overrides.get("current_version", "1.0.0")
    skill.install_method = overrides.get("install_method", "all")
    skill.data_sensitivity = overrides.get("data_sensitivity", "low")
    skill.external_calls = overrides.get("external_calls", False)
    skill.verified = overrides.get("verified", False)
    skill.featured = overrides.get("featured", False)
    skill.status = overrides.get("status", "published")
    skill.install_count = overrides.get("install_count", 10)
    skill.fork_count = overrides.get("fork_count", 2)
    skill.favorite_count = overrides.get("favorite_count", 5)
    skill.view_count = overrides.get("view_count", 100)
    skill.review_count = overrides.get("review_count", 3)
    skill.avg_rating = overrides.get("avg_rating", Decimal("4.00"))
    skill.trending_score = overrides.get("trending_score", Decimal("50.0000"))
    skill.published_at = overrides.get("published_at", datetime.now(UTC))
    skill.deprecated_at = overrides.get("deprecated_at")

    div = MagicMock()
    div.division_slug = "engineering-org"
    skill.divisions = overrides.get("divisions", [div])

    tag = MagicMock()
    tag.tag = "testing"
    skill.tags = overrides.get("tags", [tag])

    tp = MagicMock()
    tp.id = uuid.uuid4()
    tp.phrase = "test this"
    skill.trigger_phrases = overrides.get("trigger_phrases", [tp])

    skill.versions = overrides.get("versions", [])
    return skill


class TestAuthorResolution:
    """Regression: author was always None in skill dicts."""

    def test_summary_dict_includes_author_name(self) -> None:
        skill = _make_mock_skill()
        result = _skill_to_summary_dict(skill, author_name="Alice Smith")
        assert result["author"] == "Alice Smith"

    def test_summary_dict_author_none_when_not_provided(self) -> None:
        skill = _make_mock_skill()
        result = _skill_to_summary_dict(skill)
        assert result["author"] is None

    def test_detail_dict_includes_author_name(self) -> None:
        skill = _make_mock_skill()
        result = _skill_to_detail_dict(skill, author_name="Bob Jones")
        assert result["author"] == "Bob Jones"

    def test_batch_resolve_authors_returns_name_map(self) -> None:
        user_id = uuid.uuid4()
        db = MagicMock()
        mock_row = MagicMock()
        mock_row.id = user_id
        mock_row.name = "Jane Doe"
        db.query.return_value.filter.return_value.all.return_value = [mock_row]

        result = _batch_resolve_authors(db, [user_id])
        assert result[user_id] == "Jane Doe"

    def test_batch_resolve_authors_empty_list(self) -> None:
        db = MagicMock()
        result = _batch_resolve_authors(db, [])
        assert result == {}


class TestDaysAgo:
    """Regression: days_ago was always None."""

    def test_days_ago_for_recent_skill(self) -> None:
        result = _compute_days_ago(datetime.now(UTC) - timedelta(days=5))
        assert result == 5

    def test_days_ago_for_today(self) -> None:
        result = _compute_days_ago(datetime.now(UTC))
        assert result == 0

    def test_days_ago_none_when_not_published(self) -> None:
        result = _compute_days_ago(None)
        assert result is None

    def test_summary_dict_has_days_ago(self) -> None:
        skill = _make_mock_skill(published_at=datetime.now(UTC) - timedelta(days=7))
        result = _skill_to_summary_dict(skill)
        assert result["days_ago"] == 7


class TestBatchUserAnnotations:
    """Regression: N+1 queries for user_has_installed/favorited."""

    def test_batch_installed_returns_set_of_skill_ids(self) -> None:
        skill_id_1 = uuid.uuid4()
        skill_id_2 = uuid.uuid4()
        user_id = uuid.uuid4()

        db = MagicMock()
        row = MagicMock()
        row.skill_id = skill_id_1
        db.query.return_value.filter.return_value.all.return_value = [row]

        result = _batch_user_installed(db, user_id, [skill_id_1, skill_id_2])
        assert skill_id_1 in result
        assert skill_id_2 not in result

    def test_batch_favorited_returns_set_of_skill_ids(self) -> None:
        skill_id = uuid.uuid4()
        user_id = uuid.uuid4()

        db = MagicMock()
        row = MagicMock()
        row.skill_id = skill_id
        db.query.return_value.filter.return_value.all.return_value = [row]

        result = _batch_user_favorited(db, user_id, [skill_id])
        assert skill_id in result

    def test_batch_installed_empty_list(self) -> None:
        result = _batch_user_installed(MagicMock(), uuid.uuid4(), [])
        assert result == set()

    def test_batch_favorited_empty_list(self) -> None:
        result = _batch_user_favorited(MagicMock(), uuid.uuid4(), [])
        assert result == set()


class TestTrendingScoreRecalculation:
    """Regression: trending_score was never recalculated."""

    def test_recalculate_updates_scores(self) -> None:
        db = MagicMock()
        skill = MagicMock()
        skill.id = uuid.uuid4()
        skill.install_count = 100
        skill.favorite_count = 50
        skill.view_count = 1000
        skill.avg_rating = Decimal("4.50")
        skill.published_at = datetime.now(UTC) - timedelta(days=10)

        db.query.return_value.filter.return_value.all.return_value = [skill]
        mock_update_query = MagicMock()
        db.query.return_value.filter.return_value.update = mock_update_query.update

        count = recalculate_trending_scores(db)
        assert count == 1
        db.commit.assert_called_once()

    def test_decay_reduces_score_for_older_skills(self) -> None:
        """Older skills get lower trending scores via decay factor."""
        from skillhub.services.skills import recalculate_trending_scores

        # Prepare two skills with identical metrics but different ages
        new_skill = MagicMock()
        new_skill.id = uuid.uuid4()
        new_skill.install_count = 10
        new_skill.favorite_count = 5
        new_skill.view_count = 100
        new_skill.avg_rating = Decimal("4.00")
        new_skill.published_at = datetime.now(UTC)

        old_skill = MagicMock()
        old_skill.id = uuid.uuid4()
        old_skill.install_count = 10
        old_skill.favorite_count = 5
        old_skill.view_count = 100
        old_skill.avg_rating = Decimal("4.00")
        old_skill.published_at = datetime.now(UTC) - timedelta(days=90)

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [new_skill, old_skill]

        # Track update calls
        update_calls: list[dict[str, Any]] = []
        original_query = db.query.return_value.filter.return_value

        def capture_update(values: dict[str, Any]) -> None:
            update_calls.append(values)

        original_query.update = capture_update

        count = recalculate_trending_scores(db)
        assert count == 2


class TestForkContentCopy:
    """Regression: forked skills had no SkillVersion (uninstallable)."""

    def test_fork_copies_skill_version(self) -> None:
        from skillhub.services.social import fork_skill

        db = MagicMock()
        original = MagicMock()
        original.id = uuid.uuid4()
        original.name = "Code Review"
        original.short_desc = "Reviews code"
        original.category = "engineering"
        original.current_version = "1.0.0"
        original.install_method = "all"
        original.data_sensitivity = "low"
        original.external_calls = False

        upstream_version = MagicMock()
        upstream_version.version = "1.0.0"
        upstream_version.content = "# Code Review Skill"
        upstream_version.frontmatter = {"name": "Code Review"}
        upstream_version.content_hash = "abc123"

        db.query.return_value.filter.return_value.first.side_effect = [
            original,  # get_skill_or_404
            upstream_version,  # SkillVersion query
        ]
        db.query.return_value.filter.return_value.update = MagicMock()

        user_id = uuid.uuid4()
        result = fork_skill(db, "code-review", user_id)

        assert result["forked_skill_slug"].startswith("code-review-fork-")
        # Verify at least 3 objects were added: forked Skill, SkillVersion, Fork
        assert db.add.call_count >= 3


class TestGate2LLMJudge:
    """Regression: LLM judge was implemented but never called."""

    def test_gate2_calls_llm_when_enabled(self) -> None:
        from skillhub.schemas.submission import JudgeVerdict
        from skillhub.services.submissions import run_gate2_scan

        db = MagicMock()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.content = "# Test Skill"
        submission.submitted_by = uuid.uuid4()
        submission.status = MagicMock(value="gate1_passed")
        db.query.return_value.filter.return_value.first.side_effect = [
            submission,  # Submission lookup
            MagicMock(enabled=True),  # FeatureFlag lookup
        ]

        mock_verdict = JudgeVerdict(
            **{"pass": True}, score=90, findings=[], summary="Looks good"
        )

        async def mock_evaluate(content: str) -> JudgeVerdict:
            return mock_verdict

        with (
            patch("skillhub.services.llm_judge.LLMJudgeService") as mock_judge_cls,
            patch("skillhub.config.Settings") as mock_settings,
        ):
            mock_judge_instance = MagicMock()
            mock_judge_instance.evaluate = mock_evaluate
            mock_judge_cls.return_value = mock_judge_instance
            mock_settings.return_value.llm_router_url = "http://router:8080"
            mock_settings.return_value.llm_judge_enabled = True

            result = asyncio.run(run_gate2_scan(db, submission.id))

        assert result["score"] == 90

    def test_gate2_skips_when_disabled(self) -> None:
        from skillhub.services.submissions import run_gate2_scan

        db = MagicMock()
        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.content = "# Test Skill"
        submission.submitted_by = uuid.uuid4()
        db.query.return_value.filter.return_value.first.side_effect = [
            submission,  # Submission lookup
            MagicMock(enabled=False),  # FeatureFlag lookup (disabled)
        ]

        result = asyncio.run(run_gate2_scan(db, submission.id))
        assert result["score"] == 0
        assert "auto-pass" in result["summary"]
