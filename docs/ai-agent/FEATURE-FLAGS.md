# Feature Flags

## Flag Keys

| Key | Default | Description |
|---|---|---|
| `llm_judge_enabled` | `false` | Enable LLM judge for submission Gate 2 |
| `featured_skills_v2` | `false` | Enable v2 featured skills layout |
| `gamification_enabled` | `false` | Enable gamification features |
| `mcp_install_enabled` | `true` | Enable MCP install method |

Seeded by `libs/db/scripts/seed.py`.

## Data Model

```
feature_flags
  key: VARCHAR(100) PK
  enabled: BOOLEAN
  description: TEXT
  division_overrides: JSON
```

## Division Overrides

`division_overrides` JSON column. Shape: `{ "engineering-org": true, "finance-legal": false }`.

Resolution: if user's division exists in overrides, use that value. Otherwise fall back to `enabled`.

## API Endpoint

```
GET /api/v1/flags
```

Auth: optional (division override applied if token present). Returns: `{ "flags": { "key": true, ... } }`.

## React Integration

### useFlag Hook

```typescript
const showV2 = useFlag('featured_skills_v2');
```

### Consumed In Components

- `SkillDetailView` — `mcp_install_enabled` gates MCP install option visibility
- `HomeView` — `featured_skills_v2` adds `data-featured-v2` attribute to featured section

### Context

`FlagsContext` fetches flags on mount, provides to tree.

## Key Files

- `libs/db/skillhub_db/models/flags.py` — `FeatureFlag` model
- `apps/api/skillhub/routers/flags.py` — flags endpoint
- `apps/api/skillhub/services/flags.py` — division override resolution
- `apps/web/src/context/FlagsContext.tsx` — React context
- `apps/web/src/hooks/useFlag.ts` — hook
- `apps/web/src/views/SkillDetailView.tsx` — mcp_install_enabled consumer
- `apps/web/src/views/HomeView.tsx` — featured_skills_v2 consumer
