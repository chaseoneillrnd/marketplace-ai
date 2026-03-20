---
name: using-git-worktrees
description: Use when starting feature development to create isolated workspaces on new branches with clean test baselines.
---

# Using Git Worktrees

## Directory Selection Priority

1. Check for existing `.worktrees/` or `worktrees/` directory
2. Review CLAUDE.md for preferences
3. Ask user if neither exists

## Safety

MUST verify directory is ignored before creating worktree:
```bash
git check-ignore <path>
```
If not ignored, add to .gitignore and commit first.

## Setup Process

1. Create worktree on new branch
2. Detect project type (Node.js, Rust, Python, Go)
3. Run appropriate dependency installation
4. Run baseline tests to ensure clean start

## Rules

- Never skip ignore verification for project-local directories
- Always verify clean test baselines
- Follow established directory priority
