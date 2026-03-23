---
name: react-hook-builder
description: Use when creating custom React hooks in apps/web/src/hooks/
---

# React Hook Builder

## Data Fetching Hook

```tsx
// apps/web/src/hooks/useMyData.ts
import { useState, useEffect } from 'react';
import { api } from '../lib/api';

export function useMyData(params?: Record<string, string>) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    api.get('/api/v1/endpoint', { params })
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [JSON.stringify(params)]);

  return { data, loading, error };
}
```

## Existing Hooks

| Hook | File | Purpose |
|------|------|---------|
| useAuth | hooks/useAuth.ts | Auth state + login/logout |
| useFlag | hooks/useFlag.ts | Feature flag checking |
| useSkills | hooks/useSkills.ts | Skills data fetching |

## Testing Hooks

```tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useMyData } from '../hooks/useMyData';

test('fetches data', async () => {
  const { result } = renderHook(() => useMyData());
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(result.current.data).toBeDefined();
});
```

## References

- Auth hook: `apps/web/src/hooks/useAuth.ts`
- API client: `apps/web/src/lib/api.ts`
