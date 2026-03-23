---
name: skill-versioning-manager
description: Use when implementing skill version management, updates, or version history
---

# Skill Versioning Manager

## Model: skill_versions

```python
class SkillVersion(UUIDMixin, Base):
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"))
    version: Mapped[str]          # semver: "2.3.1"
    content: Mapped[str]          # Full SKILL.md content
    frontmatter: Mapped[dict]     # JSONB parsed frontmatter
    changelog: Mapped[str]
    content_hash: Mapped[str]     # SHA256 for dedup
    published_at: Mapped[datetime]
```

## "Latest" Resolution

```python
def get_latest_version(db, skill_id):
    return db.query(SkillVersion)\
        .filter_by(skill_id=skill_id)\
        .order_by(SkillVersion.published_at.desc())\
        .first()
```

## Content Hash (Dedup)

```python
import hashlib
content_hash = hashlib.sha256(content.encode()).hexdigest()
existing = db.query(SkillVersion).filter_by(skill_id=skill.id, content_hash=content_hash).first()
if existing:
    raise HTTPException(409, "Identical version already exists")
```

## MCP Update Detection

MCP `update_skill` compares local version against API latest. If different, downloads and overwrites local SKILL.md.

## References

- Skill model: `libs/db/skillhub_db/models/skill.py`
- Skills API: `apps/api/skillhub/routers/skills.py` (GET /skills/{slug}/versions)
- MCP update: `apps/mcp-server/skillhub_mcp/tools/update.py`
