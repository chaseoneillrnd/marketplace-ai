# MCP Server

9 tools exposed via the `mcp` SDK using `FastMCP`. Runs on port 8001.
Transport: `streamable-http`.

## Tools

| # | Tool | Description |
|---|---|---|
| 1 | `search_skills` | Browse/search with query, category, divisions, sort, install_method, verified, featured, page, per_page |
| 2 | `get_skill` | Full skill detail by slug + optional version |
| 3 | `install_skill` | Install to local filesystem with division check |
| 4 | `update_skill` | Update installed skill if newer version exists |
| 5 | `uninstall_skill` | Uninstall a skill from local filesystem and API |
| 6 | `list_installed` | List local installs with version info + stale flag |
| 7 | `fork_skill` | Fork a skill via API |
| 8 | `submit_skill` | Submit local SKILL.md for review |
| 9 | `get_submission_status` | Check submission status by ID |

### search_skills Parameters

| Param | Type | Description |
|---|---|---|
| `query` | str? | Free-text search |
| `category` | str? | Category slug filter |
| `divisions` | list[str]? | Division filter |
| `sort` | str? | Sort field |
| `install_method` | str? | Filter by install method |
| `verified` | bool? | Filter verified skills |
| `featured` | bool? | Filter featured skills |
| `page` | int | Page number (default 1) |
| `per_page` | int | Results per page (default 20) |

## API Client

`APIClient` wraps httpx with methods: `get`, `post`, `patch`, `delete`. All async. Bearer token passed via constructor.

## API Delegation Pattern

```
Claude Code →(MCP protocol)→ MCP Server →(HTTP + Bearer)→ Flask API →(SQLAlchemy)→ PostgreSQL
```

Thin layer. All business logic in the API. Each tool creates an `APIClient`, delegates to `skillhub_mcp/tools/`, returns API response.

## Division Enforcement

JWT decoded (without verification) to extract claims. Division checks happen API-side.

## Local Filesystem Layout

```
~/.local/share/claude/skills/{slug}/SKILL.md
```

Configurable via `SKILLHUB_MCP_SKILLS_DIR`.

## Configuration

| Var | Default | Description |
|---|---|---|
| `SKILLHUB_MCP_API_BASE_URL` | `http://localhost:8000` | API URL |
| `SKILLHUB_MCP_SKILLS_DIR` | `~/.local/share/claude/skills` | Install dir |
| `SKILLHUB_MCP_HOST` | `127.0.0.1` | Server host |
| `SKILLHUB_MCP_PORT` | `8001` | Server port |
| `SKILLHUB_MCP_DEBUG` | `false` | Debug mode |

## Key Files

- `apps/mcp-server/skillhub_mcp/server.py` — tool registration + FastMCP setup
- `apps/mcp-server/skillhub_mcp/api_client.py` — HTTP client (get/post/patch/delete)
- `apps/mcp-server/skillhub_mcp/config.py` — settings
- `apps/mcp-server/skillhub_mcp/tools/` — one module per tool
