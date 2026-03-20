---
name: executing-plans
description: Use when implementing a written development plan step-by-step in a single session with built-in review checkpoints.
---

# Executing Plans

## Process

### Step 1: Load and Review
Read plan file. Review critically — identify questions or concerns before execution.
Raise concerns with your partner rather than proceeding.

### Step 2: Execute Tasks
For each task:
1. Mark progress
2. Follow steps precisely
3. Run specified verifications
4. Mark completion

### Step 3: Complete Development
After all tasks, invoke finishing-a-development-branch skill.

## Critical Stopping Points

STOP immediately when encountering:
- Missing dependencies
- Test failures
- Unclear instructions
- Unexpected behavior

Ask for clarification rather than guessing. Don't force through blockers.

## Rules

- Set up isolated workspace using git-worktrees before starting
- Never begin on main/master without explicit consent
- Follow plan steps exactly
- Don't skip verifications
- Use subagent-driven-development instead if platform supports subagents
