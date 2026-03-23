---
name: search-and-filter-builder
description: Use when implementing search, filter, or sort endpoints
---

# Search and Filter Builder

## Full-Text Search (PostgreSQL ILIKE)

```python
if search:
    query = query.filter(
        or_(
            Skill.name.ilike(f"%{search}%"),
            Skill.short_desc.ilike(f"%{search}%"),
        )
    )
```

## Multi-Value Filters

```python
if divisions:
    query = query.join(SkillDivision).filter(SkillDivision.division_slug.in_(divisions))
if category:
    query = query.filter(Skill.category == category)
if verified is not None:
    query = query.filter(Skill.verified == verified)
```

## Sort Signals

| Signal | Implementation |
|--------|---------------|
| trending | `ORDER BY trending_score DESC` |
| most_installed | `ORDER BY install_count DESC` |
| highest_rated | `ORDER BY avg_rating DESC` (Bayesian) |
| newest | `ORDER BY published_at DESC` |
| updated | `ORDER BY updated_at DESC` |

## Pagination

```python
total = query.count()
items = query.offset((page-1) * page_size).limit(page_size).all()
return {"items": items, "total": total, "page": page, "page_size": page_size}
```

## References

- Skills service: `apps/api/skillhub/services/skills.py`
- Browse endpoint: `apps/api/skillhub/routers/skills.py`
- FilteredView: `apps/web/src/views/FilteredView.tsx`
