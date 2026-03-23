---
name: mcp-tool-builder
description: Use when adding new MCP tools in apps/mcp-server/skillhub_mcp/tools/
---

# MCP Tool Builder

## Checklist

1. Create tool in `apps/mcp-server/skillhub_mcp/tools/{name}.py`
2. Register in `apps/mcp-server/skillhub_mcp/server.py`
3. Add API client method if needed in `api_client.py`
4. Create tests in `apps/mcp-server/tests/test_{name}.py`

## Tool Pattern

```python
from mcp.server import Server
from skillhub_mcp.api_client import SkillHubClient

async def register(server: Server, client: SkillHubClient):
    @server.tool("my_tool")
    async def my_tool(slug: str) -> dict:
        """Tool description for Claude."""
        result = await client.get(f"/api/v1/skills/{slug}")
        return {"success": True, "data": result}
```

## Division Enforcement

```python
# Check before any write operation
user = await client.get("/api/v1/users/me")
skill = await client.get(f"/api/v1/skills/{slug}")
if user["division"] not in [d["slug"] for d in skill["divisions"]]:
    return {"success": False, "error": "division_restricted"}
```

## Registration in server.py

```python
from skillhub_mcp.tools import my_tool
await my_tool.register(server, client)
```

## References

- Server: `apps/mcp-server/skillhub_mcp/server.py`
- Install tool: `apps/mcp-server/skillhub_mcp/tools/install.py`
- API client: `apps/mcp-server/skillhub_mcp/api_client.py`
- Tests: `apps/mcp-server/tests/test_install.py`
