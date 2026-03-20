---
name: finishing-a-development-branch
description: Use when all tasks in a plan are complete — verifies tests, determines base branch, presents merge/PR/keep/discard options.
---

# Finishing a Development Branch

## Announcement

"I'm using the finishing-a-development-branch skill to complete this work."

## Process

1. **Verify tests pass** — Run full test suite, confirm green
2. **Determine base branch** — What branch did we branch from?
3. **Present options:**
   - Merge locally — integrate, verify, delete feature branch
   - Push and create PR — push branch, open PR for review
   - Keep as-is — preserve branch for later
   - Discard — permanently delete (requires typed confirmation: 'discard')

## Rules

- Always verify tests before offering options
- Never proceed with failing tests
- Discard requires explicit typed confirmation
- Worktree cleanup only for merge and discard options
