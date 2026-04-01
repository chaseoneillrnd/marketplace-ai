# SkillHub

Internal AI skills marketplace. Browse, install, review, share Claude skills.

## Quick Start

```
mise run install          # install all dependencies
mise run db:up            # start postgres
mise run db:migrate       # run migrations
mise run db:seed          # seed initial data
mise run dev:api          # start API on :8000
mise run dev:web          # start frontend on :5173
mise run dev:mcp          # start MCP server on :8001
```

Or via Docker: `docker compose up -d`

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + TypeScript |
| Backend | Flask/APIFlask + SQLAlchemy 2 + Alembic |
| MCP Server | Python + FastMCP SDK |
| Database | PostgreSQL 16 |
| Monorepo | NX + mise |
| Lint/Format | ruff + eslint + prettier |
| Testing | pytest + Vitest |
| Tracing | Jaeger (local) |

## Architecture

NX monorepo. API handles all business logic. MCP server delegates to API. React SPA consumes REST endpoints. Division enforcement is server-side only.

See [docs/architecture/OVERVIEW.md](docs/architecture/OVERVIEW.md).

## Development

| Command | What |
|---|---|
| `mise run dev:api` | API server with hot reload |
| `mise run dev:web` | Vite dev server |
| `mise run dev:mcp` | MCP server |
| `mise run db:migrate` | Run Alembic migrations |
| `mise run db:seed` | Seed divisions, categories, flags, stub user |
| `mise run db:reset` | Drop + migrate + seed |
| `mise run gen:openapi` | Generate OpenAPI spec |
| `mise run gen:types` | Generate TS types from OpenAPI |

## Testing

| Command | What |
|---|---|
| `mise run test:api` | API tests (pytest) |
| `mise run test:web` | Web tests (vitest) |
| `mise run test:mcp` | MCP server tests |
| `mise run test:db` | DB lib tests |
| `mise run test:api:coverage` | API tests with 80% coverage gate |
| `mise run test:web:coverage` | Web tests with 80% coverage gate |

## Tracing

Local-only. Jaeger all-in-one. Disabled by default.

| Command | What |
|---|---|
| `mise run tracing:up` | Start Jaeger |
| `mise run tracing:down` | Stop Jaeger |
| `mise run tracing:ui` | Open Jaeger UI (localhost:16686) |
| `mise run tracing:status` | Check Jaeger health |

Set `OTEL_TRACES_ENABLED=true` in `.env` to emit traces. Jaeger UI at `http://localhost:16686`.

## Quality

```
mise run lint:api         # ruff check
mise run lint:web         # eslint
mise run format:check     # ruff format + prettier --check
mise run typecheck:api    # mypy --strict
mise run typecheck:web    # tsc --noEmit
mise run quality-gate     # all of the above + tests
```

## Documentation

- [docs/architecture/](docs/architecture/) -- system design
- [docs/ai-agent/](docs/ai-agent/) -- agent-oriented reference (start with [DOC-MAP](docs/ai-agent/DOC-MAP.md))
- [skillhub-design.md](skillhub-design.md) -- approved design document
- [skillhub-technical-guide.md](skillhub-technical-guide.md) -- implementation guide
- [skillhub-diagrams.md](skillhub-diagrams.md) -- Mermaid diagrams

## Project Structure

```
apps/
  api/                  # Flask/APIFlask backend
  web/                  # React + Vite frontend
  mcp-server/           # MCP server for Claude Code
libs/
  db/                   # SQLAlchemy models + Alembic migrations
  python-common/        # Shared Python utilities
  ui/                   # Shared React components
  shared-types/         # Generated TypeScript types
docs/
  architecture/         # System architecture docs
  ai-agent/             # Agent-oriented reference docs
specs/                  # OpenAPI spec, schema dumps
mise.toml               # Task runner config
docker-compose.yml      # Local dev services
nx.json                 # NX workspace config
```
[https://claude.ai/share/a45b37b3-3765-496d-9a7c-96cfe221112d
](https://docs.google.com/presentation/d/1I5tiGXp7dxXKWdgJCnxrRwT0I9SmF-ig/edit?usp=drivesdk&ouid=102060265013781988185&rtpof=true&sd=true)
