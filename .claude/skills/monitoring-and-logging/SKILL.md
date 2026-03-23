---
name: monitoring-and-logging
description: Use when implementing structured logging, health checks, or observability
---

# Monitoring and Logging

## Structured Logging

```python
import logging
logger = logging.getLogger(__name__)
logger.info("skill_installed", extra={"skill_id": str(skill.id), "user_id": str(user.id)})
```

No `print()` in production paths. Use structured logging.

## Health Endpoint

`GET /health` → `{"status": "ok", "version": "1.0.0"}`

## Audit Log as Activity Monitor

Query `audit_log` for recent activity:
```sql
SELECT event_type, COUNT(*) FROM audit_log
WHERE created_at > now() - interval '1 hour'
GROUP BY event_type;
```

## Connection Health

- PostgreSQL: health check in docker-compose (`pg_isready`)
- Redis: health check (`redis-cli ping`)

## References

- Health router: `apps/api/skillhub/routers/health.py`
- Audit model: `libs/db/skillhub_db/models/audit.py`
- Docker: `docker-compose.yml` (health checks)
