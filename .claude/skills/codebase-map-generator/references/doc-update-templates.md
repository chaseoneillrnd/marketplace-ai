# Doc Update Templates — Reference Snippets

When offering post-creation updates to project files, use these templates as starting points. Adapt to project context.

## Template 1: constitution.md Reference

**Location**: Usually near top, in "Context & Memory" or "Tier 1 Sources" section.

### Snippet to Insert

```markdown
### Tier 1 Context: Codebase Map

The **codebase map** (`docs/ai-agent-context/codebase-map.md`) is a lightweight navigational index of architecturally significant files. Agents should reference it to understand repo structure, domain boundaries, and key relationships without reading hundreds of files.

- Update the codebase map when significant changes occur (new domains, restructured services)
- Use `codebase-map-generator` skill to regenerate it intelligently
- Preserve user-added annotations when syncing

```

### How to Propose Change

```markdown
**Proposed change to constitution.md**:

Add this section under "Context & Memory" (or similar):

[SNIPPET ABOVE]

This ensures agents know to reference the map as their first navigational tool.
```

---

## Template 2: CLAUDE.md Reference

**Location**: In "Key Files" or "Architecture Overview" section.

### Snippet to Insert

```markdown
### Codebase Navigation

- **Codebase Map**: `docs/ai-agent-context/codebase-map.md` — Directory trees, domain groupings, and architectural relationships. Start here to understand structure.
- **Architecture Docs**: `docs/ai-agent-context/` — Detailed flow diagrams, database schema, infrastructure patterns.
- **Specifications**: `.kiro/specs/` and `docs/specs/` — Feature specs, requirements, contracts.

```

### Alternative (Concise)

```markdown
**Codebase Navigation**: See `docs/ai-agent-context/codebase-map.md` for structure; `docs/ai-agent-context/` for details.
```

### How to Propose Change

```markdown
**Proposed change to CLAUDE.md**:

In the "Key Files" section, add:

[SNIPPET ABOVE]

This makes codebase-map.md the first place agents look for orientation.
```

---

## Template 3: .ruler/AGENTS.md Reference

**Location**: In "Key References" section (if exists) or new section "Navigation".

### Snippet to Insert

```markdown
### Navigation

Agents should always start with `docs/ai-agent-context/codebase-map.md` to understand:
- Directory structure and domain boundaries
- Architectural relationships and data flow
- Where to find specific services or infrastructure

When implementing features across domains, reference the codebase map to validate:
- Domain dependencies (no circular imports)
- Correct layer usage (feature → data-access → util)
- Which shared libraries to import from

```

### How to Propose Change

```markdown
**Proposed change to .ruler/AGENTS.md**:

Add this section near the top (after "Overview"):

[SNIPPET ABOVE]

This ensures all agents understand the navigational hierarchy.
```

---

## Template 4: .claude/plugin-config.md or Plugin Settings

**Location**: If you have custom Claude Code plugin configuration.

### Snippet to Insert

```markdown
### Context Hierarchy (Tier 1, Tier 2, Tier 3)

**Tier 1 (Always loaded)**:
- `.ruler/AGENTS.md` — Project rules
- `docs/ai-agent-context/codebase-map.md` — Navigational index

**Tier 2 (Per-feature upload)**:
- Repomix configs for deep domain work (uploaded ad-hoc)

**Tier 3 (On-demand)**:
- GitHub project_knowledge_search for code, files, patterns

```

### How to Propose Change

```markdown
**Proposed change to plugin settings**:

Document the new codebase-map.md as a Tier 1 always-loaded file.
```

---

## Template 5: .kiro/specs/ or docs/specs/ Reference

**Location**: If you use specification-driven development.

### Snippet to Insert

```markdown
## Implementation Guidelines

Before implementing a feature:

1. Read the feature spec (e.g., `docs/specs/[feature]/`)
2. Review the codebase map (`docs/ai-agent-context/codebase-map.md`) to understand where domain logic lives
3. Verify module boundaries using architecture docs
4. Check related domain services for reuse opportunities

```

### How to Propose Change

```markdown
**Proposed change to spec template or docs/specs/ README**:

Add a "Before You Code" section referencing codebase-map.md as the first step.
```

---

## Template 6: README.md Update

**Location**: In "Getting Started" or "Architecture" section.

### Snippet to Insert

```markdown
### Understanding the Structure

Start with the **[codebase map](docs/ai-agent-context/codebase-map.md)** for a lightweight overview of directories, domains, and relationships. Then dive into:

- [Architecture Docs](docs/ai-agent-context/) — Detailed flows, database schema, infrastructure
- [Specifications](.kiro/specs/) — Feature requirements and contracts
- [Project Memory](CLAUDE.md) — Coding standards and decisions

```

### How to Propose Change

```markdown
**Proposed change to README.md**:

Add this section to the "Getting Started" area to guide new contributors.
```

---

## Proposed Change Preview Format

When presenting to user, use this format:

```markdown
## Proposed Doc Updates

I found these files that could reference the new codebase-map.md:

### Option 1: constitution.md
**Change**: Add "Tier 1 Context: Codebase Map" section
**Impact**: Ensures immutable rules mention map as foundational context
**Preview**:
[SHOW SNIPPET]

### Option 2: CLAUDE.md
**Change**: Add codebase-map.md to "Key Files" section
**Impact**: Makes map Claude Code's first reference for navigation
**Preview**:
[SHOW SNIPPET]

---

**I recommend updating both (preserves context hierarchy).** 

Should I proceed with these changes?
- [ ] Yes, both
- [ ] Only CLAUDE.md
- [ ] Only constitution.md
- [ ] None, just save the map
```

---

## Sync Guidelines (When Regenerating)

If the codebase-map.md is updated and you're syncing related docs:

1. **Only update references, not full docs**. Don't rewrite constitution.md or CLAUDE.md.
2. **Preserve user additions**. If they've added custom guidance, keep it.
3. **Check staleness**. If reference is >6 months old or references moved domains, update path.
4. **Ask before executing**. Always preview and request consent.

Example sync logic:

```markdown
**When syncing docs after map regen**:

- If domain name changed in map: Update reference in docs to use new name
- If new domain added to map: Mention it in "Navigation" sections of docs
- If domain deleted from map: Remove or update stale references
- If file path changed: Update map reference path in docs

Always preserve user-written guidance and custom sections.
```

---

## Context Window Awareness

Remember: Users want Tier 1 files compact. When proposing updates:

- **Don't add long sections** (max 5 lines per reference)
- **Don't duplicate the map** (reference it, don't copy)
- **Don't force updates** (user decides which files to update)
- **Respect existing structure** (adapt to existing doc patterns, don't reformat)

Example concise reference (good):
```markdown
**Codebase Structure**: See `docs/ai-agent-context/codebase-map.md` for domain overview.
```

Example bloated reference (avoid):
```markdown
The codebase is organized into domains. To understand the structure, you should read the codebase map file which contains a directory tree, domain sections, and architectural relationships. This file is located at...
```
