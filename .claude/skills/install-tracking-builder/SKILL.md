---
name: install-tracking-builder
description: Use when implementing install/uninstall tracking
---

# Install Tracking Builder

## Install Record

```python
install = Install(
    skill_id=skill.id, user_id=user["user_id"],
    version=skill.current_version,
    method="web",  # or "mcp" or "manual"
    installed_at=datetime.utcnow(),
)
```

## Soft Uninstall

Set `uninstalled_at` instead of deleting. Preserves history.

## Division Gate

Check `user.division in skill.divisions` BEFORE creating install record.

## MCP Local Files

MCP install tool writes `~/.local/share/claude/skills/{slug}/SKILL.md`.

## Counter Update

`skill.install_count` = active installs (where `uninstalled_at IS NULL`).

## References

- Social router: `apps/api/skillhub/routers/social.py`
- Install model: `libs/db/skillhub_db/models/social.py`
- MCP install: `apps/mcp-server/skillhub_mcp/tools/install.py`
