---
name: division-access-enforcer
description: Use when implementing division-based access control on any endpoint
---

# Division Access Enforcer

## Core Rule

Division enforcement happens in Flask (before_request) — NEVER client-side.

## Enforcement Pattern

```python
from flask import Blueprint, g, abort
from skillhub_flask.db import get_db

bp = Blueprint("skills_install", __name__)

@bp.route("/api/v1/skills/<slug>/install", methods=["POST"])
def install_skill(slug: str):
    db = get_db()
    user = g.current_user

    skill = db.query(Skill).filter(Skill.slug == slug).first()
    if not skill:
        abort(404, description="Skill not found")

    user_division = user["division"]
    authorized = [sd.division_slug for sd in skill.divisions]

    if user_division not in authorized:
        # Log the denial
        audit_log(db, "access.denied", user["user_id"], "skill", skill.id,
                  {"division": user_division, "required": authorized})
        abort(403, description="Division not authorized for this skill")
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

- Auth (before_request): `apps/api/skillhub_flask/blueprints/auth.py`
- Social blueprint: `apps/api/skillhub_flask/blueprints/social.py`
- Audit model: `libs/db/skillhub_db/models/audit.py`
