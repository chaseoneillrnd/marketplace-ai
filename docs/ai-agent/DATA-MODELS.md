# Data Models

23 tables across 5 domains. All UUIDs use `uuid4`. Timestamps use `DateTime(timezone=True)`.

## Domain: Identity

- `Division` — slug PK, name, color
- `User` — uuid PK, email UK, username UK, name, division FK, role, oauth_provider, oauth_sub, is_platform_team, is_security_team, last_login_at
- `OAuthSession` — uuid PK, user_id FK, provider, access_token_hash, expires_at

## Domain: Skill Core

- `Category` — slug PK, name, sort_order
- `Skill` — uuid PK, slug UK, name, short_desc, category FK, author_id FK, author_type, current_version, install_method, data_sensitivity, status, published_at, counters (install/fork/favorite/view/review_count, avg_rating, trending_score)
- `SkillVersion` — uuid PK, skill_id FK, version, content, frontmatter JSON, changelog, content_hash
- `SkillDivision` — composite PK (skill_id, division_slug)
- `SkillTag` — composite PK (skill_id, tag)
- `TriggerPhrase` — uuid PK, skill_id FK, phrase

## Domain: Social

- `Install` — uuid PK, skill_id FK, user_id FK, version, method, uninstalled_at
- `Fork` — uuid PK, original_skill_id FK, forked_skill_id FK, forked_by FK, upstream_version_at_fork
- `Favorite` — composite PK (user_id, skill_id)
- `Follow` — composite PK (follower_id, followed_user_id)
- `Review` — uuid PK, skill_id FK, user_id FK, rating, body, helpful_count, unhelpful_count
- `ReviewVote` — composite PK (review_id, user_id), vote
- `Comment` — uuid PK, skill_id FK, user_id FK, body, upvote_count, deleted_at
- `Reply` — uuid PK, comment_id FK, user_id FK, body, deleted_at
- `CommentVote` — composite PK (comment_id, user_id)

## Domain: Submission

Tables: `Submission`, `SubmissionGateResult`, `DivisionAccessRequest`. See [SUBMISSION-PIPELINE.md](SUBMISSION-PIPELINE.md).

## Domain: Platform

Tables: `FeatureFlag`, `AuditLog`. See [FEATURE-FLAGS.md](FEATURE-FLAGS.md).

## Seed Data

Source: `libs/db/scripts/seed_data.py` + `libs/db/scripts/seed.py`.

- **6 stub users** match `STUB_USERS` in `auth.py` via `uuid5(STUB_USER_NAMESPACE, username)` — deterministic IDs
- Additional seed users across all divisions for realistic data
- `SEED_INSTALLS` — real install rows with skill_slug, user_index, version, method, days_ago
- `SEED_FAVORITES` — real favorite rows with skill_slug, user_index
- Counters zeroed then reconciled from actual rows post-seed (`_reconcile_counters`)
- Bayesian rating recalculation runs during reconciliation
- `content_hash` uses SHA256: `hashlib.sha256(content.encode()).hexdigest()`

## Denormalized Counters

Updated in service layer (same transaction). Reconciled from real rows during seed.

## Audit Log Constraint

Append-only. Application code must only INSERT.

## Key Files

- `libs/db/skillhub_db/models/` — all model files
- `libs/db/skillhub_db/base.py` — `Base`, `UUIDMixin`, `TimestampMixin`
- `libs/db/scripts/seed_data.py` — seed data definitions
- `libs/db/scripts/seed.py` — seed runner + counter reconciliation
