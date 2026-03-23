# Database Architecture

PostgreSQL 16. 23 tables across 5 domains. Managed by Alembic.

## Domains

### Identity (3 tables)
- `divisions` — PK: `slug`. Org units with name + color.
- `users` — PK: `id` (UUID). FK to `divisions.slug`. Unique on email, username.
- `oauth_sessions` — PK: `id`. FK to `users.id`. Stores hashed tokens only.

### Skill Core (6 tables)
- `categories` — PK: `slug`. Skill categories with sort order.
- `skills` — PK: `id`. FK to `categories.slug`, `users.id`. Unique on slug. Contains denormalized counters.
- `skill_versions` — PK: `id`. FK to `skills.id`. Versioned content + frontmatter. Indexed on `content_hash`.
- `skill_divisions` — Composite PK: `(skill_id, division_slug)`. Access control.
- `skill_tags` — Composite PK: `(skill_id, tag)`.
- `trigger_phrases` — PK: `id`. FK to `skills.id`.

### Social (9 tables)
- `installs` — PK: `id`. Soft-deletable via `uninstalled_at`.
- `forks` — PK: `id`. Links `original_skill_id` -> `forked_skill_id`.
- `favorites` — Composite PK: `(user_id, skill_id)`.
- `follows` — Composite PK: `(follower_id, followed_user_id)`.
- `reviews` — PK: `id`. UNIQUE on `(skill_id, user_id)`. Denormalized vote counts.
- `review_votes` — Composite PK: `(review_id, user_id)`. Enum: helpful/unhelpful.
- `comments` — PK: `id`. Soft-deletable via `deleted_at`.
- `replies` — PK: `id`. FK to `comments.id`. Soft-deletable.
- `comment_votes` — Composite PK: `(comment_id, user_id)`.

### Submission (3 tables)
- `submissions` — PK: `id`. Unique `display_id` (human-friendly). Status enum with 10 states.
- `submission_gate_results` — PK: `id`. FK to `submissions.id`. Gate number + result + findings JSON.
- `division_access_requests` — PK: `id`. Status: pending/approved/denied.

### Platform (2 tables)
- `feature_flags` — PK: `key`. Boolean `enabled` + JSON `division_overrides`.
- `audit_log` — PK: `id`. Append-only (DB trigger blocks UPDATE/DELETE).

## Key Constraints

- All UUIDs via `uuid4`, mixed in via `UUIDMixin`
- All timestamps via `TimestampMixin` (created_at, updated_at with `server_default=func.now()`)
- CASCADE deletes on all skill-related FKs
- `reviews` UNIQUE on `(skill_id, user_id)` prevents duplicate reviews

## Migration Strategy

- Single migration file: `libs/db/migrations/versions/001_initial_schema.py`
- Run: `mise run db:migrate` (wraps `alembic upgrade head`)
- Rollback: `mise run db:rollback`
- Generate: `mise run db:make-migration`
- Check: `mise run db:check`
- Config: `libs/db/alembic.ini`

## Seed Data

`libs/db/scripts/seed.py` — idempotent. Seeds: 8 divisions, 9 categories, 4 feature flags, 1 stub user. All use `ON CONFLICT DO NOTHING`.
