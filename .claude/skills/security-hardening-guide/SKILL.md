---
name: security-hardening-guide
description: Use when reviewing or implementing security measures
---

# Security Hardening Guide

## JWT Validation

Always decode before trusting. Never trust raw claims.
```python
payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
```

## Division Enforcement

Server-side only. Never client-side.
```python
if user["division"] not in authorized_divisions:
    raise HTTPException(403, "Division not authorized")
```

## SQL Injection Prevention

SQLAlchemy parameterizes all queries automatically. NEVER use f-strings in queries.

## XSS Prevention

React escapes by default. Never use `dangerouslySetInnerHTML`.

## CORS

```python
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], ...)
```

## Audit Log

Append-only. PostgreSQL trigger blocks UPDATE/DELETE on audit_log table.

## Secrets

All via pydantic-settings. Never in code. `.env` not committed.

## SAST Scanning

```bash
mise run security:scan  # Runs bandit on Python code
mise run security:audit # Runs npm audit
```

## References

- Dependencies: `apps/api/skillhub/dependencies.py`
- Config: `apps/api/skillhub/config.py`
- .env.example: project root
- CI security stage: `.gitlab-ci.yml`
