# Codebase Map Generator Skill

**Name**: `codebase-map-generator`

**Purpose**: Create, regenerate, and maintain codebase maps as Tier 1 project context files with smart detection, socratic validation, user editing support, and post-creation doc updates.

---

## Files

### SKILL.md (397 lines)
Main skill definition. Contains:
- Core 6-phase workflow (detection → probing → mapping → generation → iteration → finalization)
- Tool integration patterns for glob, grep, read, bash, AskUserQuestion, artifacts
- Output specifications (directory tree, domain sections, relationships, optional sections)
- Post-creation doc update workflow
- Critical guidelines and example triggers

### references/tech-stack-patterns.md
Glob patterns for detecting:
- JavaScript/TypeScript (monorepos, frameworks, configs)
- Go (modules, services)
- Python (projects, frameworks)
- Databases (Prisma, SQL, ORMs)
- Infrastructure (CDK, Terraform, Docker, CI/CD)
- Configuration & metadata files

Recommended glob sequence for progressive understanding.

### references/section-templates.md
Domain-aware markdown templates that adapt to detected tech stack:
- TypeScript monorepo (Nx, pnpm, Lerna)
- Go microservice
- Python Django/FastAPI
- Single-repo TypeScript
- Database schema sections
- Infrastructure sections
- Architectural relationships (arrows, tables, bullets)
- Configuration sections

Template selection logic based on detection signals.

### references/socratic-prompts.md
Exact prompts for 6 socratic questions:
1. Domain boundaries validation
2. Naming preferences (path-accurate vs. concise)
3. Optional sections (schema, infra, config)
4. Architectural focus (top 3 priority areas)
5. Map location confirmation
6. Post-creation doc updates (max 2 files)

Includes conditional questions for discrepancies and sync mode.
Flow diagram + tips for asking effectively.

### references/doc-update-templates.md
Reference snippets for updating related project files:
- constitution.md — Tier 1 context section
- CLAUDE.md — Codebase navigation reference
- .ruler/AGENTS.md — Navigation section
- .claude/ plugin config — Context hierarchy
- .kiro/specs/ — Implementation guidelines
- README.md — Getting started guide

Includes proposed change preview format, sync guidelines, and context window awareness tips.

---

## Triggers

Use this skill when:
- `"create a codebase map"`
- `"regenerate the codebase map"`
- `"sync the codebase map"`
- `"update my project's navigation index"`
- Need a living navigational index for agent code discovery
- Any variant of creating/maintaining a codebase map as Tier 1 context

---

## Key Features

✓ **Smart Detection**: Automatically detects tech stack, frameworks, project structure
✓ **Socratic Probing**: Asks clarifying questions to validate structure against reality
✓ **User Editing**: Supports inline refinement + intelligent sync/regen
✓ **Dynamic Templates**: Adapts section structure to detected repo type
✓ **Relationship Mapping**: Extracts dependencies from import patterns
✓ **Post-Creation Updates**: Offers to update constitution.md, CLAUDE.md, .ruler/ with references
✓ **Language-Agnostic**: Works with TypeScript, Go, Python, and hybrid repos
✓ **Spartan Design**: Keeps codebase map compact (token-efficient for Tier 1)

---

## Integration

Place in: `.claude/skills/codebase-map-generator/`

Requires: glob, Grep, Read, Bash, AskUserQuestion, artifacts tools

References files (bundled, no external dependencies): `references/*.md`
