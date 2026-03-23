---
name: fork-system-builder
description: Use when working with the skill fork system
---

# Fork System Builder

## Fork Creation

Creates new Skill with `status=draft`, links via forks table.

```python
fork = Fork(
    original_skill_id=original.id,
    forked_skill_id=new_skill.id,
    forked_by=user["user_id"],
    upstream_version_at_fork=original.current_version,
)
```

## Upstream Tracking

`upstream_version_at_fork` enables diff detection against newer upstream versions.

## Denormalized Counter

`original.fork_count += 1` on fork creation.

## References

- Social router: `apps/api/skillhub/routers/social.py`
- Fork model: `libs/db/skillhub_db/models/social.py`
- MCP fork tool: `apps/mcp-server/skillhub_mcp/tools/fork.py`
