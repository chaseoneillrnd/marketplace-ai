---
name: oauth-flow-implementer
description: Use when implementing OAuth provider flows for production auth
---

# OAuth Flow Implementer

## Flow

1. `GET /auth/oauth/{provider}` → returns redirect URL + state
2. User authenticates with provider
3. `GET /auth/oauth/{provider}/callback?code=...&state=...`
4. API exchanges code for tokens, extracts userinfo
5. Upsert user, issue SkillHub JWT

## Provider Config (.env)

```
OAUTH_MICROSOFT_CLIENT_ID=...
OAUTH_MICROSOFT_CLIENT_SECRET=...
OAUTH_MICROSOFT_TENANT_ID=...
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GITHUB_CLIENT_ID=...
```

## Claim Mapping

Extract from provider's userinfo:
- `email` → users.email
- `name` → users.name
- `division` → from org claim or group membership
- `role` → from role claim

## JWT Issuance

```python
payload = {
    "user_id": str(user.id), "email": user.email,
    "name": user.name, "division": user.division,
    "role": user.role, "is_platform_team": user.is_platform_team,
    "exp": datetime.utcnow() + timedelta(hours=8)
}
token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
```

## References

- Auth router: `apps/api/skillhub/routers/auth.py`
- Config: `apps/api/skillhub/config.py`
- .env.example: project root
