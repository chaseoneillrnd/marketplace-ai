---
name: quality-gate-builder
description: Use when adding quality checks to the CI/local quality gate
---

# Quality Gate Builder

## Run Locally

```bash
mise run quality-gate      # Full gate
mise run quality-gate:api  # API only
mise run quality-gate:web  # Web only
```

## What It Checks

1. `ruff check` — Python lint
2. `ruff format --check` — Python format
3. `mypy --strict` — Python types
4. `pytest --cov-fail-under=80` — Python coverage
5. `tsc --noEmit` — TypeScript types
6. `vitest --coverage` — TypeScript coverage

## Add a New Check

Add to the `quality-gate` task in `mise.toml`:
```toml
echo "=== New Check ==="
my-check-command || true
```

## CI Mirror

`.gitlab-ci.yml` runs the same checks in 5 stages: lint → test → typecheck → build → security.

## References

- mise.toml: quality-gate section
- .gitlab-ci.yml: all stages
