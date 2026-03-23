---
name: mise-task-builder
description: Use when adding mise tasks in mise.toml
---

# Mise Task Builder

## Naming Convention

`namespace:task` — e.g., `test:api`, `lint:web`, `db:migrate`

## Task Pattern

```toml
[tasks."namespace:task"]
description = "What this task does"
run = "command here"
env = { PYTHONPATH = "apps/api:libs/db:libs/python-common" }
```

## Multi-Line

```toml
[tasks."my:task"]
run = """
echo "Step 1"
echo "Step 2"
"""
```

## Namespaces

dev, build, test, lint, format, typecheck, db, gen, docker, quality-gate, ci, docs, repo, security

## References

- mise.toml: project root (60+ tasks defined)
