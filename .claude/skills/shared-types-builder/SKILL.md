---
name: shared-types-builder
description: Use when generating or managing TypeScript types in libs/shared-types/
---

# Shared Types Builder

## Generate from OpenAPI

```bash
mise run gen:openapi  # FastAPI → specs/openapi.json
mise run gen:types    # openapi.json → libs/shared-types/src/api.generated.ts
```

## Manual Types

Add to `libs/shared-types/src/index.ts` for types not in OpenAPI spec.

## Import Pattern

```typescript
import type { SkillSummary, UserProfile } from '@skillhub/shared-types';
```

## References

- Package: `libs/shared-types/`
- Generated: `libs/shared-types/src/api.generated.ts`
- OpenAPI source: `specs/openapi.json`
