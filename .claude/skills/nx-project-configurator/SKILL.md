---
name: nx-project-configurator
description: Use when configuring NX monorepo projects and dependency rules
---

# NX Project Configurator

## Dependency Rules

1. apps/* NEVER import from other apps/*
2. libs/* NEVER import from apps/*
3. apps/web → libs/ui, libs/shared-types
4. apps/api → libs/db, libs/python-common
5. apps/mcp-server → libs/python-common
6. libs/db → libs/python-common

## Workspace Layout

```json
// nx.json
{
  "targetDefaults": {
    "build": { "dependsOn": ["^build"] },
    "test": { "dependsOn": ["build"] }
  }
}
```

## Root package.json Workspaces

```json
{
  "workspaces": ["apps/web", "libs/ui", "libs/shared-types"]
}
```

## Adding a New Project

1. Create directory under apps/ or libs/
2. Add package.json or pyproject.toml
3. Verify: `npx nx graph` shows correct dependencies
4. Add to workspace array if TypeScript

## References

- nx.json: project root
- package.json: project root
- tsconfig.base.json: project root
