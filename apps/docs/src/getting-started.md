# Getting Started

SkillHub gives you three ways to install skills: the MCP Server (recommended for Claude Code users), the Claude Code CLI, and manual copy. This guide walks through each method.

## Prerequisites

Before you begin, make sure you have:

- **Claude Code** or **Claude Desktop** installed
- Access to your organization's SkillHub instance (e.g., `https://skillhub.yourcompany.com`)
- A valid SSO session (or dev credentials if running locally)

## Option 1: MCP Server (Recommended) {#mcp-server}

The SkillHub MCP Server integrates directly with Claude Code and Claude Desktop, giving you 9 tools to search, install, manage, and submit skills without leaving your AI assistant.

### Step 1: Install the MCP Server

::: code-group

```bash [npm (global)]
npm install -g @skillhub/mcp-server
```

```bash [npx (no install)]
npx @skillhub/mcp-server
```

:::

### Step 2: Configure Claude Code

Add the SkillHub MCP server to your Claude Code configuration:

```json
// ~/.claude/mcp_servers.json
{
  "skillhub": {
    "command": "npx",
    "args": ["@skillhub/mcp-server"],
    "env": {
      "SKILLHUB_API_URL": "https://skillhub.yourcompany.com/api/v1",
      "SKILLHUB_TOKEN": "${SKILLHUB_JWT_TOKEN}"
    }
  }
}
```

::: tip Local Development
For local development, use `http://localhost:8000/api/v1` as the API URL. You can obtain a dev JWT token via:

```bash
curl -X POST http://localhost:8000/auth/token \
  -d "username=test&password=user"
```
:::

### Step 3: Verify the Connection

Restart Claude Code, then ask Claude:

```
Search SkillHub for code review skills
```

If configured correctly, Claude will use the `search_skills` MCP tool and return matching results from the marketplace.

### Step 4: Install a Skill

Once you find a skill you want, install it directly:

```
Install the pr-review-assistant skill from SkillHub
```

Claude will call `install_skill` with the skill slug. The MCP server:

1. Checks your division has access to the skill
2. Downloads the latest version content
3. Writes the `SKILL.md` file to `.claude/skills/<slug>/SKILL.md`
4. Records the installation in the SkillHub API

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `search_skills` | Search the marketplace by keyword, category, or division |
| `get_skill` | Get full detail for a specific skill by slug |
| `install_skill` | Install a skill to your local `.claude/skills/` directory |
| `update_skill` | Detect and update stale installed skills |
| `list_installed` | View all installed skills with staleness indicator |
| `fork_skill` | Fork a skill to create a division-specific variant |
| `submit_skill` | Submit a SKILL.md for review without leaving the editor |
| `check_submission_status` | Check your submission's pipeline status |

---

## Option 2: Claude Code CLI {#claude-cli}

If you prefer direct CLI commands over natural language, you can use the Claude Code skill management commands:

### Install a Skill

```bash
claude skill install pr-review-assistant
```

This command resolves the slug against the SkillHub API, checks division access, and writes the skill file.

### List Installed Skills

```bash
claude skill list
```

### Update a Skill

```bash
claude skill update pr-review-assistant
```

### Uninstall a Skill

```bash
claude skill uninstall pr-review-assistant
```

::: info
The CLI commands interact with the same SkillHub API as the MCP server. You need the same environment variables configured (`SKILLHUB_API_URL`, `SKILLHUB_TOKEN`).
:::

---

## Option 3: Using via Cline {#cline}

Cline supports MCP servers through its configuration panel.

### Step 1: Open Cline Settings

In VS Code, open the Cline extension sidebar and navigate to **Settings > MCP Servers**.

### Step 2: Add the SkillHub Server

Click **Add Server** and enter:

| Field | Value |
|-------|-------|
| Name | `skillhub` |
| Command | `npx` |
| Args | `@skillhub/mcp-server` |
| Environment | `SKILLHUB_API_URL=https://skillhub.yourcompany.com/api/v1` |

### Step 3: Use Skills

Once connected, you can ask Cline to search and install skills just as you would in Claude Code. The MCP tools are available in Cline's tool palette.

---

## Option 4: Manual Installation {#manual}

You can always install a skill by copying its content directly.

### Step 1: Find the Skill

Browse the SkillHub web marketplace at your organization's URL, or use the API:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/skills/pr-review-assistant
```

### Step 2: Copy the Content

On the skill detail page, go to the **Install** tab and click **Copy SKILL.md**. Alternatively, copy the `content` field from the API response.

### Step 3: Write the File

Create the skill directory and file:

```bash
mkdir -p .claude/skills/pr-review-assistant
cat > .claude/skills/pr-review-assistant/SKILL.md << 'EOF'
---
name: PR Review Assistant
description: Thorough pull request reviews with actionable feedback
triggers:
  - review this PR
  - review pull request
  - code review
---

(skill content here)
EOF
```

### Step 4: Verify

Start a new Claude Code session. The skill is now loaded into Claude's context when you use one of its trigger phrases.

---

## What Happens After Installation

When you install a skill (via any method):

1. **A `SKILL.md` file** is written to `.claude/skills/<slug>/SKILL.md` in your project
2. **The install is tracked** in SkillHub's API (install count, version, method)
3. **Claude Code loads the skill** on next session start, injecting it into the context window when a trigger phrase is matched

::: warning Division Access
Skills are scoped to organizational divisions. If you try to install a skill that your division does not have access to, the installation will be blocked. You can request access through the web UI or via the API.
:::

## Next Steps

- [Learn what skills are and how they work](/introduction-to-skills)
- [Discover skills in the marketplace](/skill-discovery)
- [Submit your own skill](/submitting-a-skill)
