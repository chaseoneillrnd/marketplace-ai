---
name: openapi-spec-manager
description: Use when generating or managing the OpenAPI spec and TypeScript types
---

# OpenAPI Spec Manager

## Generate

```bash
mise run gen:openapi    # FastAPI → specs/openapi.json
mise run gen:types      # openapi.json → libs/shared-types/src/api.generated.ts
```

## Freshness Check (CI)

`.gitlab-ci.yml` compares generated spec against committed spec. Fails if stale.

## Swagger UI

Available at `http://localhost:8000/docs` when API is running.

## References

- Spec: `specs/openapi.json`
- Types: `libs/shared-types/src/api.generated.ts`
- Generator tasks: `mise.toml` (gen:openapi, gen:types)
