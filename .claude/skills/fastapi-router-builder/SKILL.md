---
name: fastapi-router-builder
description: Use when creating new FastAPI routers in apps/api/skillhub/routers/
---

# FastAPI Router Builder

## Checklist

1. Create router file in `apps/api/skillhub/routers/{name}.py`
2. Create schemas in `apps/api/skillhub/schemas/{name}.py`
3. Create service in `apps/api/skillhub/services/{name}.py`
4. Register router in `apps/api/skillhub/main.py`
5. Create tests in `apps/api/tests/test_{name}.py`

## Router Pattern

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skillhub.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/v1/{name}", tags=["{name}"])

@router.get("/")
def list_items(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return service.list_items(db, user)
```

## Registration in main.py

```python
from skillhub.routers import {name}
app.include_router({name}.router)
```

## Service Layer Pattern

- Accept `db: Session` as first param
- Raise `HTTPException` for errors
- Write audit_log entries for mutations
- Use eager loading to prevent N+1

## References

- Existing router: `apps/api/skillhub/routers/skills.py`
- Service pattern: `apps/api/skillhub/services/skills.py`
- Dependencies: `apps/api/skillhub/dependencies.py`
- Schemas: `apps/api/skillhub/schemas/skill.py`
