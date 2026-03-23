---
name: error-handling-patterns
description: Use when implementing error handling across the API, frontend, or MCP server
---

# Error Handling Patterns

## FastAPI

```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="Skill not found")
raise HTTPException(status_code=403, detail="Division not authorized")
raise HTTPException(status_code=409, detail="Already exists")
raise HTTPException(status_code=422, detail="Validation error")
```

## React API Client

```typescript
// apps/web/src/lib/api.ts
async function handleResponse(res: Response) {
  if (res.status === 401) { clearToken(); window.location.reload(); }
  if (res.status === 403) { throw new Error("Access denied"); }
  if (res.status === 404) { throw new Error("Not found"); }
  if (!res.ok) { throw new Error(await res.text()); }
  return res.json();
}
```

## MCP Tool Errors

```python
return {"success": False, "error": "division_restricted",
        "message": "Your division is not authorized for this skill"}
```

## Error Response Schema

```json
{"detail": "Human-readable error message"}
```

For validation: `{"detail": [{"loc": ["body", "field"], "msg": "...", "type": "..."}]}`

## References

- API dependencies: `apps/api/skillhub/dependencies.py`
- API client: `apps/web/src/lib/api.ts`
- MCP tools: `apps/mcp-server/skillhub_mcp/tools/`
