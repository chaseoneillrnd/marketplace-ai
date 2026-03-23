---
name: pydantic-schema-designer
description: Use when creating Pydantic v2 schemas in apps/api/skillhub/schemas/
---

# Pydantic Schema Designer

## Schema File Pattern

Create in `apps/api/skillhub/schemas/{domain}.py`

## Request vs Response

```python
from pydantic import BaseModel, ConfigDict

# Request — what the client sends
class SkillCreate(BaseModel):
    name: str
    slug: str
    short_desc: str
    category: str
    divisions: list[str]

# Response — what the API returns
class SkillSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    short_desc: str
    install_count: int
    avg_rating: float

# Detail — full response
class SkillDetail(SkillSummary):
    description: str
    versions: list[SkillVersionResponse]
    divisions: list[DivisionResponse]
    tags: list[str]
```

## Pagination Response

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
```

## Browse Parameters

```python
class BrowseParams(BaseModel):
    category: str | None = None
    divisions: list[str] | None = None
    sort: str = "trending"
    page: int = 1
    page_size: int = 20
    search: str | None = None
```

## References

- Skill schemas: `apps/api/skillhub/schemas/skill.py`
- Used in routers: `apps/api/skillhub/routers/skills.py`
