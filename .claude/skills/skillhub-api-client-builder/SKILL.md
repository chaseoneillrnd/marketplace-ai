---
name: skillhub-api-client-builder
description: Use when adding new API functions to the frontend client
---

# SkillHub API Client Builder

## Pattern (apps/web/src/lib/api.ts)

```typescript
export const api = {
  async get(url: string, opts?: { params?: Record<string, string> }) {
    const token = getToken();
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return handleResponse(res);
  },

  async post(url: string, body: unknown) {
    const token = getToken();
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  },
};
```

## Error Handling

- 401 → `clearToken()` + reload (auto-logout)
- 403 → "Access denied" error
- 404 → "Not found" error

## References

- API client: `apps/web/src/lib/api.ts`
- Auth: `apps/web/src/lib/auth.ts`
