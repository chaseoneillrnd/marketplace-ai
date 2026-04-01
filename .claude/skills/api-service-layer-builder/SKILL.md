---
name: api-service-layer-builder
description: Use when creating service modules in apps/api/skillhub/services/
---

# API Service Layer Builder

## Pattern

```python
# apps/api/skillhub/services/my_service.py
from sqlalchemy.orm import Session, joinedload
from flask import abort

def list_items(db: Session, user: dict, page: int = 1, page_size: int = 20):
    query = db.query(MyModel).options(joinedload(MyModel.related))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}

def get_item(db: Session, item_id: str):
    item = db.query(MyModel).filter(MyModel.id == item_id).first()
    if not item:
        abort(404, description="Item not found")
    return item
```

## Rules

- Services accept `db: Session` as first param
- Services use `abort(status_code, description=...)` for errors
- Use `joinedload`/`selectinload` to prevent N+1
- Write audit_log entries for mutations
- Keep business logic here, not in blueprints

## References

- Skills service: `apps/api/skillhub/services/skills.py`
- Social service: `apps/api/skillhub/services/social.py`
- Submission service: `apps/api/skillhub/services/submission.py`
