# Frequently Asked Questions

Common questions about SkillHub, organized by topic. Click any question to expand the answer.

## Installation

::: details How do I install my first skill?
The fastest way is through the MCP Server integration with Claude Code. Once configured, simply ask Claude:

```
Search SkillHub for code review skills
```

Then:

```
Install the pr-review-assistant skill
```

Claude handles the rest -- checking division access, downloading the skill, and writing it to `.claude/skills/pr-review-assistant/SKILL.md`.

See the full [Getting Started guide](/getting-started) for all installation methods.
:::

::: details Where are installed skills stored on my machine?
Skills are stored as markdown files in your project directory:

```
your-project/
  .claude/
    skills/
      pr-review-assistant/
        SKILL.md
      sql-query-builder/
        SKILL.md
```

Each skill gets its own directory under `.claude/skills/`, named by the skill's slug.
:::

::: details Can I install skills globally instead of per-project?
Skills are currently installed per-project in the `.claude/skills/` directory within your working directory. This is by design -- different projects may need different skills. If you want a skill available across all projects, you can install it in your home directory's Claude configuration at `~/.claude/skills/`.
:::

::: details How do I update an installed skill?
Use the MCP server or CLI:

```bash
# Via natural language in Claude Code
Update the pr-review-assistant skill from SkillHub

# Via CLI
claude skill update pr-review-assistant
```

The `list_installed` MCP tool also shows a staleness indicator for each installed skill, telling you which ones have newer versions available.
:::

::: details How do I uninstall a skill?
```bash
# Via natural language in Claude Code
Uninstall the meeting-summarizer skill

# Via CLI
claude skill uninstall meeting-summarizer

# Manually
rm -rf .claude/skills/meeting-summarizer/
```

Using the MCP or CLI method also records the uninstall in SkillHub's tracking system.
:::

## Skill Submission

::: details How long does the review process take?
- **Gate 1 (Automated):** Immediate -- runs within seconds of submission
- **Gate 2 (LLM Judge):** Typically under 30 seconds
- **Gate 3 (Human Review):** Target SLA is under 48 hours

Most submissions that pass Gates 1 and 2 are reviewed by a human within one business day.
:::

::: details My submission failed Gate 1. What should I check?
Common Gate 1 failures:

1. **Missing required fields** -- Ensure your YAML front matter includes `name`, `description`, `triggers`, and `category`
2. **Trigger collision** -- Your trigger phrases are too similar to an existing skill (Jaccard > 0.7). Make your triggers more specific.
3. **Invalid category** -- Must be one of: engineering, product, data, security, finance, general, hr, research, operations
4. **Empty content** -- The markdown body after the front matter must be at least 50 characters

Check your submission status for specific failure details:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/submissions/SUB-00042
```
:::

::: details My submission failed Gate 2 (LLM Judge). What does the score mean?
The LLM judge scores on three dimensions: quality (40%), security (30%), and usefulness (30%). A total score of 70 or above is required to pass.

Common reasons for low scores:
- **Vague instructions** that do not give Claude a clear process to follow
- **No output format** specified, leaving results inconsistent
- **Potential security issues** like prompting Claude to access external URLs
- **Trivially obvious content** that does not add value beyond what Claude already knows

Review the judge's findings in the submission detail for specific feedback.
:::

::: details Can I resubmit after a rejection?
If the reviewer **requested changes** (not a permanent rejection), yes. Revise your content based on the reviewer's notes and resubmit. The revised submission goes through the full 3-gate pipeline again.

If the submission was **rejected**, you will need to create a substantially different submission. The rejection reason will explain what fundamental issue led to rejection.
:::

::: details Can I update a published skill?
Yes. Submit an updated version through the same submission process. The update goes through all three gates. Once approved, the new version replaces the previous one, and users with the old version installed will see a staleness indicator.
:::

## Reviews and Ratings

::: details Can I edit my review after posting?
Yes. You can update both your star rating and review text at any time. You have one review per skill, and editing replaces the existing content.

```bash
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating": 4, "body": "Updated review text"}' \
  https://skillhub.yourcompany.com/api/v1/skills/my-skill/reviews
```
:::

::: details How is the average rating calculated?
SkillHub uses a **Bayesian average** instead of a simple mean. This prevents skills with very few ratings from dominating the leaderboard. A skill with 2 five-star ratings will not outrank a skill with 50 ratings averaging 4.7 stars.

The formula pulls low-sample skills toward the platform-wide average, requiring meaningful engagement to reach the top.
:::

::: details Can I delete a comment?
You can **soft-delete** your own comments. The comment text is removed, but the thread structure is preserved (replies remain visible). Admins can also soft-delete any comment that violates community guidelines.
:::

## Divisions and Access

::: details What are divisions?
Divisions are organizational units (e.g., Engineering Org, Product Org, Data Org) that control skill visibility. Skills are authorized for specific divisions, and the API enforces this -- you can only see and install skills your division has access to.

SkillHub has 8 divisions: Engineering Org, Product Org, Data Org, Security Org, Finance Org, HR Org, Research Org, and Operations Org.
:::

::: details I need access to a skill outside my division. How do I request it?
From the skill's detail page (if you can see it via search), click **Request Access**. You will need to provide a reason for the request. An admin from the target division reviews and approves or denies the request.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Need this skill for cross-team project X"}' \
  https://skillhub.yourcompany.com/api/v1/skills/{slug}/access-requests
```
:::

::: details Can a skill be available to all divisions?
Yes. When submitting a skill, the author declares which divisions should have access. A skill can be authorized for all 8 divisions if it is broadly applicable. The Platform Team reviews division declarations as part of Gate 3.
:::

## MCP Server

::: details What is MCP?
MCP (Model Context Protocol) is a standard for connecting AI assistants to external tools and data sources. SkillHub's MCP server exposes 9 tools that let you interact with the marketplace directly from Claude Code or Claude Desktop, without switching to a browser.
:::

::: details Which MCP tools are available?
| Tool | Description |
|------|-------------|
| `search_skills` | Search the marketplace |
| `get_skill` | Get skill details by slug |
| `install_skill` | Install a skill locally |
| `update_skill` | Update an installed skill |
| `list_installed` | List installed skills with staleness info |
| `fork_skill` | Fork a skill for your division |
| `submit_skill` | Submit a new skill for review |
| `check_submission_status` | Check pipeline status |
| `uninstall_skill` | Remove an installed skill |
:::

::: details The MCP server is not connecting. How do I debug?
1. **Check the configuration** in `~/.claude/mcp_servers.json` -- verify the `SKILLHUB_API_URL` and `SKILLHUB_TOKEN` values
2. **Test the API directly** with curl to confirm the server is reachable
3. **Check your token** -- JWT tokens expire; obtain a fresh one if needed
4. **Restart Claude Code** after changing MCP configuration
5. **Check logs** -- the MCP server logs to stderr by default
:::

## Admin

::: details Who can access admin functions?
Two roles have admin access:
- **Platform Team** (`is_platform_team: true`) -- Can feature/deprecate skills, review submissions, manage users, and view audit logs
- **Security Team** (`is_security_team: true`) -- Can remove skills for security reasons and view audit logs

Both roles are set as flags on the user record, not as a separate role column.
:::

::: details What is the audit log?
The audit log is an append-only table that records every significant platform action: skill installations, submissions, reviews, admin actions, access requests, and more. It is protected by a database trigger that prevents any UPDATE or DELETE operations -- once written, entries are permanent.

This provides a tamper-proof record for compliance and incident investigation.
:::

::: details How do feature flags work?
Feature flags are boolean switches that control platform behavior. Each flag can have per-division overrides stored as JSONB. Current flags include:

- `llm_judge_enabled` -- Controls whether Gate 2 (AI evaluation) runs
- `featured_skills_v2` -- Controls the featured skills section layout
- `gamification_enabled` -- Controls community engagement metrics display
- `mcp_install_enabled` -- Controls MCP-based skill installation

Admins manage flags via the API:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/flags
```
:::

## Next Steps

- [Get started with installation](/getting-started)
- [Browse the marketplace](/skill-discovery)
- [Check the resources page for a glossary](/resources)
