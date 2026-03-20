"""Tests for Skill domain Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from skillhub.schemas.skill import (
    SkillBrowseParams,
    SkillBrowseResponse,
    SkillDetail,
    SkillSummary,
    SkillVersionListItem,
    SkillVersionResponse,
    SortOption,
    TriggerPhraseResponse,
)


class TestSkillSummary:
    """Tests for SkillSummary schema."""

    def test_instantiates_with_required_fields(self) -> None:
        summary = SkillSummary(
            id=uuid.uuid4(),
            slug="pr-review-assistant",
            name="PR Review Assistant",
            short_desc="Automated PR reviews",
            category="Engineering",
            author_type="community",
            version="1.0.0",
            install_method="all",
            verified=False,
            featured=False,
            install_count=42,
            fork_count=5,
            favorite_count=10,
            avg_rating=Decimal("4.20"),
            rating_count=8,
        )
        assert summary.slug == "pr-review-assistant"
        assert summary.install_count == 42

    def test_defaults_for_optional_fields(self) -> None:
        summary = SkillSummary(
            id=uuid.uuid4(),
            slug="test",
            name="Test",
            short_desc="desc",
            category="Engineering",
            author_type="community",
            version="1.0.0",
            install_method="all",
            verified=False,
            featured=False,
            install_count=0,
            fork_count=0,
            favorite_count=0,
            avg_rating=Decimal("0.00"),
            rating_count=0,
        )
        assert summary.divisions == []
        assert summary.tags == []
        assert summary.author is None
        assert summary.days_ago is None
        assert summary.user_has_installed is None
        assert summary.user_has_favorited is None

    def test_from_attributes_mode(self) -> None:
        """SkillSummary has from_attributes config for ORM compatibility."""
        assert SkillSummary.model_config.get("from_attributes") is True


class TestSkillDetail:
    """Tests for SkillDetail schema."""

    def test_includes_trigger_phrases(self) -> None:
        detail = SkillDetail(
            id=uuid.uuid4(),
            slug="code-review",
            name="Code Review",
            short_desc="Reviews code",
            category="Engineering",
            author_id=uuid.uuid4(),
            author_type="official",
            current_version="2.0.0",
            install_method="claude-code",
            data_sensitivity="low",
            external_calls=False,
            verified=True,
            featured=True,
            status="published",
            install_count=100,
            fork_count=10,
            favorite_count=50,
            view_count=1000,
            review_count=20,
            avg_rating=Decimal("4.50"),
            trending_score=Decimal("85.1234"),
            trigger_phrases=[
                TriggerPhraseResponse(id=uuid.uuid4(), phrase="review this PR"),
                TriggerPhraseResponse(id=uuid.uuid4(), phrase="check my code"),
            ],
        )
        assert len(detail.trigger_phrases) == 2
        assert detail.trigger_phrases[0].phrase == "review this PR"

    def test_from_attributes_mode(self) -> None:
        assert SkillDetail.model_config.get("from_attributes") is True


class TestSkillBrowseParams:
    """Tests for SkillBrowseParams schema."""

    def test_validates_sort_enum(self) -> None:
        params = SkillBrowseParams(sort=SortOption.RATING)
        assert params.sort == SortOption.RATING

    def test_invalid_sort_rejected(self) -> None:
        with pytest.raises(ValueError):
            SkillBrowseParams(sort="invalid")  # type: ignore[arg-type]

    def test_per_page_max_100(self) -> None:
        params = SkillBrowseParams(per_page=100)
        assert params.per_page == 100

    def test_per_page_over_100_rejected(self) -> None:
        with pytest.raises(ValueError):
            SkillBrowseParams(per_page=200)

    def test_per_page_min_1(self) -> None:
        with pytest.raises(ValueError):
            SkillBrowseParams(per_page=0)

    def test_divisions_defaults_to_empty_list(self) -> None:
        params = SkillBrowseParams()
        assert params.divisions == []

    def test_divisions_accepts_list(self) -> None:
        params = SkillBrowseParams(divisions=["Engineering Org", "Product Org"])
        assert len(params.divisions) == 2

    def test_defaults(self) -> None:
        params = SkillBrowseParams()
        assert params.q is None
        assert params.category is None
        assert params.sort == SortOption.TRENDING
        assert params.page == 1
        assert params.per_page == 20


class TestSkillBrowseResponse:
    """Tests for SkillBrowseResponse schema."""

    def test_has_more_flag(self) -> None:
        response = SkillBrowseResponse(
            items=[],
            total=0,
            page=1,
            per_page=20,
            has_more=False,
        )
        assert response.has_more is False


class TestSkillVersionResponse:
    """Tests for SkillVersionResponse schema."""

    def test_includes_content_and_frontmatter(self) -> None:
        version = SkillVersionResponse(
            id=uuid.uuid4(),
            version="1.2.0",
            content="# My Skill\nDoes things.",
            frontmatter={"name": "My Skill", "version": "1.2.0"},
            published_at=datetime.now(UTC),
        )
        assert version.content.startswith("# My Skill")
        assert version.frontmatter is not None
        assert version.frontmatter["version"] == "1.2.0"

    def test_from_attributes_mode(self) -> None:
        assert SkillVersionResponse.model_config.get("from_attributes") is True


class TestSkillVersionListItem:
    """Tests for SkillVersionListItem schema."""

    def test_no_content_field(self) -> None:
        item = SkillVersionListItem(
            id=uuid.uuid4(),
            version="1.0.0",
            published_at=datetime.now(UTC),
        )
        assert not hasattr(item, "content") or "content" not in item.model_fields
        assert item.version == "1.0.0"
