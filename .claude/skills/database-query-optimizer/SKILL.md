---
name: database-query-optimizer
description: Use when optimizing SQLAlchemy queries or addressing N+1 problems
---

# Database Query Optimizer

## Prevent N+1 with Eager Loading

```python
from sqlalchemy.orm import joinedload, selectinload

# joinedload = single JOIN query (good for to-one)
skills = db.query(Skill).options(joinedload(Skill.category_rel)).all()

# selectinload = separate IN query (good for to-many)
skills = db.query(Skill).options(selectinload(Skill.divisions)).all()
```

## Key Indexes

```sql
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_status ON skills(status);
CREATE INDEX idx_skills_trending ON skills(trending_score DESC);
CREATE INDEX idx_installs_skill_user ON installs(skill_id, user_id);
CREATE INDEX idx_favorites_user ON favorites(user_id);
CREATE INDEX idx_audit_log_event ON audit_log(event_type, created_at);
```

## Denormalized Counter Trade-offs

Counters on skills table (install_count, etc.) avoid expensive COUNT queries. Trade-off: must update on every social action. Source of truth = join table; counter = cache.

## EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE SELECT * FROM skills WHERE category = 'testing' ORDER BY trending_score DESC LIMIT 20;
```

## References

- Skills service: `apps/api/skillhub/services/skills.py`
- Models: `libs/db/skillhub_db/models/`
