---
name: error-handling-patterns
description: Use when implementing error handling across the API, frontend, or MCP server
---

# Error Handling Patterns

## Flask API

```python
from flask import abort

abort(404, description="Skill not found")
abort(403, description="Division not authorized")
abort(409, description="Already exists")
abort(422, description="Validation error")
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
{"description": "Human-readable error message"}
```

For validation: `{"messages": {"field": ["Error message"]}}`

## References

- Auth blueprint: `apps/api/skillhub_flask/blueprints/auth.py`
- API client: `apps/web/src/lib/api.ts`
- MCP tools: `apps/mcp-server/skillhub_mcp/tools/`
