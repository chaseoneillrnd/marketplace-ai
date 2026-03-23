---
name: react-view-builder
description: Use when creating new React views in apps/web/src/views/
---

# React View Builder

## Checklist

1. Create view in `apps/web/src/views/{Name}View.tsx`
2. Add route in `apps/web/src/App.tsx`
3. Wire API calls via `apps/web/src/lib/api.ts`
4. Add loading/error/empty states
5. Create tests in `apps/web/src/__tests__/{Name}View.test.tsx`

## View Pattern

```tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { api } from '../lib/api';

export function MyView() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get('/api/v1/endpoint')
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonCard />;
  if (error) return <ErrorState onRetry={...} />;
  if (!data?.length) return <EmptyState />;

  return <div>{/* content */}</div>;
}
```

## State Patterns

- Loading: `SkeletonCard` component
- Error: Retry button
- Empty: "No results" with clear-filters CTA
- Auth-gated: Check `useAuth().user` before rendering

## References

- HomeView: `apps/web/src/views/HomeView.tsx`
- API client: `apps/web/src/lib/api.ts`
- Auth hook: `apps/web/src/hooks/useAuth.ts`
- Components: `apps/web/src/components/`
