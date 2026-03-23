---
name: codebase-map-generator
description: Create, regenerate, and maintain codebase maps as Tier 1 project context files. Use when "create a codebase map", "regenerate the codebase map", "sync the codebase map", "update my project's navigation index", or need a living navigational index to help agents quickly find code. Supports smart detection of tech stack and domain boundaries, socratic probing for discrepancies, user editing with intelligent sync, and post-creation updates to CLAUDE.md and related project docs. Handles monorepos, microservices, traditional single-repo layouts, and language-agnostic projects.
---

# Codebase Map Generator

Create and maintain lightweight, agent-navigational codebase maps that serve as Tier 1 project context. Maps are spartan indices—directory trees, domain groupings, and relationship summaries—not exhaustive code catalogs. A single codebase map in context leaves 90% of the window open for work.

## Core Workflow

### Phase 1: Repository Shape Detection

Scan directory structure and detect tech stack:

1. **Glob file patterns** to identify languages, package managers, frameworks, database schemas, infrastructure code
2. **Analyze key config files** (package.json, tsconfig.json, go.mod, schema.prisma, Dockerfile)
3. **Map directory layout** (monorepo, microservices, single-repo, nested applications)
4. **Identify entry points** (handlers, main functions, index files, Lambda functions)
5. Present findings to user for validation

### Phase 2: Socratic Probing

Validate detected structure against reality:

1. Ask clarifying questions on domain boundaries, naming conventions, optional sections
2. Gather architectural focus areas (which domains matter most)
3. Confirm map location and user preferences
4. Store responses for templating

### Phase 3: Domain & Relationship Mapping

Extract relationships and group files into domains:

1. Use import/export patterns to identify service boundaries and dependencies
2. Group files into logical domains (auth, billing, chat, data-access, etc.)
3. Build dependency graph (Domain A → Domain B exports)
4. Extract public APIs and entry points per domain
5. Note infrastructure, database, and configuration patterns

### Phase 4: Map Generation & Preview

Build markdown in artifact:

1. Render directory tree focused on architecturally significant paths
2. Create domain sections (files + 1-line purposes, key relationships)
3. Add architectural relationships section (dependency graph)
4. Include optional sections (database schema, infrastructure, config)
5. Display in artifact for user preview and iteration

### Phase 5: User Iteration

Allow refinement before finalization:

1. User can suggest edits: rename domains, remove/add sections, adjust emphasis
2. Update artifact in real-time as feedback arrives
3. Validate consistency (e.g., ensure all referenced domains exist)

### Phase 6: Finalization & Post-Creation

Write map and offer doc updates:

1. Write final map to user-chosen location (default: `docs/ai-agent-context/codebase-map.md`)
2. Identify relevant "always-in-context" files (constitution.md, CLAUDE.md, .ruler/AGENTS.md)
3. Preview proposed changes to max 2 files (user chooses which)
4. Execute updates with explicit consent only

---

## Tool Integration

### Tech Stack Detection (Glob)

Scan for language, framework, and structure patterns. Reference `references/tech-stack-patterns.md` for complete glob patterns per ecosystem.

Examples:
```
package.json, pnpm-workspace.yaml → JavaScript/TypeScript monorepo
go.mod → Go project
schema.prisma → Prisma ORM
infrastructure/, cdk.out/ → Infrastructure as Code
apps/, libs/ → monorepo structure
```

Run glob sequentially for different file types to avoid noise. After glob results, validate with `git ls-files | wc -l` to ensure coverage.

### Code Analysis (Grep)

Identify domain boundaries and service dependencies:

```
export (interface|type|class|function|Service) → public API
import.*from.*[domain]/feature/src → domain imports
constructor\(private.*Service\) → dependency injection
export default → barrel exports
```

For each detected domain (e.g., `libs/auth/feature`):
1. Grep for `import.*@domain` → what this domain consumes
2. Grep for `export.*Service|export interface` → what this domain exposes

Build a directed graph: Domain A depends on → Domain B.

### Config & Entry Point Examination (Read)

Extract architecture metadata from key files:

1. **package.json**: workspace structure, scripts, key dependencies, Node version
2. **tsconfig.json / go.mod**: module resolution, path aliases, build config
3. **schema.prisma / database.sql**: models, tables, relationships (list names only, not full schema)
4. **App entry files** (apps/api/src/main.ts, cmd/main.go): handler patterns, middleware structure
5. **Existing docs** (.claude/AGENTS.md, constitution.md): capture existing architectural guidance

### Staleness & Sync (Bash)

When regenerating an existing codebase-map:

```bash
# Files modified recently
git log --pretty=format: --name-only --since="90 days ago" | sort -u

# Deleted files (for pruning stale domains/files)
git diff HEAD~1 --name-status | grep "^D"

# Last commit per directory
git log --pretty=format=%ai -1 -- [path]
```

**Sync Rules** (explicit, not fuzzy):
- **If a file/domain no longer exists**: Remove from map
- **If a file path changed or partially stale**: Update with current path + note changes
- **If new files/domains added**: Add sections + integrate into flow
- **If user edited sections**: Preserve inline comments/annotations, update facts only

### Socratic Probing (AskUserQuestion)

Ask concrete questions to validate detection. Reference `references/socratic-prompts.md` for exact question text.

Example workflow:
```
Q1: Domain boundaries
> "I detected these top-level groupings: [list]. Are these your core domains?"
Options: Accept / Rename / Manual specify

Q2: Naming preferences
> "Should I call sections 'libs/auth/feature' or 'Auth Domain'?"
Options: Path-accurate / Concise

Q3: Optional sections
> "I found Prisma schema / CDK. Include database/infrastructure sections?"
Options: Yes / No

Q4: Architectural focus
> "Which 3 areas matter most for agent navigation?"
Options: [checkboxes from detected domains + config areas]

Q5: Map location
> "Where should I save this?"
Options: docs/ai-agent-context/codebase-map.md / Custom path
```

Store responses in memory for rendering logic.

### Map Rendering (Artifacts)

Generate markdown in artifact:

```markdown
# [Project Name] Codebase Map

> Navigational index of architecturally significant files. Code is source of truth.

## File Tree

[Directory tree, ~30-50 lines, focused on architecturally significant paths]

---

## [Domain 1 Name]

[3-8 key files with 1-line purposes]

**Relationships**: [brief mention of what this domain depends on]

---

[Additional domain sections in priority order]

---

## Architectural Relationships

[Dependency graph: Domain A → Domain B → etc.]

---

## [Optional] Database Schema

[Table names + key relationships, no full DDL]

## [Optional] Infrastructure

[Top-level stacks, deployment units, key services]

## [Optional] Configuration

[Key env vars, config sources, feature flags]
```

Present with prompt:
> "Preview of your codebase map. Refine section titles, add/remove domains, or adjust content? I'll update the artifact in real-time."

Update artifact live as user provides feedback.

### Dynamic Template Bundling

Templates adapt to detected tech stack and structure. Reference `references/section-templates.md`.

**Template selection logic**:
1. **Monorepo + TypeScript** → Use Nx/pnpm workspace template
2. **Microservices + Go** → Use service-per-repo template
3. **Single-repo + Python** → Use Django/FastAPI app template
4. **Hybrid** → Combine templates per actual structure

Template determines:
- Directory tree depth (monorepos need more depth)
- Domain section structure (service classes vs. modules vs. packages)
- Relationship notation (imports vs. HTTP calls vs. data flow)

---

## Output Specifications

### Directory Tree Section

Minimal tree focusing on architectural significance. Example depth: 3-4 levels max.

```
benefitly/
├── apps/              # Application shells
│   ├── api/           # User-facing Lambda API
│   └── web/           # React SPA frontend
├── libs/              # Business logic + shared code
│   ├── auth/feature/  # Authentication domain
│   └── shared/        # Shared infrastructure
├── infrastructure/    # CDK stacks + AWS config
└── docs/              # Documentation + CLAUDE.md
```

Not a comprehensive file listing—only paths needed for agent navigation.

### Domain Sections

For each significant domain:

```
## [Domain Name]

\`\`\`
libs/[domain]/feature/src/
├── services/         # Business logic
├── types/            # Type definitions
├── middleware/       # (if applicable)
└── index.ts
\`\`\`

**Key files**:
- `[file].ts` → Purpose (1 line)
- `[file].ts` → Purpose (1 line)

**Relationships**: [Brief note of outbound dependencies or what depends on this domain]
```

### Architectural Relationships

Arrow notation or bullet list showing how domains connect:

```
User Request → API (apps/api)
  → Chat Service (libs/chat/feature)
    → RAG Context (libs/plan/feature)
      → PGVector Search (libs/shared/data-access/pgvector)
    → Bedrock Client (libs/shared/util/bedrock)
```

Or dependency summary:
- Chat depends on Plan (for RAG context), User (for context), Billing (for feature gates)
- Plan depends on Data Access (Prisma), Shared Utils (encryption, S3)

### Optional Sections

Include only if user selects + content exists:

**Database Schema**:
```
## Database

**Models** (via Prisma):
- User, Organization, Membership → Multi-tenancy
- Plan, Document → RAG documents
- Conversation, Message → Chat history
- Subscription → Stripe integration
```

**Infrastructure**:
```
## Infrastructure (AWS CDK)

- **API Stack**: Lambda (api, admin-api), API Gateway, WebSocket
- **Data Stack**: Aurora DSQL, Aurora PostgreSQL (pgvector), DynamoDB
- **Storage**: S3 (PDF documents, embeddings cache)
- **Processing**: Step Functions (document pipeline), SQS, Lambda workers
- **Auth**: Cognito
```

**Configuration**:
```
## Key Configuration

- **Feature flags**: DynamoDB-backed, evaluated per user/org/tier
- **Model selection**: Llama 4 Maverick/Scout, configurable via env
- **Rate limits**: Per-endpoint, DynamoDB-backed
- **Plan tiers**: Free, Lite, Pro, Enterprise (Stripe-backed)
```

---

## Post-Creation Doc Updates

### Identifying Relevant Files

Scan project for "always-in-context" files:

1. **constitution.md** — Immutable foundational rules (programming language, testing, architecture)
2. **CLAUDE.md** — Project root guidelines (coding standards, architecture decisions, review checklists)
3. **.ruler/AGENTS.md** — Agent instructions (rules enforced by hooks, module boundaries)
4. **.kiro/specs/** — Specification documents
5. **.claude/** — Plugin config, custom skills, project settings

### Proposing Changes

For max 2 files user selects:

1. **constitution.md**: Add reference to codebase map as Tier 1 context
   - Insert 1-2 lines mentioning codebase-map.md as navigational index
2. **CLAUDE.md**: Add codebase map reference in "Key Files" section
   - Update relevant architecture docs pointers
3. **.ruler/AGENTS.md**: Update module boundary references if domains changed

### Preview & Consent

Show user proposed changes:

```markdown
Proposed updates:

**constitution.md**:
- Add: "Tier 1 Context: See docs/ai-agent-context/codebase-map.md for navigational index"

**CLAUDE.md**:
- Update "Key References" section to cite codebase-map.md

Proceed with these updates?
[Yes / No / Selective]
```

Only execute with explicit consent. Preserve any user-added content in updated files.

---

## Critical Guidelines

**DO**:
- Detect tech stack automatically; don't assume language
- Ask clarifying questions on domain boundaries—discrepancies break agent navigation
- Make directory trees and domains semi-required, but structure flexible
- Support user editing with smart sync during regeneration (facts update, user edits preserved)
- Offer doc updates without pushing—user decides scope
- Use imperative voice: "Scan for X", "Detect domains", not "Claude will scan"

**DO NOT**:
- Over-analyze code logic (map structure, not implementation details)
- Force a template onto repos with non-standard patterns
- Skip socratic probing—validation matters
- Assume directory structure = domains without checking imports
- Auto-update external docs without explicit user consent
- Include every file (spartan indices only)

---

## Example Triggers

- "Create a codebase map for this repo"
- "Regenerate the codebase map—things have changed"
- "Sync the codebase map with recent commits"
- "Build a navigation index so agents can find code"
- "Update my project's codebase map and reference it in CLAUDE.md"
