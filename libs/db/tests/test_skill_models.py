"""Tests for Skill Core domain models."""

from decimal import Decimal

from sqlalchemy.orm import Session

from skillhub_db.models.skill import (
    Category,
    SkillDivision,
    SkillTag,
    SkillVersion,
    TriggerPhrase,
)


class TestCategory:
    def test_category_slug_is_primary_key(self, db: Session):
        cat = Category(slug="data", name="Data", sort_order=3)
        db.add(cat)
        db.commit()
        assert db.get(Category, "data") is not None


class TestSkill:
    def test_skill_instantiates_with_required_fields(self, db: Session, skill):
        assert skill.slug == "pr-review-assistant"
        assert skill.name == "PR Review Assistant"

    def test_skill_counters_default_to_zero(self, db: Session, skill):
        assert skill.install_count == 0
        assert skill.fork_count == 0
        assert skill.favorite_count == 0
        assert skill.view_count == 0
        assert skill.review_count == 0

    def test_skill_avg_rating_default(self, db: Session, skill):
        assert skill.avg_rating == Decimal("0.00")

    def test_skill_trending_score_default(self, db: Session, skill):
        assert skill.trending_score == Decimal("0.0000")

    def test_skill_status_defaults_to_draft(self, db: Session, skill):
        assert skill.status.value == "draft"


class TestSkillVersion:
    def test_version_content_hash_stored(self, db: Session, skill):
        sv = SkillVersion(
            skill_id=skill.id,
            version="1.0.0",
            content="# My Skill\nContent here",
            content_hash="a1b2c3d4e5f6",
        )
        db.add(sv)
        db.commit()
        assert sv.content_hash == "a1b2c3d4e5f6"

    def test_version_frontmatter_json(self, db: Session, skill):
        sv = SkillVersion(
            skill_id=skill.id,
            version="1.0.0",
            content="content",
            content_hash="hash123",
            frontmatter={"name": "test", "triggers": ["t1"]},
        )
        db.add(sv)
        db.commit()
        db.refresh(sv)
        assert sv.frontmatter["name"] == "test"


class TestSkillDivision:
    def test_skill_division_composite_key(self, db: Session, skill):
        sd = SkillDivision(
            skill_id=skill.id,
            division_slug="engineering-org",
        )
        db.add(sd)
        db.commit()
        assert sd.skill_id == skill.id
        assert sd.division_slug == "engineering-org"


class TestSkillTag:
    def test_skill_tag(self, db: Session, skill):
        tag = SkillTag(skill_id=skill.id, tag="code-review")
        db.add(tag)
        db.commit()
        assert tag.tag == "code-review"


class TestTriggerPhrase:
    def test_trigger_phrase(self, db: Session, skill):
        tp = TriggerPhrase(skill_id=skill.id, phrase="review my PR")
        db.add(tp)
        db.commit()
        assert tp.phrase == "review my PR"


class TestSkillRelationships:
    def test_skill_versions_relationship(self, db: Session, skill):
        sv = SkillVersion(
            skill_id=skill.id,
            version="1.0.0",
            content="content",
            content_hash="hash",
        )
        db.add(sv)
        db.commit()
        db.refresh(skill)
        assert len(skill.versions) == 1
        assert skill.versions[0].version == "1.0.0"

    def test_skill_tags_relationship(self, db: Session, skill):
        tag1 = SkillTag(skill_id=skill.id, tag="python")
        tag2 = SkillTag(skill_id=skill.id, tag="review")
        db.add_all([tag1, tag2])
        db.commit()
        db.refresh(skill)
        assert len(skill.tags) == 2

    def test_skill_divisions_relationship(self, db: Session, skill):
        sd = SkillDivision(skill_id=skill.id, division_slug="engineering-org")
        db.add(sd)
        db.commit()
        db.refresh(skill)
        assert len(skill.divisions) == 1

    def test_skill_trigger_phrases_relationship(self, db: Session, skill):
        tp = TriggerPhrase(skill_id=skill.id, phrase="help me review")
        db.add(tp)
        db.commit()
        db.refresh(skill)
        assert len(skill.trigger_phrases) == 1
