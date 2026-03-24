# SkillHub — Claude Code Configuration

## Project Overview

Internal AI skills marketplace (SkillHub) enabling org-wide Claude skill sharing.
Built as an NX monorepo with Flask/APIFlask backend, React frontend, and MCP server.

## Tech Stack

- **Frontend:** React 18 + Vite + TypeScript
- **Backend:** Flask/APIFlask (Python 3.12) + SQLAlchemy 2 + Alembic
- **MCP Server:** Python + mcp SDK
- **Database:** PostgreSQL 16 + Redis 7
- **Monorepo:** NX + mise
- **Testing:** pytest + Vitest (coverage gates ≥80%)
- **Lint/Format:** ruff + eslint + prettier

## Architecture

```
apps/web → libs/ui, libs/shared-types
apps/api → libs/db, libs/python-common
apps/mcp-server → libs/python-common
libs/db → libs/python-common
```

Rules:
- No circular dependencies
- apps/* never import from other apps/*
- libs/* never import from apps/*

## Code Quality Standards

- Python: ruff (lint + format), mypy --strict, no type: ignore without comment
- TypeScript: eslint, prettier, tsc --noEmit clean
- No commented-out code committed
- No print() / console.log() in production paths — use structured logging
- TDD: write tests FIRST, then implementation
- Python coverage gate: ≥80% (pytest-cov --cov-fail-under=80)
- TypeScript coverage gate: ≥80% (vitest --coverage)

## Security

- No secrets in code — all via Settings (pydantic-settings)
- JWT: decode before trusting, never trust raw claims without verification
- Division enforcement happens server-side (Flask before_request) — never client-side
- audit_log: append-only, no UPDATE/DELETE from application code

## Design Documents

- `skillhub-design.md` — Approved design document
- `skillhub-technical-guide.md` — Complete implementation guide (29 prompts across 11 stages)
- `skillhub-diagrams.md` — Visual architecture companion with Mermaid diagrams

## Development Workflow

This project uses the **superpowers** skills framework from https://github.com/obra/superpowers.
Skills are installed in `.claude/skills/` and guide structured development.

### Workflow Stages
1. **Brainstorming** — Refine ideas through Socratic dialogue
2. **Writing Plans** — Break work into 2-5 minute tasks with TDD
3. **Subagent-Driven Development** — Fresh agents per task with two-stage review
4. **Test-Driven Development** — RED-GREEN-REFACTOR cycle enforced
5. **Code Review** — Reviews against plan, issues by severity
6. **Verification Before Completion** — Evidence before assertions always

### Key Commands
- `mise run install` — Full setup
- `mise run dev:api` — Start API server
- `mise run dev:web` — Start web dev server
- `mise run dev:mcp` — Start MCP server
- `mise run test:api` — Run API tests
- `mise run test:web` — Run web tests
- `mise run quality-gate` — Full CI gate locally
- `mise run db:migrate` — Run database migrations
- `mise run db:seed` — Seed database
