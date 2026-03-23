# Social Features

All social endpoints under `/api/v1/skills/{slug}/`. All require auth except reviews/comments listing.

## Actions

### Install
- `POST /{slug}/install` — body: `{ method, version }`
- `DELETE /{slug}/install` — soft delete (sets `uninstalled_at`)
- Division enforcement: JWT `division` checked against `skill_divisions`

### Favorite
- `POST /{slug}/favorite` — idempotent upsert
- `DELETE /{slug}/favorite` — remove
- Composite PK: `(user_id, skill_id)`

### Fork
- `POST /{slug}/fork`
- Creates new Skill row + Fork record + copies SkillVersion (single insert)
- Records `upstream_version_at_fork` for diff tracking

### Follow
- `POST /{slug}/follow` — follows skill's author (not the skill)
- `DELETE /{slug}/follow` — unfollow
- Idempotent upsert

### Review
- `GET /{slug}/reviews` — paginated, sorted by `helpful_count` DESC
- `POST /{slug}/reviews` — one per user per skill (409 on duplicate)
- `PATCH /{slug}/reviews/{id}` — owner only
- `POST /{slug}/reviews/{id}/vote` — `helpful` or `unhelpful`

### Comment
- `GET /{slug}/comments` — paginated with nested replies
- `POST /{slug}/comments` — create
- `DELETE /{slug}/comments/{id}` — soft delete, owner or platform team
- `POST /{slug}/comments/{id}/replies` — reply
- `POST /{slug}/comments/{id}/vote` — upvote (idempotent)

## View Count

Uses isolated DB session in `BackgroundTasks`. The background task creates its own `SessionLocal()` so it does not share the request-scoped session.

## User Collections

`GET /api/v1/users/me/{installs,favorites,forks}` responses include:
- `author` — resolved author name (batch query)
- `days_ago` — integer days since `published_at`

## Denormalized Counters

Updated in same DB transaction as the social action:

| Counter | Table | Trigger |
|---|---|---|
| `install_count` | skills | install/uninstall |
| `fork_count` | skills | fork |
| `favorite_count` | skills | favorite/unfavorite |
| `view_count` | skills | skill detail view (background task) |
| `review_count` | skills | create/delete review |
| `avg_rating` | skills | create/update/delete review |

## Key Files

- `apps/api/skillhub/routers/social.py` — social endpoints
- `apps/api/skillhub/services/social.py` — install, favorite, fork, follow
- `apps/api/skillhub/services/reviews.py` — reviews + comments
- `apps/api/skillhub/services/users.py` — user collections with author resolution
- `apps/api/skillhub/routers/skills.py` — view count background task
