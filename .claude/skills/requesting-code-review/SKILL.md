---
name: requesting-code-review
description: Use after completing tasks in subagent-driven development, after finishing major features, and before merge to main.
---

# Requesting Code Review

## When to Request

**Mandatory:**
- After completing tasks in subagent-driven development
- After finishing major features
- Before merge to main

**Optional:**
- When stuck on approach
- Before refactoring

## Process

1. Obtain git commits: `git rev-parse` for base and head
2. Dispatch code-reviewer subagent with template
3. Address feedback by severity:
   - **Critical**: Fix immediately
   - **Important**: Resolve before proceeding
   - **Minor**: Note for later

## Core Philosophy

Review early, review often. Keep reviewers focused on work product.

## Red Flags

- Skipping reviews for "simple" changes
- Ignoring critical findings
- Proceeding with unfixed important issues
- Dismissing valid feedback without technical reasoning
