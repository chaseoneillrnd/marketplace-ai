---
name: webhook-builder
description: Use when building webhook or notification patterns
---

# Webhook Builder

## Event Sources

Audit log serves as event source. Every mutation creates an audit_log entry with `event_type`.

## Notification Patterns (future)

- Follow notifications: new skill from followed author
- Submission status changes: gate passed/failed
- Division access granted

## Event Types

`skill.installed`, `skill.forked`, `review.created`, `submission.gate2_passed`, `access.granted`

## References

- Audit log: `libs/db/skillhub_db/models/audit.py`
- Social service: `apps/api/skillhub/services/social.py`
