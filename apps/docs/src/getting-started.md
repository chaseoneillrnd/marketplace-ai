# Getting Started

SkillHub is an internal marketplace — the MCP server and API run from this monorepo, not from a public registry. This guide walks through the three ways to install skills.

## Prerequisites

- **Claude Code** installed
- The SkillHub monorepo cloned and set up (`mise run init`)
- Dev servers running (`mise run dev:all`)
- A valid session (use stub auth locally — see [Authentication](#authentication) below)

## Authentication {#authentication}

SkillHub uses JWT tokens for API access. In development, stub auth provides pre-configured test users:

```bash
# Get a dev token (password is always "user")
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "user"}'
```

**Available dev users:**

| Username | Division | Role | Admin? |
|----------|----------|------|--------|
| `alice` | Engineering Org | Staff Engineer | Yes (platform team) |
| `bob` | Data Science Org | Senior Data Scientist | No |
| `carol` | Security Org | Security Lead | No (security team) |
| `dave` | Product Org | Senior PM | No |
| `admin` | Engineering Org | Platform Lead | Yes (platform + security) |
| `test` | Engineering Org | Senior Engineer | No |

You can also list all dev users via `GET http://localhost:8000/auth/dev-users`.

---

## Option 1: MCP Server (Recommended) {#mcp-server}

The SkillHub MCP Server integrates directly with Claude Code, giving you tools to search, install, manage, and submit skills without leaving your AI assistant.

### Step 1: Start the MCP Server

The MCP server runs from the monorepo:

```bash
# Via mise (recommended)
mise run dev:mcp

# Or directly
PYTHONPATH=apps/mcp-server:libs/python-common python -m skillhub_mcp.server
```

The server starts on `localhost:8001` and connects to the API at `localhost:8000`.

### Step 2: Configure Claude Code

Add the SkillHub MCP server to your Claude Code configuration:

```json
// .mcp.json (project-level) or ~/.claude/mcp_servers.json (global)
{
  "mcpServers": {
    "skillhub": {
      "command": "python",
      "args": ["-m", "skillhub_mcp.server"],
      "env": {
        "PYTHONPATH": "apps/mcp-server:libs/python-common",
        "SKILLHUB_MCP_API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

::: tip Configuration
The MCP server reads settings from `SKILLHUB_MCP_*` environment variables:
- `SKILLHUB_MCP_API_BASE_URL` — API endpoint (default: `http://localhost:8000`)
- `SKILLHUB_MCP_HOST` — Server bind address (default: `127.0.0.1`)
- `SKILLHUB_MCP_PORT` — Server port (default: `8001`)
- `SKILLHUB_MCP_SKILLS_DIR` — Where to write SKILL.md files (default: `~/.claude/skills`)
:::

### Step 3: Authenticate

In Claude Code, ask Claude to log in:

```
Log in to SkillHub as alice
```

Claude will call the `login` tool which authenticates against the API and stores the bearer token for subsequent requests.

### Step 4: Search and Install

```
Search SkillHub for code review skills
```

```
Install the pr-review-assistant skill from SkillHub
```

The MCP server will check your division has access, download the skill content, write `SKILL.md` to your local `.claude/skills/` directory, and record the install in the API.

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `login` | Authenticate with SkillHub (stub auth in dev) |
| `search_skills` | Search by keyword, category, division, or filter |
| `get_skill` | Get full detail for a skill by slug |
| `install_skill` | Install a skill to `.claude/skills/` with division enforcement |
| `update_skill` | Update an installed skill to the latest version |
| `uninstall_skill` | Remove a skill locally and record the uninstall |
| `list_installed` | View installed skills with staleness indicator |
| `fork_skill` | Fork a skill to create a division-specific variant |
| `submit_skill` | Submit a SKILL.md for review |
| `get_submission_status` | Check your submission's pipeline status |

---

## Option 2: Web UI {#web-ui}

Browse and manage skills through the web marketplace at [localhost:5173](http://localhost:5173).

### Install from the Web

1. Browse or search for a skill
2. Click into the skill detail page
3. Click **Install** and follow the instructions for your preferred method
4. The detail page shows the `SKILL.md` content you can copy manually

### Track Your Installs

Your installed skills, favorites, and followed authors are tracked in your profile. The web UI shows version staleness indicators when newer versions are available.

---

## Option 3: Manual Installation {#manual}

You can always install a skill by copying its content directly.

### Step 1: Find the Skill

Browse the web marketplace or use the API:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/skills/pr-review-assistant
```

### Step 2: Write the File

Create the skill directory and file:

```bash
mkdir -p .claude/skills/pr-review-assistant
# Paste the skill content into SKILL.md
```

### Step 3: Verify

Start a new Claude Code session. The skill loads into Claude's context when you use one of its trigger phrases.

---

## What Happens After Installation

When you install a skill (via any method):

1. **A `SKILL.md` file** is written to `.claude/skills/<slug>/SKILL.md` in your project
2. **The install is tracked** in SkillHub's API (install count, version, method)
3. **Claude Code loads the skill** on next session start, injecting it into the context window when a trigger phrase is matched

::: warning Division Access
Skills are scoped to organizational divisions. If you try to install a skill that your division does not have access to, the installation will be blocked. Request access through the web UI or contact your division admin.
:::

## Next Steps

- [Learn what skills are and how they work](/introduction-to-skills)
- [Discover skills in the marketplace](/skill-discovery)
- [Submit your own skill](/submitting-a-skill)
