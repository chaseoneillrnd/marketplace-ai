---
name: seed-data-manager
description: Use when managing seed data in libs/db/scripts/seed.py
---

# Seed Data Manager

## Idempotent Insert Pattern

```python
def seed_divisions(db):
    divisions = [
        {"slug": "engineering-org", "name": "Engineering Org", "color": "#3B82F6"},
        {"slug": "marketing", "name": "Marketing", "color": "#8B5CF6"},
        # ... 8 total
    ]
    for d in divisions:
        existing = db.query(Division).filter_by(slug=d["slug"]).first()
        if not existing:
            db.add(Division(**d))
```

## Seeded Data

| Table | Count | Purpose |
|-------|-------|---------|
| divisions | 8 | Engineering, Marketing, Sales, Legal, HR, Finance, Product, Design |
| categories | 9 | Code Review, Testing, DevOps, Documentation, Security, etc. |
| feature_flags | 4 | llm_judge, mcp_install, featured_v2, gamification |
| users | 1 | Test user (dev only) |

## Run

```bash
mise run db:seed          # Seed only
mise run db:reset         # Drop + migrate + seed
```

## References

- Seed script: `libs/db/scripts/seed.py`
- Division model: `libs/db/skillhub_db/models/division.py`
- Category model: `libs/db/skillhub_db/models/skill.py`
