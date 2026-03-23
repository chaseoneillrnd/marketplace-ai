---
name: pre-commit-hook-builder
description: Use when adding pre-commit hooks to .pre-commit-config.yaml
---

# Pre-Commit Hook Builder

## Current Hooks

- ruff (lint + format) for Python
- eslint for TypeScript
- prettier for formatting
- commitizen for commit messages

## Add Hook

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/my/hook
  rev: v1.0.0
  hooks:
    - id: my-hook
      files: '\.(py|ts)$'
```

## References

- Config: `.pre-commit-config.yaml`
- Install: `pre-commit install`
