# Guide Context Note

**Date:** 2026-03-23
**Status:** Active

## Key Clarification

This is a **greenfield PoC application** — no users have access to the code yet. The backend
is being ported to Flask for a demo. This means:

- **No canary deployment needed** — no live traffic to protect
- **No backwards compatibility required** — no consumers to break
- **No coexistence period** — FastAPI can be deleted after porting
- **Phase 5 (cutover guide) is largely unnecessary** — simple swap, not gradual ramp
- **Phase 4 Task 4.8 (canary infra) is unnecessary** — no nginx dual-service

## Design Priority

When there's a conflict between "backwards compatible with FastAPI behavior" and
"Flask best practices," **always favor Flask best practices**.

## Guides Affected

- `phase4-admin-canary-guide.md` — Task 4.8 (canary) can be skipped
- `phase5-cutover-guide.md` — Mostly unnecessary; just delete FastAPI and update configs
- All guides — any decision favoring backwards compat should be reconsidered
