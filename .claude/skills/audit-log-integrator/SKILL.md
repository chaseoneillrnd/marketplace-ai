---
name: audit-log-integrator
description: Use when adding audit log entries for any mutation or security event
---

# Audit Log Integrator

## Core Rule

Audit log is append-only. No UPDATE or DELETE from application code. PostgreSQL trigger enforces this.

## Log Pattern

```python
from libs.db.skillhub_db.models.audit import AuditLog

def audit_log(db, event_type, actor_id, target_type, target_id, metadata=None, ip=None):
    entry = AuditLog(
        event_type=event_type,
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata or {},
        ip_address=ip,
    )
    db.add(entry)
```

## Event Type Convention

`{domain}.{action}` — examples:
- `skill.installed`, `skill.uninstalled`, `skill.forked`
- `skill.favorited`, `skill.unfavorited`
- `review.created`, `review.updated`
- `submission.created`, `submission.gate1_passed`
- `admin.skill_featured`, `admin.skill_removed`
- `access.denied`, `access.requested`, `access.granted`

## Metadata JSONB

Include context needed for audit trail:
```json
{"version": "2.3.1", "method": "mcp", "division": "engineering-org"}
```

## Query Pattern (Admin)

```python
@router.get("/api/v1/admin/audit-log")
def get_audit_log(event_type: str = None, target_type: str = None, ...):
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if event_type: query = query.filter(AuditLog.event_type == event_type)
```

## References

- Model: `libs/db/skillhub_db/models/audit.py`
- Admin router: `apps/api/skillhub/routers/admin.py`
- Social (usage): `apps/api/skillhub/services/social.py`
