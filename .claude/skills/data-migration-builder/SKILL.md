---
name: data-migration-builder
description: Use when writing data migrations (backfills, counter updates) with Alembic
---

# Data Migration Builder

## Pattern

```python
def upgrade():
    op.execute("""
        UPDATE skills SET install_count = (
            SELECT COUNT(*) FROM installs
            WHERE installs.skill_id = skills.id AND installs.uninstalled_at IS NULL
        )
    """)

def downgrade():
    pass  # Data migrations typically not reversible
```

## Backfill Strategy

For large tables, batch:
```python
op.execute("UPDATE skills SET field = value WHERE id IN (SELECT id FROM skills LIMIT 1000)")
```

## References

- Migrations: `libs/db/alembic/versions/`
- Alembic config: `libs/db/alembic.ini`
