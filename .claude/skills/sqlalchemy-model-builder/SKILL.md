---
name: sqlalchemy-model-builder
description: Use when adding new SQLAlchemy 2 models in libs/db/skillhub_db/models/
---

# SQLAlchemy Model Builder

## Checklist

1. Create model in `libs/db/skillhub_db/models/{name}.py`
2. Register in `libs/db/skillhub_db/models/__init__.py`
3. Generate migration: `mise run db:make-migration`
4. Add seed data in `libs/db/scripts/seed.py`
5. Create tests in `libs/db/tests/test_{name}_models.py`

## Model Pattern

```python
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from skillhub_db.base import Base, UUIDMixin, TimestampMixin

class MyModel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "my_models"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="my_models")
```

## Mixins (from base.py)

- `UUIDMixin` — adds `id: UUID` primary key
- `TimestampMixin` — adds `created_at`, `updated_at`

## Migration

```bash
mise run db:make-migration "add my_models table"
mise run db:migrate
```

## References

- Base/Mixins: `libs/db/skillhub_db/base.py`
- Skill model: `libs/db/skillhub_db/models/skill.py`
- Social models: `libs/db/skillhub_db/models/social.py`
- Tests: `libs/db/tests/test_skill_models.py`
