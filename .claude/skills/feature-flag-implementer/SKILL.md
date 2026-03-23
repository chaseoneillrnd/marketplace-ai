---
name: feature-flag-implementer
description: Use when adding new feature flags or gating features behind flags
---

# Feature Flag Implementer

## Add a New Flag

1. Add seed in `libs/db/scripts/seed.py`:
```python
FeatureFlag(key="my_flag", enabled=False, description="...", division_overrides={})
```

2. Gate in API:
```python
flag = db.query(FeatureFlag).filter(FeatureFlag.key == "my_flag").first()
if not flag or not flag.enabled:
    # Check division override
    overrides = flag.division_overrides or {}
    if not overrides.get(user["division"], flag.enabled):
        raise HTTPException(403, "Feature not available")
```

3. Gate in React:
```tsx
import { useFlag } from '../hooks/useFlag';

function MyComponent() {
  const isEnabled = useFlag("my_flag");
  if (!isEnabled) return null;
  return <FeatureContent />;
}
```

## Division Overrides (JSONB)

```json
{"engineering-org": true, "marketing": false}
```

Override takes precedence over global `enabled` for matching division.

## Existing Flags

| Key | Default | Purpose |
|-----|---------|---------|
| llm_judge_enabled | false | Gate 2 LLM evaluation |
| mcp_install_enabled | true | MCP install flow |
| featured_skills_v2 | false | New featured algorithm |
| gamification_enabled | false | User stats and badges |

## References

- Flag model: `libs/db/skillhub_db/models/flags.py`
- Flag service: `apps/api/skillhub/services/flags.py`
- Flag router: `apps/api/skillhub/routers/flags.py`
- React hook: `apps/web/src/hooks/useFlag.ts`
