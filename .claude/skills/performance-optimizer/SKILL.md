---
name: performance-optimizer
description: Use when optimizing React rendering, API response times, or bundle size
---

# Performance Optimizer

## React

- `React.memo` for SkillCard in grid renders
- `useMemo` for filtered/sorted lists
- `React.lazy` + `Suspense` for view code splitting
- Avoid re-renders: stable references for callbacks

## API

- Eager loading (joinedload/selectinload) to prevent N+1
- Pagination (never return unbounded results)
- Denormalized counters avoid COUNT queries

## Database

- Indexes on frequently queried columns (category, status, trending_score)
- EXPLAIN ANALYZE for slow queries

## References

- Skills service: `apps/api/skillhub/services/skills.py`
- Views: `apps/web/src/views/`
