# PRIORITIES — SkillHub

> Current priorities with defense. Updated 2026-03-21.

## P0 — Must complete now

1. **Stage 10: Documentation & CI finalization**
   - Why: Codebase undocumented. New devs can't onboard. CI not fully green.
   - Defense: 9 stages of code exist with no agent docs, no README, no Repo Master.

2. **Test coverage hardening**
   - Why: 80% gate exists but not verified across all paths. High-value features need defensible coverage.
   - Defense: Social layer, submissions, MCP tools need edge case coverage.

## P1 — Next sprint

3. **libs/python-common extraction**
   - Why: Auth, logging, exceptions duplicated across api and mcp-server.
   - Defense: DRY violation. Bug in one copy won't be fixed in other.

4. **OpenAPI spec + TypeScript type generation**
   - Why: Frontend types manually maintained. Drift risk.
   - Defense: Single source of truth prevents contract violations.

## P2 — Planned

5. **Production OAuth integration**
   - Why: Stub auth is dev-only. Can't deploy without real SSO.
   - Defense: Security requirement. Division claims must come from identity provider.

6. **Admin UI panel**
   - Why: Admin routes exist but no UI. Platform Team uses curl/Swagger.
   - Defense: Operational overhead. Human review queue needs a proper interface.
