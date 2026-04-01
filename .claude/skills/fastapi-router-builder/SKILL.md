---
name: flask-blueprint-builder
description: Use when creating new Flask blueprints in apps/api/skillhub_flask/blueprints/
---

# Flask Blueprint Builder

## Checklist

1. Create blueprint file in `apps/api/skillhub_flask/blueprints/{name}.py`
2. Create schemas in `apps/api/skillhub/schemas/{name}.py`
3. Create service in `apps/api/skillhub/services/{name}.py`
4. Register blueprint in `apps/api/skillhub_flask/app.py`
5. Create tests in `apps/api/tests/test_{name}.py`

## Blueprint Pattern

```python
from flask import Blueprint, g, jsonify
from skillhub_flask.db import get_db

bp = Blueprint("{name}", __name__, url_prefix="/api/v1/{name}")

@bp.route("/", methods=["GET"])
def list_items():
    db = get_db()
    user = g.current_user
    return jsonify(service.list_items(db, user))
```

## Registration in app.py

```python
from skillhub_flask.blueprints import {name}
app.register_blueprint({name}.bp)
```

## Service Layer Pattern

- Accept `db: Session` as first param
- Use `abort(status_code, description=...)` for errors
- Write audit_log entries for mutations
- Use eager loading to prevent N+1

## References

- Existing blueprint: `apps/api/skillhub_flask/blueprints/skills.py`
- Service pattern: `apps/api/skillhub/services/skills.py`
- Auth (before_request): `apps/api/skillhub_flask/blueprints/auth.py`
- Schemas: `apps/api/skillhub/schemas/skill.py`
