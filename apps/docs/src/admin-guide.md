# Admin Guide

This guide covers SkillHub's administrative capabilities for Platform Team and Security Team members. All admin functions are available via both the web admin panel (at `/admin`) and the API.

## Admin Roles

SkillHub has two admin roles, implemented as boolean flags on user records:

| Role | Flag | Capabilities |
|------|------|-------------|
| **Platform Team** | `is_platform_team: true` | Feature/deprecate skills, review submissions (Gate 3), manage users, configure feature flags, view audit logs |
| **Security Team** | `is_security_team: true` | Remove skills for security reasons, view audit logs, override division restrictions for investigation |

These roles are additive -- a user can have both flags enabled. Regular users have both flags set to `false`.

---

## Division Setup and Management

Divisions are the foundation of SkillHub's access control model. Every skill, user, and access decision is scoped to one or more divisions.

### The 8 Default Divisions

| Slug | Display Name | Color |
|------|-------------|-------|
| `engineering-org` | Engineering Org | Blue |
| `product-org` | Product Org | Purple |
| `data-org` | Data Org | Green |
| `security-org` | Security Org | Red |
| `finance-org` | Finance Org | Amber |
| `hr-org` | HR Org | Teal |
| `research-org` | Research Org | Indigo |
| `operations-org` | Operations Org | Orange |

Divisions are seeded at database initialization and stored in the `divisions` table with `slug` as the primary key.

### Managing Skill-Division Assignments

When a skill is submitted, the author declares which divisions should have access. The Platform Team reviewer validates these declarations during Gate 3. After publication, admins can modify division assignments:

```bash
# View a skill's current divisions
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/skills/pr-review-assistant

# The response includes:
# "divisions": ["engineering-org", "product-org"]
```

### Cross-Division Access Requests

When a user requests access to a skill outside their division, the request appears in the admin queue:

```bash
# List pending access requests
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/admin/access-requests?status=pending

# Approve a request
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "approved"}' \
  https://skillhub.yourcompany.com/api/v1/admin/access-requests/{request_id}/resolve

# Deny a request
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "denied", "reason": "This skill contains engineering-specific tooling not applicable to your division."}' \
  https://skillhub.yourcompany.com/api/v1/admin/access-requests/{request_id}/resolve
```

::: warning
Division enforcement is **server-side only**. The API checks the requesting user's division against the skill's authorized divisions on every request. Client-side filtering is cosmetic -- never rely on it for access control.
:::

---

## Feature Flags

Feature flags provide progressive rollout control and kill switches for platform features. The **Feature Flags** section of the admin panel (`/admin/flags`) provides a full management UI: a list of all flags with global ON/OFF toggles, a detail panel for per-division overrides, and the ability to create or delete flags without touching the API directly.

In the detail panel, each division can be set to one of three states: **Inherit** (uses the global value), **Enable** (force-on for that division), or **Disable** (force-off for that division). Division override dots are shown on the list for flags that have any active overrides.

### Flag Structure

Each flag has:

| Field | Type | Description |
|-------|------|-------------|
| `key` | String (PK) | Unique identifier (e.g., `llm_judge_enabled`) |
| `enabled` | Boolean | Global on/off switch |
| `description` | String | Human-readable explanation |
| `division_overrides` | JSONB | Per-division overrides (e.g., `{"engineering-org": true, "finance-org": false}`) |

### Current Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `llm_judge_enabled` | `true` | Controls whether Gate 2 (AI evaluation) runs during submission |
| `featured_skills_v2` | `true` | Controls the featured skills carousel layout on the homepage |
| `gamification_enabled` | `true` | Controls display of community engagement metrics |
| `mcp_install_enabled` | `true` | Controls whether MCP-based skill installation is available |

### Override Logic

The effective flag value for a user is determined by:

1. Check `division_overrides` for the user's division
2. If an override exists, use it
3. If no override exists, use the global `enabled` value

```bash
# List all flags
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/flags

# Update a flag
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "division_overrides": {
      "engineering-org": true,
      "finance-org": false
    }
  }' \
  https://skillhub.yourcompany.com/api/v1/admin/flags/llm_judge_enabled
```

::: tip Progressive Rollout
Use division overrides to roll out a feature to one division first, then expand:

1. Set `enabled: false` globally
2. Set `division_overrides: {"engineering-org": true}` to enable for Engineering only
3. Monitor for issues
4. Add more divisions to the override
5. Set `enabled: true` globally and remove overrides
:::

---

## Audit Log

The audit log provides a tamper-proof record of all significant platform actions. It is the primary tool for compliance, incident investigation, and accountability.

### How It Works

- Every significant action creates an `audit_log` entry
- The table is **append-only** -- a PostgreSQL trigger blocks all `UPDATE` and `DELETE` operations
- Even database superusers cannot modify entries without disabling the trigger
- Entries include the actor, action type, target, metadata, IP address, and timestamp

### Audit Log Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique entry identifier |
| `event_type` | String | Action category (e.g., `skill.install`, `submission.approve`, `admin.flag_update`) |
| `actor_id` | UUID | User who performed the action |
| `target_type` | String | Type of object acted upon (e.g., `skill`, `submission`, `user`) |
| `target_id` | UUID | ID of the target object |
| `metadata` | JSONB | Additional context (varies by event type) |
| `ip_address` | String | Client IP address |
| `created_at` | Timestamp | When the action occurred |

### Event Types

| Event Type | When It Is Logged |
|------------|-------------------|
| `skill.install` | A user installs a skill |
| `skill.uninstall` | A user uninstalls a skill |
| `skill.fork` | A user forks a skill |
| `skill.feature` | Admin features a skill on the homepage |
| `skill.deprecate` | Admin deprecates a skill |
| `skill.remove` | Security Team removes a skill |
| `submission.create` | A user submits a new skill |
| `submission.gate1` | Gate 1 automated validation completes |
| `submission.gate2` | Gate 2 LLM judge evaluation completes |
| `submission.approve` | Admin approves a submission at Gate 3 |
| `submission.reject` | Admin rejects a submission at Gate 3 |
| `submission.change_request` | Admin requests changes at Gate 3 |
| `admin.flag_update` | Admin modifies a feature flag |
| `admin.user_update` | Admin modifies a user record |
| `access.request` | User requests cross-division access |
| `access.approve` | Admin approves an access request |
| `access.deny` | Admin denies an access request |

### Querying the Audit Log

```bash
# Recent audit entries
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/admin/audit-log?limit=50"

# Filter by event type
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/admin/audit-log?event_type=skill.remove"

# Filter by actor
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/admin/audit-log?actor_id={user_id}"

# Filter by target
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/admin/audit-log?target_type=skill&target_id={skill_id}"

# Filter by date range
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/admin/audit-log?from=2026-03-01&to=2026-03-24"
```

---

## User Management

Admins can list, filter, and update user records, including role assignments and division changes.

### Listing Users

```bash
# List all users
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/admin/users

# Filter by division
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/admin/users?division=engineering-org"

# Filter by role flags
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/admin/users?is_platform_team=true"
```

### Updating User Records

```bash
# Grant Platform Team access
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_platform_team": true}' \
  https://skillhub.yourcompany.com/api/v1/admin/users/{user_id}

# Grant Security Team access
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_security_team": true}' \
  https://skillhub.yourcompany.com/api/v1/admin/users/{user_id}

# Change a user's division
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"division": "product-org"}' \
  https://skillhub.yourcompany.com/api/v1/admin/users/{user_id}
```

::: warning
All user management actions are recorded in the audit log. Granting admin privileges should follow your organization's approval process.
:::

---

## Submission Review Workflow

Platform Team members review submissions at Gate 3. This is the final check before a skill becomes available in the marketplace.

### The Review Queue

```bash
# Get pending submissions (Gate 3 queue)
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/admin/submissions?status=gate3_pending"
```

### Review Process

For each submission in the queue, the reviewer should evaluate:

1. **Organizational value** -- Does this skill serve a genuine need?
2. **Division appropriateness** -- Are the declared divisions reasonable?
3. **Content accuracy** -- Will the instructions produce correct output?
4. **Safety** -- Could this skill produce harmful, misleading, or data-leaking output?
5. **Overlap** -- Does this duplicate an existing skill without sufficient differentiation?

### Making a Decision

::: code-group

```bash [Approve]
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "result": "approve",
    "notes": "Well-structured skill with clear use case. Approved for declared divisions."
  }' \
  https://skillhub.yourcompany.com/api/v1/admin/submissions/{id}/review
```

```bash [Request Changes]
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "result": "changes_requested",
    "notes": "The output format section is missing. Please add a clear specification of what the skill should produce. Also, the engineering-org division is declared but the content is specific to data pipelines -- consider changing to data-org."
  }' \
  https://skillhub.yourcompany.com/api/v1/admin/submissions/{id}/review
```

```bash [Reject]
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "result": "reject",
    "notes": "This skill instructs Claude to make external API calls to a third-party service, which violates the platform security policy. This is a fundamental design issue, not something that can be fixed with minor revisions."
  }' \
  https://skillhub.yourcompany.com/api/v1/admin/submissions/{id}/review
```

:::

::: tip Review Best Practices
- **Be specific** in change request notes. "Needs improvement" is not actionable; "Add a numbered output format" is.
- **Use rejection sparingly.** Most issues can be resolved with a change request. Reserve rejection for fundamental problems.
- **Check Gate 2 results** before reviewing. The LLM judge findings may highlight issues worth focusing on.
- **Review within 48 hours.** The target SLA keeps submissions from languishing in the queue.
:::

---

## Skill Moderation

The **Skills** section of the admin panel (`/admin/skills`) shows all published skills in a searchable, paginated table. Each row displays the skill name, slug, category, version, install count, and status (published, featured, deprecated, or removed). Per-row action buttons let Platform Team members feature/unfeature or deprecate a skill, and Security Team members can remove a skill with a confirmation dialog.

Admins can moderate published skills through three actions:

### Feature a Skill

Highlight a skill on the homepage carousel:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"featured": true, "featured_order": 1}' \
  https://skillhub.yourcompany.com/api/v1/admin/skills/{slug}/moderate
```

### Deprecate a Skill

Mark a skill as deprecated (still accessible but flagged as outdated):

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "deprecated"}' \
  https://skillhub.yourcompany.com/api/v1/admin/skills/{slug}/moderate
```

### Remove a Skill (Security Team)

Emergency removal for security issues:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "removed", "reason": "Skill content contains prompt injection vector"}' \
  https://skillhub.yourcompany.com/api/v1/admin/skills/{slug}/moderate
```

::: danger
Removing a skill is immediate and affects all users. Users who have already installed the skill retain their local copy, but the skill is hidden from the marketplace and cannot be reinstalled. Use this only for genuine security incidents.
:::

---

## Analytics Dashboard

The admin dashboard at `/admin` displays live platform metrics. The dashboard page shows:

- **Daily Active Users, New Installs (7d), Active Installs, Published Skills, Pending Reviews, and Submission Pass Rate** as real-time stat cards
- **Installs Over Time** — an area chart showing install and user trends
- **By Division** — per-division install breakdown
- **Submission Funnel (30d)** — conversion from submitted through gate1, gate2, approved, and published

Key metrics are also available directly via the API:

### Available Metrics

```bash
# Platform overview stats
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/admin/stats

# Response includes:
# {
#   "total_skills": 61,
#   "total_users": 24,
#   "total_installs": 342,
#   "total_submissions": 18,
#   "pending_reviews": 3,
#   "skills_by_category": {...},
#   "installs_by_division": {...}
# }
```

### Key Pilot Metrics to Monitor

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Skills installed per active user per week | >= 2 | Install events / active users |
| Skill submission rate | >= 5 new skills per month | Submission count by month |
| Gate 3 review completion time | < 48 hours | Time from gate3_pending to approve/reject |
| User satisfaction (NPS) | >= 40 | Feedback submissions categorized as praise vs. complaint |

## Data Export

The **Export** section of the admin panel (`/admin/export`) lets you download platform data without writing API queries. Choose a scope (Installs, Submissions, Users, or Analytics), a format (CSV or JSON), and a date range. Date presets — Today, Yesterday, Last 7 Days, Last 30 Days, Last 90 Days, Year to Date, and All Time — fill the date fields automatically, or you can set a custom range. Each admin account can request up to 5 exports per day.

---

## Next Steps

- [Review the FAQ for common admin questions](/faq)
- [Browse the resources and glossary](/resources)
- [Return to the documentation home](/)
