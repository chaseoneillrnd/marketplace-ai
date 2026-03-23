---
name: division-access-enforcer
description: Use when implementing division-based access control on any endpoint
---

# Division Access Enforcer

## Core Rule

Division enforcement happens in FastAPI — NEVER client-side.

## Enforcement Pattern

```python
from fastapi import HTTPException, Depends
from skillhub.dependencies import get_current_user, get_db

@router.post("/api/v1/skills/{slug}/install")
def install_skill(slug: str, db=Depends(get_db), user=Depends(get_current_user)):
    skill = db.query(Skill).filter(Skill.slug == slug).first()
    if not skill:
        raise HTTPException(404, "Skill not found")

    user_division = user["division"]
    authorized = [sd.division_slug for sd in skill.divisions]

    if user_division not in authorized:
        # Log the denial
        audit_log(db, "access.denied", user["user_id"], "skill", skill.id,
                  {"division": user_division, "required": authorized})
        raise HTTPException(403, "Division not authorized for this skill")
```

## Access Request Workflow

1. User POST `/api/v1/skills/{slug}/access-request` with reason
2. Platform Team reviews: POST `/api/v1/admin/access-requests/{id}/review`
3. If approved: INSERT into skill_divisions
4. Audit log entry for both request and decision

## JWT Claims

```json
{"user_id": "uuid", "email": "...", "division": "engineering-org", "role": "Senior Engineer",
 "is_platform_team": false, "is_security_team": false}
```

## References

- Dependencies: `apps/api/skillhub/dependencies.py`
- Social router: `apps/api/skillhub/routers/social.py`
- Audit model: `libs/db/skillhub_db/models/audit.py`
