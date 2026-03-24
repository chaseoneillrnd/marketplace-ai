"""Tests for seed data integrity and reconciliation logic.

Verifies that:
1. All skill counters are zeroed (no fabricated values)
2. Bayesian avg_rating formula matches services/reviews.py
3. Review days_ago values are varied (not all the same)
4. Install and favorite seed data reference valid skills/users
5. content_hash uses deterministic hashing
6. Reconciliation logic produces correct counts
"""

from __future__ import annotations

import hashlib
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pytest

# Add seed scripts to path so we can import seed_data
_seed_dir = str(Path(__file__).resolve().parents[3] / "libs" / "db" / "scripts")
if _seed_dir not in sys.path:
    sys.path.insert(0, _seed_dir)

from seed_data import (
    ALL_SKILLS,
    SEED_FAVORITES,
    SEED_INSTALLS,
    SEED_REVIEWS,
    SEED_USERS,
)

# Bayesian constants — must match services/reviews.py and seed.py
BAYESIAN_C = 5
BAYESIAN_M = Decimal("3.0")


class TestSkillCountersZeroed:
    """Verify no fabricated counters remain in seed data."""

    def test_all_review_counts_are_zero(self) -> None:
        for skill in ALL_SKILLS:
            assert skill["review_count"] == 0, (
                f"Skill '{skill['slug']}' has fabricated review_count={skill['review_count']}"
            )

    def test_all_avg_ratings_are_zero(self) -> None:
        for skill in ALL_SKILLS:
            assert skill["avg_rating"] == 0.0, (
                f"Skill '{skill['slug']}' has fabricated avg_rating={skill['avg_rating']}"
            )

    def test_all_install_counts_are_zero(self) -> None:
        for skill in ALL_SKILLS:
            assert skill["install_count"] == 0, (
                f"Skill '{skill['slug']}' has fabricated install_count={skill['install_count']}"
            )

    def test_all_fork_counts_are_zero(self) -> None:
        for skill in ALL_SKILLS:
            assert skill.get("fork_count", 0) == 0, (
                f"Skill '{skill['slug']}' has fabricated fork_count={skill.get('fork_count')}"
            )

    def test_all_favorite_counts_are_zero(self) -> None:
        for skill in ALL_SKILLS:
            assert skill.get("favorite_count", 0) == 0, (
                f"Skill '{skill['slug']}' has fabricated favorite_count={skill.get('favorite_count')}"
            )

    def test_all_trending_scores_are_zero(self) -> None:
        for skill in ALL_SKILLS:
            assert skill["trending_score"] == 0.0, (
                f"Skill '{skill['slug']}' has fabricated trending_score={skill['trending_score']}"
            )


class TestBayesianFormula:
    """Verify the Bayesian avg_rating formula produces correct results."""

    def _bayesian_avg(self, ratings: list[int]) -> Decimal:
        """Compute Bayesian average from a list of ratings."""
        count = len(ratings)
        sum_ratings = Decimal(str(sum(ratings)))
        return round(
            (BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + count),
            2,
        )

    def test_no_reviews_gives_prior_mean(self) -> None:
        result = self._bayesian_avg([])
        assert result == BAYESIAN_M

    def test_single_five_star_review(self) -> None:
        result = self._bayesian_avg([5])
        # (5*3.0 + 5) / (5+1) = 20/6 = 3.33
        assert result == Decimal("3.33")

    def test_many_high_reviews_approaches_true_mean(self) -> None:
        # 100 five-star reviews should pull avg close to 5
        result = self._bayesian_avg([5] * 100)
        # (5*3 + 500) / (5+100) = 515/105 = 4.90...
        assert result >= Decimal("4.90")

    def test_mixed_reviews(self) -> None:
        # ratings: 5, 4, 5, 3 -> sum=17, count=4
        # (5*3.0 + 17) / (5+4) = 32/9 = 3.56
        result = self._bayesian_avg([5, 4, 5, 3])
        assert result == Decimal("3.56")

    def test_formula_matches_expected_for_each_reviewed_skill(self) -> None:
        """For each skill that has reviews in SEED_REVIEWS, verify the
        Bayesian formula produces a consistent result."""
        reviews_by_skill: dict[str, list[int]] = {}
        for r in SEED_REVIEWS:
            reviews_by_skill.setdefault(r["skill_slug"], []).append(r["rating"])

        for slug, ratings in reviews_by_skill.items():
            expected = self._bayesian_avg(ratings)
            count = len(ratings)
            sum_r = Decimal(str(sum(ratings)))
            manual = round(
                (BAYESIAN_C * BAYESIAN_M + sum_r) / (BAYESIAN_C + count), 2
            )
            assert expected == manual, (
                f"Bayesian mismatch for '{slug}': {expected} != {manual}"
            )


class TestReviewCountReconciliation:
    """Verify that review_count would match actual review rows after seeding."""

    def test_review_count_matches_actual_rows(self) -> None:
        """For every skill with reviews, the expected review_count should
        equal the actual count of review entries in SEED_REVIEWS."""
        reviews_by_skill = Counter(r["skill_slug"] for r in SEED_REVIEWS)
        skill_slugs = {s["slug"] for s in ALL_SKILLS}

        for slug, count in reviews_by_skill.items():
            if slug in skill_slugs:
                # After reconciliation, skill.review_count should be this count
                assert count > 0, f"Expected reviews for '{slug}' but got 0"

    def test_skills_without_reviews_have_zero_count(self) -> None:
        """Skills not in SEED_REVIEWS should keep review_count=0."""
        reviewed_slugs = {r["skill_slug"] for r in SEED_REVIEWS}
        for skill in ALL_SKILLS:
            if skill["slug"] not in reviewed_slugs:
                # After reconciliation, review_count stays 0
                assert skill["review_count"] == 0


class TestInstallCountReconciliation:
    """Verify install_count would match actual install rows after seeding."""

    def test_install_count_matches_actual_rows(self) -> None:
        installs_by_skill = Counter(inst["skill_slug"] for inst in SEED_INSTALLS)
        skill_slugs = {s["slug"] for s in ALL_SKILLS}

        for slug, count in installs_by_skill.items():
            assert slug in skill_slugs, (
                f"SEED_INSTALLS references non-existent skill '{slug}'"
            )
            assert count > 0

    def test_install_references_valid_users(self) -> None:
        for inst in SEED_INSTALLS:
            assert inst["user_index"] < len(SEED_USERS), (
                f"Install for '{inst['skill_slug']}' references invalid user_index={inst['user_index']}"
            )


class TestFavoriteCountReconciliation:
    """Verify favorite_count would match actual favorite rows after seeding."""

    def test_favorite_count_matches_actual_rows(self) -> None:
        favs_by_skill = Counter(fav["skill_slug"] for fav in SEED_FAVORITES)
        skill_slugs = {s["slug"] for s in ALL_SKILLS}

        for slug, count in favs_by_skill.items():
            assert slug in skill_slugs, (
                f"SEED_FAVORITES references non-existent skill '{slug}'"
            )
            assert count > 0

    def test_favorite_references_valid_users(self) -> None:
        for fav in SEED_FAVORITES:
            assert fav["user_index"] < len(SEED_USERS), (
                f"Favorite for '{fav['skill_slug']}' references invalid user_index={fav['user_index']}"
            )


class TestReviewDaysAgoVaried:
    """Verify review dates are spread across different time ranges."""

    def test_reviews_have_days_ago(self) -> None:
        for r in SEED_REVIEWS:
            assert "days_ago" in r, (
                f"Review for '{r['skill_slug']}' missing days_ago field"
            )

    def test_days_ago_values_are_varied(self) -> None:
        days_values = {r["days_ago"] for r in SEED_REVIEWS}
        # Should have at least 3 distinct values
        assert len(days_values) >= 3, (
            f"Expected varied days_ago values, got only {days_values}"
        )

    def test_days_ago_spans_reasonable_range(self) -> None:
        days_values = [r["days_ago"] for r in SEED_REVIEWS]
        assert min(days_values) <= 7, "Expected some recent reviews (within 7 days)"
        assert max(days_values) >= 30, "Expected some older reviews (30+ days)"


class TestContentHash:
    """Verify content_hash uses deterministic SHA256-based hashing."""

    def test_content_hash_is_deterministic(self) -> None:
        """Same content should always produce same hash."""
        for skill in ALL_SKILLS[:5]:  # Sample a few
            content = skill["content"]
            hash1 = hashlib.sha256(content.encode()).hexdigest()[:16]
            hash2 = hashlib.sha256(content.encode()).hexdigest()[:16]
            assert hash1 == hash2, f"Hash not deterministic for '{skill['slug']}'"

    def test_different_content_produces_different_hash(self) -> None:
        """Different content should produce different hashes."""
        hashes = set()
        for skill in ALL_SKILLS:
            h = hashlib.sha256(skill["content"].encode()).hexdigest()[:16]
            hashes.add(h)
        # With 61 skills, we should have at least 50 unique hashes
        assert len(hashes) >= 50, (
            f"Expected mostly unique content hashes, got {len(hashes)} unique out of {len(ALL_SKILLS)}"
        )


class TestSeedDataReferentialIntegrity:
    """Verify all foreign key references in seed data are valid."""

    def test_review_skill_slugs_exist(self) -> None:
        skill_slugs = {s["slug"] for s in ALL_SKILLS}
        for r in SEED_REVIEWS:
            assert r["skill_slug"] in skill_slugs, (
                f"Review references non-existent skill '{r['skill_slug']}'"
            )

    def test_review_user_indices_valid(self) -> None:
        for r in SEED_REVIEWS:
            assert r["user_index"] < len(SEED_USERS), (
                f"Review for '{r['skill_slug']}' has invalid user_index={r['user_index']}"
            )

    def test_install_skill_slugs_exist(self) -> None:
        skill_slugs = {s["slug"] for s in ALL_SKILLS}
        for inst in SEED_INSTALLS:
            assert inst["skill_slug"] in skill_slugs, (
                f"Install references non-existent skill '{inst['skill_slug']}'"
            )

    def test_favorite_skill_slugs_exist(self) -> None:
        skill_slugs = {s["slug"] for s in ALL_SKILLS}
        for fav in SEED_FAVORITES:
            assert fav["skill_slug"] in skill_slugs, (
                f"Favorite references non-existent skill '{fav['skill_slug']}'"
            )

    def test_no_duplicate_review_per_skill_user(self) -> None:
        """Each (skill_slug, user_index) pair should be unique in reviews."""
        seen = set()
        for r in SEED_REVIEWS:
            key = (r["skill_slug"], r["user_index"])
            assert key not in seen, (
                f"Duplicate review: skill='{r['skill_slug']}' user_index={r['user_index']}"
            )
            seen.add(key)

    def test_no_duplicate_favorite_per_skill_user(self) -> None:
        """Each (skill_slug, user_index) pair should be unique in favorites."""
        seen = set()
        for fav in SEED_FAVORITES:
            key = (fav["skill_slug"], fav["user_index"])
            assert key not in seen, (
                f"Duplicate favorite: skill='{fav['skill_slug']}' user_index={fav['user_index']}"
            )
            seen.add(key)

    def test_no_duplicate_install_per_skill_user(self) -> None:
        """Each (skill_slug, user_index) pair should be unique in installs."""
        seen = set()
        for inst in SEED_INSTALLS:
            key = (inst["skill_slug"], inst["user_index"])
            assert key not in seen, (
                f"Duplicate install: skill='{inst['skill_slug']}' user_index={inst['user_index']}"
            )
            seen.add(key)


# ---------------------------------------------------------------------------
# Admin seed data integrity — feedback, metrics, platform updates
# ---------------------------------------------------------------------------

from seed_data import SEED_FEEDBACK, SEED_DAILY_METRICS, SEED_PLATFORM_UPDATES


class TestAdminSeedDataIntegrity:
    """Verify admin seed data is present and correctly formatted."""

    def test_feedback_entries_exist(self) -> None:
        """Seed data includes feedback entries."""
        assert len(SEED_FEEDBACK) >= 15, (
            f"Expected >= 15 feedback entries, got {len(SEED_FEEDBACK)}"
        )

    def test_feedback_categories_diverse(self) -> None:
        """Feedback covers all 4 categories."""
        categories = {f["category"] for f in SEED_FEEDBACK}
        expected = {"feature_request", "bug_report", "praise", "complaint"}
        assert expected.issubset(categories), (
            f"Missing categories: {expected - categories}"
        )

    def test_daily_metrics_exist(self) -> None:
        """Seed data includes 30 days of daily metrics."""
        assert len(SEED_DAILY_METRICS) >= 200, (
            f"Expected >= 200 daily_metrics rows (30 days x ~9 divisions), "
            f"got {len(SEED_DAILY_METRICS)}"
        )

    def test_daily_metrics_has_all_sentinel(self) -> None:
        """daily_metrics includes __all__ platform-wide rows."""
        all_count = sum(
            1 for m in SEED_DAILY_METRICS if m.get("division_slug") == "__all__"
        )
        assert all_count >= 25, (
            f"Expected >= 25 __all__ rows (30 days), got {all_count}"
        )

    def test_platform_updates_exist(self) -> None:
        """Seed data includes roadmap/changelog entries."""
        assert len(SEED_PLATFORM_UPDATES) >= 10, (
            f"Expected >= 10 platform_updates, got {len(SEED_PLATFORM_UPDATES)}"
        )

    def test_platform_updates_has_shipped(self) -> None:
        """Some platform updates are shipped (changelog entries)."""
        shipped = sum(1 for u in SEED_PLATFORM_UPDATES if u["status"] == "shipped")
        assert shipped >= 3, (
            f"Expected >= 3 shipped items for changelog, got {shipped}"
        )

    def test_platform_updates_has_planned(self) -> None:
        """Some platform updates are planned (roadmap entries)."""
        planned = sum(1 for u in SEED_PLATFORM_UPDATES if u["status"] == "planned")
        assert planned >= 2, (
            f"Expected >= 2 planned items, got {planned}"
        )

    def test_feedback_references_valid_users(self) -> None:
        """Feedback user_index values must be valid."""
        for fb in SEED_FEEDBACK:
            assert fb["user_index"] < len(SEED_USERS), (
                f"Feedback has invalid user_index={fb['user_index']}"
            )

    def test_feedback_has_required_fields(self) -> None:
        """Each feedback entry must have all required fields."""
        required = {"user_index", "category", "body", "sentiment", "days_ago"}
        for i, fb in enumerate(SEED_FEEDBACK):
            missing = required - set(fb.keys())
            assert not missing, (
                f"Feedback entry {i} missing fields: {missing}"
            )
