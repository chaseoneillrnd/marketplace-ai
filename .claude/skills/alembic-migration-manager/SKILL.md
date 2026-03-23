---
name: alembic-migration-manager
description: Use when creating or managing database migrations with Alembic
---

# Alembic Migration Manager

## Quick Commands

| Task | Command |
|------|---------|
| Generate from models | `mise run db:make-migration "description"` |
| Apply all | `mise run db:migrate` |
| Rollback one | `mise run db:rollback` |
| Rollback all | `mise run db:rollback:all` |
| Check status | `mise run db:check` |
| Full reset | `mise run db:reset` |

## Migration Naming

`libs/db/alembic/versions/YYYYMMDD_HHMM_description.py`

## Autogenerate Pattern

```bash
# 1. Edit model in libs/db/skillhub_db/models/
# 2. Generate migration
mise run db:make-migration "add user_preferences table"
# 3. Review generated file
# 4. Apply
mise run db:migrate
```

## Manual Migration

```python
def upgrade():
    op.add_column('skills', sa.Column('deprecated_at', sa.DateTime))
    op.create_index('idx_skills_deprecated', 'skills', ['deprecated_at'])

def downgrade():
    op.drop_index('idx_skills_deprecated')
    op.drop_column('skills', 'deprecated_at')
```

## Data Migration

```python
def upgrade():
    # Schema change
    op.add_column('skills', sa.Column('new_field', sa.String))
    # Data backfill
    op.execute("UPDATE skills SET new_field = old_field WHERE old_field IS NOT NULL")
```

## CI Guard

`alembic check` in CI fails if models diverge from migrations. Run `mise run db:check` locally before committing.

## References

- Config: `libs/db/alembic.ini`
- Existing migration: `libs/db/alembic/versions/001_initial_schema.py`
- Models: `libs/db/skillhub_db/models/`
