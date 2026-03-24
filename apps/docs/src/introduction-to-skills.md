# Introduction to Skills

Skills are the building blocks of SkillHub. They give Claude specialized knowledge and instructions for specific tasks -- from reviewing pull requests to drafting executive summaries to generating data visualizations.

## What Is a Skill?

A skill is a **markdown file** (`SKILL.md`) that contains structured instructions for Claude. When installed, the skill's content is injected into Claude's context window whenever a matching trigger phrase is detected, giving Claude task-specific expertise on demand.

Think of skills as reusable prompt templates with metadata -- but instead of copying and pasting prompts, you install them once and they activate automatically.

## The SKILL.md Format

Every skill is a single markdown file with two sections: **front matter** (YAML metadata) and **content** (the instructions Claude follows).

```markdown
---
name: PR Review Assistant
description: Thorough pull request code reviews with actionable feedback
triggers:
  - review this PR
  - review pull request
  - code review
category: engineering
tags:
  - code-review
  - pull-request
  - quality
---

# PR Review Assistant

You are an expert code reviewer. When asked to review a pull request,
follow this structured process:

## Review Checklist

1. **Correctness** — Does the code do what it claims?
2. **Security** — Are there injection risks, exposed secrets, or auth gaps?
3. **Performance** — Are there N+1 queries, unnecessary allocations, or blocking calls?
4. **Readability** — Is the code clear to a new team member?
5. **Testing** — Are edge cases covered? Are tests meaningful?

## Output Format

For each finding, provide:
- **File and line** — exact location
- **Severity** — critical / warning / suggestion
- **Description** — what the issue is
- **Recommendation** — how to fix it

Always end with a summary: approve, request changes, or needs discussion.
```

## Anatomy of a Skill

### Front Matter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Human-readable display name |
| `description` | Yes | One-line summary (shown in search results) |
| `triggers` | Yes | Phrases that activate the skill in Claude Code |
| `category` | Yes | One of the 9 marketplace categories |
| `tags` | No | Freeform labels for search and filtering |

### Content Section

The content section is freeform markdown. This is what Claude actually reads and follows. Effective skill content typically includes:

- **Role definition** -- who Claude should act as
- **Process steps** -- a structured workflow to follow
- **Output format** -- what the result should look like
- **Constraints** -- what to avoid or watch out for
- **Examples** -- sample inputs and outputs (optional but powerful)

## How Skills Work in Claude Code

When you start a Claude Code session, the following happens:

```
1. Claude Code scans .claude/skills/ for SKILL.md files
2. Each skill's front matter is parsed (name, triggers, description)
3. When you type a message matching a trigger phrase, the skill's
   full content is injected into Claude's context window
4. Claude follows the skill's instructions for that interaction
```

::: info Context Window Injection
Skills are loaded **on demand** based on trigger phrases, not all at once. This is important because Claude's context window has a finite size. Only relevant skills are injected for each conversation turn.
:::

### Trigger Matching

Trigger phrases use fuzzy matching. If your skill has the trigger `review this PR`, any of these will activate it:

- "review this PR"
- "can you review this pull request?"
- "please do a code review"

The matching is generous -- Claude Code looks for semantic overlap, not exact string matches.

## Skill Categories

SkillHub organizes skills into 9 categories that map to common organizational functions:

| Category | Description | Example Skills |
|----------|-------------|----------------|
| **Engineering** | Code generation, review, testing, DevOps | PR Review, Test Generator, Refactoring Guide |
| **Product** | Specs, user stories, roadmaps | PRD Writer, User Story Generator, Roadmap Planner |
| **Data** | Analytics, SQL, visualization, ML | SQL Query Builder, Dashboard Generator, Data Pipeline |
| **Security** | Threat modeling, audit, compliance | Vulnerability Scanner, OWASP Checklist, Audit Report |
| **Finance** | Budgets, forecasting, reporting | Financial Model Builder, Expense Analyzer |
| **General** | Cross-functional, productivity | Meeting Summarizer, Email Drafter, Slide Deck Creator |
| **HR** | People ops, hiring, onboarding | Interview Guide, Onboarding Checklist, Policy Writer |
| **Research** | Literature review, synthesis, ideation | Research Summarizer, Competitive Analysis, Patent Search |
| **Operations** | Process improvement, SOP, logistics | SOP Generator, Process Mapper, Incident Reporter |

## Skill Types by Use Case

Skills tend to fall into four broad patterns:

### Coding Skills
Inject software engineering expertise. They typically define review checklists, code generation patterns, or testing strategies.

### Productivity Skills
Automate document creation -- meeting notes, slide outlines, email drafts. They focus on output format and tone.

### Analysis Skills
Guide Claude through data interpretation, chart generation, and insight extraction. They define structured analytical frameworks.

### Communication Skills
Shape how Claude writes for specific audiences -- executive summaries, customer emails, internal announcements. They encode style guides and organizational voice.

## What Makes a Good Skill

::: tip Best Practices
1. **Be specific.** A skill for "Python FastAPI endpoint review" outperforms one for "code review."
2. **Define the output format.** Claude follows explicit formatting instructions reliably.
3. **Include constraints.** Tell Claude what NOT to do (e.g., "never suggest rewriting the entire file").
4. **Use numbered steps.** Sequential processes produce more consistent results.
5. **Keep it focused.** One skill, one task. Use [skill chaining](/advanced-usage) for complex workflows.
:::

::: warning Common Pitfalls
- **Too vague:** "Help with code" gives Claude no actionable structure.
- **Too long:** Skills over 2,000 words may crowd out conversation context.
- **Conflicting instructions:** If a skill says "be concise" and "include all details," Claude will struggle.
- **No triggers:** Without trigger phrases, the skill never activates automatically.
:::

## Next Steps

- [See real-world uses for skills](/uses-for-skills)
- [Discover skills in the marketplace](/skill-discovery)
- [Submit your own skill](/submitting-a-skill)
