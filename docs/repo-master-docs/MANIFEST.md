# MANIFEST — SkillHub

> Perusal index. Under 50 lines. Enables instant GO/NO-GO/SUMMON.
> Last updated: 2026-03-22

## Status: ACTIVE — 21 audit fixes applied. E2E validated. 550 API + 84 MCP + 76 frontend tests pass.

## Feature State

| Area | Confidence | Status | Action |
|------|-----------|--------|--------|
| Database (23 tables) | 95% | GO | Seed data reconciled. Counters match real rows. |
| Skills API (browse/search) | 95% | GO | Full CRUD + author/days_ago in user collections. |
| Auth (stub + JWT) | 80% | GO | 6 multi-identity dev users. OAuth still 501. |
| Social (install/review/fork) | 90% | GO | Fork fixed. View count isolated. Counters atomic. |
| Submissions (3-gate) | 85% | GO | Async Gate 2. Auto-trigger. Jaccard dupe check. published_at set. |
| MCP Server (9 tools) | 90% | GO | All filter params. PATCH method. Real API calls. |
| React Frontend (5 views) | 85% | GO | Reviews tab live. Flags wired. State synced from API. |
| Feature Flags | 80% | GO | mcp_install + featured_v2 gate components. useFlag consumed. |
| Admin Routes | 85% | GO | User mgmt + submission queue + audit log. |
| Repo Master Docs | 80% | GO | Updated post-fleet. 7 AI agent docs current. |
| OAuth Production | 15% | SUMMON | Stubs only. Multi-identity dev auth proves pipeline. |

## Priorities (current)

1. Test coverage verification — confirm 80%+ gate across all apps
2. End-to-end validation — seed, browse, install, review, fork flow
3. libs/python-common extraction — shared auth, logging, exceptions
4. OpenAPI spec generation + type codegen

## Recent Decisions

- 2026-03-22: Fleet remediation complete. 21 fixes, 550+76 tests green. Confidence restored.
- 2026-03-22: Council audit downgraded confidence across 8 areas. Fleet dispatched.
- 2026-03-21: Bootstrapped governance docs, codebase map generated
