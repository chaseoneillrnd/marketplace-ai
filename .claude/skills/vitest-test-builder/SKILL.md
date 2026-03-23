---
name: vitest-test-builder
description: Use when writing Vitest tests for the React frontend
---

# Vitest Test Builder

## Component Test

```tsx
import { render, screen } from '@testing-library/react';
import { SkillCard } from '../components/SkillCard';

test('renders skill name', () => {
  render(<SkillCard skill={mockSkill} />);
  expect(screen.getByText('PR Review')).toBeInTheDocument();
});
```

## Hook Test

```tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useSkills } from '../hooks/useSkills';

test('fetches skills', async () => {
  const { result } = renderHook(() => useSkills());
  await waitFor(() => expect(result.current.loading).toBe(false));
});
```

## API Mock

```tsx
vi.mock('../lib/api', () => ({
  api: { get: vi.fn().mockResolvedValue({ items: [], total: 0 }) }
}));
```

## Run

```bash
mise run test:web           # Run tests
mise run test:web:coverage  # With coverage
```

## References

- Tests: `apps/web/src/__tests__/`
- Config: `apps/web/vite.config.ts`
