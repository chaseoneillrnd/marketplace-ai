# API Reference

All endpoints. Auth column: `none` = public, `optional` = enhanced with auth, `user` = required, `platform` = platform team, `security` = security team.

## Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | Health check + version |

## Auth (`/auth`)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/token` | none | Stub login, returns JWT |
| GET | `/auth/me` | user | Return current user claims |
| GET | `/auth/dev-users` | none* | List available stub users |
| GET | `/auth/oauth/{provider}` | none | OAuth redirect URL (placeholder) |
| GET | `/auth/oauth/{provider}/callback` | none | OAuth callback (501) |

*`/auth/dev-users` requires `stub_auth_enabled` setting. Returns 403 when disabled.

## Skills (`/api/v1/skills`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/skills` | optional | Browse/search with filters and pagination |
| GET | `/api/v1/skills/categories` | none | List all categories |
| GET | `/api/v1/skills/{slug}` | optional | Skill detail by slug |
| GET | `/api/v1/skills/{slug}/versions` | user | List all versions |
| GET | `/api/v1/skills/{slug}/versions/latest` | user | Get latest version content |
| GET | `/api/v1/skills/{slug}/versions/{version}` | user | Get specific version content |

## Social (`/api/v1/skills`)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/skills/{slug}/install` | user | Install skill (division check) |
| DELETE | `/api/v1/skills/{slug}/install` | user | Uninstall (soft delete) |
| POST | `/api/v1/skills/{slug}/favorite` | user | Favorite (idempotent) |
| DELETE | `/api/v1/skills/{slug}/favorite` | user | Unfavorite |
| POST | `/api/v1/skills/{slug}/fork` | user | Fork skill |
| POST | `/api/v1/skills/{slug}/follow` | user | Follow skill author (idempotent) |
| DELETE | `/api/v1/skills/{slug}/follow` | user | Unfollow skill author |
| GET | `/api/v1/skills/{slug}/reviews` | none | List reviews (paginated) |
| POST | `/api/v1/skills/{slug}/reviews` | user | Create review (409 if duplicate) |
| PATCH | `/api/v1/skills/{slug}/reviews/{id}` | user | Update review (owner only) |
| POST | `/api/v1/skills/{slug}/reviews/{id}/vote` | user | Vote helpful/unhelpful |
| GET | `/api/v1/skills/{slug}/comments` | none | List comments (paginated) |
| POST | `/api/v1/skills/{slug}/comments` | user | Create comment |
| DELETE | `/api/v1/skills/{slug}/comments/{id}` | user | Soft delete (owner or platform) |
| POST | `/api/v1/skills/{slug}/comments/{id}/replies` | user | Reply to comment |
| POST | `/api/v1/skills/{slug}/comments/{id}/vote` | user | Upvote comment |

## Submissions

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/submissions` | user | Create submission (runs Gate 1) |
| GET | `/api/v1/submissions/{id}` | user | Get detail (owner or platform) |
| POST | `/api/v1/skills/{slug}/access-request` | user | Request cross-division access |

## Users (`/api/v1/users`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/users/me` | user | Profile with stats |
| GET | `/api/v1/users/me/installs` | user | Installed skills (paginated) |
| GET | `/api/v1/users/me/favorites` | user | Favorited skills (paginated) |
| GET | `/api/v1/users/me/forks` | user | Forked skills (paginated) |
| GET | `/api/v1/users/me/submissions` | user | Submissions with status (paginated) |

## Admin (`/api/v1/admin`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/admin/users` | platform | List all users (filterable) |
| PATCH | `/api/v1/admin/users/{user_id}` | platform | Update user fields |
| POST | `/api/v1/admin/submissions/{id}/scan` | platform | Trigger Gate 2 LLM scan |
| GET | `/api/v1/admin/submissions` | platform | List all submissions |
| POST | `/api/v1/admin/submissions/{id}/review` | platform | Gate 3 human review |
| GET | `/api/v1/admin/access-requests` | platform | List access requests |
| POST | `/api/v1/admin/access-requests/{id}/review` | platform | Review access request |
| POST | `/api/v1/admin/skills/{slug}/feature` | platform | Set featured status |
| POST | `/api/v1/admin/skills/{slug}/deprecate` | platform | Deprecate skill |
| DELETE | `/api/v1/admin/skills/{slug}` | security | Soft-remove skill |
| POST | `/api/v1/admin/recalculate-trending` | platform | Recalculate trending scores |
| GET | `/api/v1/admin/audit-log` | platform | Query audit log |

## Flags (`/api/v1`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/flags` | optional | All flags with division overrides |
| POST | `/api/v1/admin/flags` | platform | Create a feature flag |
| PATCH | `/api/v1/admin/flags/{key}` | platform | Update a feature flag |
| DELETE | `/api/v1/admin/flags/{key}` | platform | Delete a feature flag |

## Pagination Pattern

All paginated endpoints accept `page` (default 1) and `per_page` (default 20, max 100).
Response shape: `{ items: [], total: int, page: int, per_page: int, has_more: bool }`.
