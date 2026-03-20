---
name: brainstorming
description: Use when starting new features, exploring ideas, or refining requirements — guides structured Socratic dialogue before any implementation.
---

# Brainstorming

## Hard Gate

NO code, scaffolding, or implementation until design is presented and user-approved.

## Process

1. **Explore context** — Review existing files, docs, recent changes
2. **Ask clarifying questions** — One at a time, multiple choice preferred
3. **Propose 2-3 approaches** — With trade-offs and recommendation
4. **Present design sections** — With approval checkpoints after each
5. **Write design document** — Save to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
6. **Spec review loop** — Use spec-document-reviewer subagent (max 3 iterations)
7. **User review gate** — Ask user to approve the written spec
8. **Invoke writing-plans skill** — The only skill invoked after brainstorming

## Principles

- One question per message
- Multiple choice preferred over open-ended
- YAGNI ruthlessly — eliminate unnecessary features
- Follow existing code conventions
- Break systems into focused units with clear interfaces

## Terminal State

Invoking writing-plans skill signals brainstorming completion.
