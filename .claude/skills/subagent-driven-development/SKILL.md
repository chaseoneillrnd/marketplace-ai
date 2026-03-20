---
name: subagent-driven-development
description: Use when executing implementation plans with multiple tasks. Dispatches fresh subagents per task with two-stage review (spec compliance then code quality) for high quality, fast iteration.
---

# Subagent-Driven Development

## Announcement

When this skill activates, say:
"I'm using the subagent-driven-development skill to execute the plan."

## Overview

Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

## Process

### 1. Extract Tasks
Read the plan. Extract ALL tasks upfront. Present the task list to the user.

### 2. For Each Task

```
LOOP per task:
  1. Dispatch IMPLEMENTER subagent (see implementer-prompt.md)
  2. Review implementer's report
  3. Dispatch SPEC REVIEWER subagent (see spec-reviewer-prompt.md)
  4. If spec issues found → re-dispatch implementer with fix instructions
  5. Dispatch CODE QUALITY REVIEWER subagent (see code-quality-reviewer-prompt.md)
  6. If quality issues found → re-dispatch implementer with fix instructions
  7. Both reviews pass → mark task complete, move to next
```

### 3. Model Selection

Assign models based on task complexity:
- **Mechanical tasks** (rename, move, simple CRUD): Use cheapest model
- **Standard implementation** (new features, integrations): Use standard model
- **Architecture/design review**: Use most capable model

Use the least powerful model that can handle each role to conserve cost and increase speed.

### 4. Implementer Prompt Template

```
Agent tool (general-purpose):
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N: [task name]

    ## Task Description
    [FULL TEXT of task from plan - paste it here, don't make subagent read file]

    ## Context
    [Scene-setting: where this fits, dependencies, architectural context]

    ## Your Job
    1. Implement exactly what the task specifies
    2. Write tests (following TDD if task says to)
    3. Verify implementation works
    4. Commit your work
    5. Self-review
    6. Report back

    ## Report Format
    - Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
    - What you implemented
    - What you tested and test results
    - Files changed
    - Self-review findings
    - Any issues or concerns
```

### 5. Spec Reviewer Prompt Template

```
Agent tool (general-purpose):
  description: "Review spec compliance for Task N"
  prompt: |
    You are reviewing whether an implementation matches its specification.

    ## What Was Requested
    [FULL TEXT of task requirements]

    ## CRITICAL: Do Not Trust the Report
    Read the actual code. Compare to requirements line by line.

    ## Report
    - ✅ Spec compliant
    - ❌ Issues found: [list with file:line references]
```

### 6. Code Quality Reviewer

After spec compliance passes, dispatch code quality review checking:
- Clean separation of concerns
- Proper error handling
- Type safety
- DRY principle
- Edge cases handled
- Tests actually verify behavior

## Red Flags — STOP

- Skipping reviews (spec compliance OR code quality)
- Proceeding with unfixed issues
- Starting quality review before spec compliance passes
- Implementer reporting BLOCKED but controller pushing forward
- Not re-reviewing after fixes

## When Tasks Fail

- BLOCKED: Provide more context or break into smaller tasks
- NEEDS_CONTEXT: Supply the missing information
- After 3 failed attempts: Escalate to user, do not brute force
