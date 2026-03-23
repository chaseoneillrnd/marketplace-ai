---
name: admin-endpoint-builder
description: Use when building admin endpoints requiring platform_team or security_team roles
---

# Admin Endpoint Builder

## Auth Dependencies

```python
from skillhub.dependencies import require_platform_team, require_security_team

@router.post("/api/v1/admin/action", dependencies=[Depends(require_platform_team)])
def admin_action(db=Depends(get_db), user=Depends(get_current_user)):
    ...
```

## Existing Admin Endpoints

- POST /admin/submissions/{id}/review — Gate 3 human review
- POST /admin/skills/{slug}/feature — Set featured flag
- DELETE /admin/skills/{slug} — Emergency removal (Security Team)
- GET /admin/audit-log — Query audit entries

## References

- Admin router: `apps/api/skillhub/routers/admin.py`
- Admin service: `apps/api/skillhub/services/admin.py`
- Dependencies: `apps/api/skillhub/dependencies.py`
