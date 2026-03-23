---
name: env-config-manager
description: Use when managing environment variables and configuration
---

# Environment Config Manager

## Source of Truth

`.env.example` documents all variables. `.env` is gitignored.

## Pydantic Settings

```python
# apps/api/skillhub/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    STUB_AUTH_ENABLED: bool = True
    LLM_ROUTER_URL: str = ""
```

## Frontend Variables

Prefix with `VITE_` for Vite exposure: `VITE_API_URL=http://localhost:8000`

## Docker Compose

Variables injected via `environment:` block with `${VAR:-default}` syntax.

## Rule

No secrets in code. All via Settings. `.env` never committed.

## References

- .env.example: project root
- Config: `apps/api/skillhub/config.py`
- docker-compose.yml: project root
