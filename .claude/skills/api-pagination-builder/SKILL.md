---
name: api-pagination-builder
description: Use when implementing pagination for API endpoints
---

# API Pagination Builder

## Backend Pattern

```python
@router.get("/api/v1/items")
def list_items(page: int = 1, page_size: int = 20, db=Depends(get_db)):
    query = db.query(Item)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}
```

## Response Schema

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
```

## Frontend (Load More)

```tsx
const [page, setPage] = useState(1);
const [items, setItems] = useState([]);
const [hasMore, setHasMore] = useState(true);

const loadMore = async () => {
  const res = await api.get(`/api/v1/items?page=${page + 1}`);
  setItems(prev => [...prev, ...res.items]);
  setHasMore(res.items.length === res.page_size);
  setPage(p => p + 1);
};
```

## References

- Skills browse: `apps/api/skillhub/routers/skills.py`
- Skill schemas: `apps/api/skillhub/schemas/skill.py`
