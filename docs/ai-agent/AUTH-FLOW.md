# Auth Flow

## Current: Multi-Identity Stub Auth

Dev/test only. 6 stub users, all with password `user`.

```
POST /auth/token  { "username": "<stub>", "password": "user" }
→ { "access_token": "<jwt>", "token_type": "bearer" }

GET /auth/dev-users → list of available stub users
```

Controlled by `STUB_AUTH_ENABLED`. Returns 403 when disabled.

### Stub Users

| Username | Division | Role | Platform | Security |
|---|---|---|---|---|
| `alice` | engineering-org | Staff Engineer | yes | no |
| `bob` | data-science-org | Senior Data Scientist | no | no |
| `carol` | security-org | Security Lead | no | yes |
| `dave` | product-org | Senior Product Manager | no | no |
| `admin` | engineering-org | Platform Lead | yes | yes |
| `test` | engineering-org | Senior Engineer | no | no |

UUIDs are deterministic: `uuid5(STUB_USER_NAMESPACE, username)`.

## Planned: OAuth

Providers: `microsoft`, `google`, `okta`, `github`, `oidc`. All return 501.

## JWT Claims

```json
{
  "user_id": "uuid",
  "sub": "uuid",
  "email": "alice@acme.com",
  "name": "Alice Chen",
  "username": "alice",
  "division": "engineering-org",
  "role": "Staff Engineer",
  "is_platform_team": true,
  "is_security_team": false,
  "iat": 1234567890,
  "exp": 1234567890
}
```

Algorithm: `HS256`. Secret: `JWT_SECRET` env var. Expiry: `JWT_EXPIRE_MINUTES`.

## Dependency Chain

```
Request → get_current_user → decode JWT → claims dict
  ├→ require_platform_team (is_platform_team=true or 403)
  └→ require_security_team (is_security_team=true or 403)
```

## Division Enforcement

Server-side in service functions. User's `division` JWT claim checked against `skill_divisions` table. No division rows = accessible to all. Never trust client-side filtering.

## Key Files

- `apps/api/skillhub/routers/auth.py` — auth endpoints + STUB_USERS registry
- `apps/api/skillhub/dependencies.py` — `get_current_user`, `require_platform_team`, `require_security_team`
- `apps/api/skillhub/config.py` — JWT settings
