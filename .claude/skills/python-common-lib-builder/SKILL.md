---
name: python-common-lib-builder
description: Use when building shared Python utilities in libs/python-common/
---

# Python Common Lib Builder

## Purpose

Shared utilities for apps/api and apps/mcp-server. Avoids duplication.

## Planned Modules

- `skillhub_common.auth` — JWT helpers, token validation
- `skillhub_common.logging` — Structured JSON logging setup
- `skillhub_common.exceptions` — Custom exception hierarchy
- `skillhub_common.config` — Base settings class

## Import Pattern

```python
from skillhub_common.auth import validate_jwt
from skillhub_common.logging import get_logger
```

## PYTHONPATH

All mise tasks include: `PYTHONPATH = "libs/python-common"`

## References

- Package: `libs/python-common/skillhub_common/`
- Used by: apps/api, apps/mcp-server, libs/db
