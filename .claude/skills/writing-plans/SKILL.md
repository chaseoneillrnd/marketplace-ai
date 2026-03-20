---
name: writing-plans
description: Use when breaking down features or tasks into implementation plans with exact file paths, TDD steps, and verification commands for 2-5 minute tasks.
---

# Writing Plans

## Announcement

When this skill activates, say:
"I'm using the writing-plans skill to create the implementation plan."

## Plan Location

Save plans to: `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`

## Plan Structure

### Header
- Feature name and goal
- Architecture overview
- Tech stack and dependencies
- File structure (all files mapped upfront)

### Tasks

Break work into 2-5 minute actions following TDD:
1. Write failing test
2. Run test (see RED)
3. Implement minimal code
4. Run test (see GREEN)
5. Refactor if needed
6. Commit

### Task Format

Each task specifies:
- Exact file paths
- Complete code snippets (not pseudocode)
- Precise commands with expected outputs
- Step-by-step checkboxes
- Verification command

## File Structure Principles

- Map ALL files upfront with clear responsibilities
- Each file: one clear responsibility, well-defined interface
- Prefer focused files over monolithic ones
- Follow existing codebase patterns

## Quality Assurance

After writing the plan:
1. Dispatch plan-document-reviewer subagent for validation
2. Fix issues and re-review if needed (max 3 iterations)
3. Present to user for approval

## After Approval

Offer two execution paths:
1. **Subagent-driven** (recommended): Fresh agent per task
2. **Inline execution**: Using the executing-plans skill

## Core Philosophy

DRY, YAGNI, TDD, frequent commits. Clear boundaries and well-defined interfaces.
