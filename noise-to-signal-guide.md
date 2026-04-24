# The Perfect Claude Code Setup — Universal Edition
> "Noise to Signal" — Configuring Any Repository for Claude Code

*Evolved from the Aegient reference implementation. Universalized for any team, any stack, any repo state.*

---

## Table of Contents

1. [Why This Exists](#1-why-this-exists)
2. [Universal Directory Structure](#2-universal-directory-structure)
3. [Reference Architectures](#3-reference-architectures)
4. [CLAUDE.md — The Brain](#4-claudemd--the-brain)
5. [.claudeignore — The Filter](#5-claudeignore--the-filter)
6. [.claude/rules/ — Deterministic Guidelines](#6-clauderules--deterministic-guidelines)
7. [.claude/skills/ — Progressive Disclosure Knowledge](#7-claudeskills--progressive-disclosure-knowledge)
8. [.claude/agents/ — Specialized Subagents](#8-claudeagents--specialized-subagents)
9. [.claude/org/ — Tribal Knowledge](#9-claudeorg--tribal-knowledge)
10. [.claude/settings.json — Hooks & Configuration](#10-claudesettingsjson--hooks--configuration)
11. [MCP Server Configuration](#11-mcp-server-configuration)
12. [design/ — Design Artifacts](#12-design--design-artifacts)
13. [docs/agentic/ — Agent-Optimized Reference Docs](#13-docsagentic--agent-optimized-reference-docs)
14. [Memory Management & Parallel Agent Safety](#14-memory-management--parallel-agent-safety)
15. [Context Management](#15-context-management)
16. [Composability — How It All Connects](#16-composability--how-it-all-connects)
17. [The Quality Skills: audit, sync, scaffold, map](#17-the-quality-skills-audit-sync-scaffold-map)
18. [The "Noise to Signal" Talk Guide](#18-the-noise-to-signal-talk-guide)
19. [Quick Setup Checklist](#19-quick-setup-checklist)
20. [Anti-Patterns](#20-anti-patterns)

---

## 1. Why This Exists

Claude Code is only as good as the signal you give it.

In an unconfigured repository, every Claude session starts cold. Claude must rediscover your architecture, your patterns, your gotchas — every single time. A 200,000-token context window with 2,000 tokens of relevant signal is a 1% efficiency machine.

This guide converts your repository from noise to signal. After setup:
- Claude knows your structure, conventions, and constraints without being told
- Your agentic docs stay current automatically
- Any team member can run one command to configure any repo
- The setup maintains itself

**The core insight:** CLAUDE.md is advisory (~80% compliance). Hooks are deterministic (100%). Skills are on-demand knowledge. Agents are isolated specialists. Once you understand which layer belongs where, the setup is obvious.

**Who this is for:** Any team, any stack, any repo state — including inherited messes.

---

## 2. Universal Directory Structure

```
[repo-root]/
├── CLAUDE.md                          # Root brain (size varies by repo type — see §4)
├── .claudeignore                      # Context exclusion filter
├── .claude/
│   ├── settings.json                  # Hooks, permissions, model config
│   ├── settings.local.json            # Personal overrides (gitignored)
│   ├── rules/                         # Always-loaded guidelines (max 5 files, ≤50 lines each)
│   │   ├── code-standards.md
│   │   ├── testing.md
│   │   ├── git-workflow.md
│   │   ├── architecture.md            # Only if architectural rules are complex
│   │   └── [compliance].md            # Only if regulated (HIPAA, SOC2, GDPR, etc.)
│   ├── skills/                        # On-demand knowledge (progressive disclosure)
│   │   ├── agentic/
│   │   │   └── repo/
│   │   │       └── quality/
│   │   │           ├── audit/SKILL.md     # Visual compliance report
│   │   │           ├── sync/SKILL.md      # Automated configuration sync
│   │   │           ├── scaffold/SKILL.md  # Bootstrap new or inherited repos
│   │   │           └── map/SKILL.md       # Regenerate CODEBASE-MAP.md
│   │   ├── [domain]-conventions/SKILL.md  # e.g., api-conventions, db-patterns
│   │   ├── debug/SKILL.md
│   │   └── research/SKILL.md
│   ├── agents/                        # Specialized subagents
│   │   ├── explorer.md                # Always include this one
│   │   ├── architect.md               # Optional: for complex architecture decisions
│   │   ├── security-reviewer.md       # Optional: for compliance-sensitive repos
│   │   └── [domain]-specialist.md     # Optional: domain-specific experts
│   ├── hooks/                         # Hook scripts (all chmod +x)
│   │   ├── block-dangerous.sh
│   │   ├── format-on-edit.sh
│   │   ├── typecheck-on-edit.sh       # Only for typed languages
│   │   ├── verify-tests-on-stop.sh
│   │   └── session-context-loader.sh
│   ├── org/                           # Org/team tribal knowledge (not gitignored)
│   │   ├── procedures.md              # Release, hotfix, on-call procedures
│   │   ├── deviations.md              # "We deviate from standard because..."
│   │   ├── nuance.md                  # "Things that will surprise you"
│   │   ├── team-contacts.md           # Who owns what
│   │   └── secrets-protocol.md        # How to reference secrets safely
│   └── agent-memory/                  # Per-agent accumulated knowledge
│       └── [agent-name]/MEMORY.md     # Managed by agents with memory: project
│
├── design/                            # Design artifacts (human + agent readable)
│   ├── system/                        # System design docs, C4 diagrams, flow charts
│   ├── api/                           # API design: OpenAPI, gRPC protos, GraphQL schemas
│   ├── data/                          # ERDs, schema diagrams, migration plans
│   ├── ui/                            # UI/UX docs, wireframes, design system references
│   ├── decisions/                     # ADRs (supersedes or mirrors docs/agentic/DECISIONS.md)
│   └── experiments/                   # Design spikes, POCs, proposals under consideration
│
├── docs/
│   ├── agentic/                       # Agent-optimized reference (spartan, navigational)
│   │   ├── CODEBASE-MAP.md            # Auto-maintained by :map skill
│   │   ├── ARCHITECTURE.md            # System design (spartan)
│   │   ├── DATA-MODEL.md              # Schema index → schemas/ for detail
│   │   ├── API-CONTRACTS.md           # Endpoint/contract specifications
│   │   ├── MIGRATIONS.md              # Pending + recent schema migrations
│   │   ├── DECISIONS.md               # ADR log
│   │   ├── schemas/                   # Per-domain schema files
│   │   │   ├── [domain-a]-schema.md
│   │   │   └── shared-schema.md
│   │   ├── compliance/                # Compliance docs (if regulated)
│   │   │   ├── [framework]/
│   │   └── pipeline/                  # Stage artifacts for multi-agent pipelines
│   │       ├── STAGE-CONTRACT.md
│   │       └── stage-[N]-[name].md
│   └── human/                         # Full prose docs for humans
│
├── apps/                              # [Monorepo only] Runnable applications
│   └── [app-name]/
│       ├── CLAUDE.md                  # App-specific context (≤40 lines)
│       └── src/
│
├── libs/  OR  packages/               # [Monorepo only] Shared domain logic
│   └── [domain]/[type]/
│       └── CLAUDE.md                  # High-impact libs only (≤20 lines)
│
└── src/                               # [Monolith only] Source root
    └── [domain]/
        └── CLAUDE.md                  # Only if domain > 10k lines with distinct patterns
```

---

## 3. Reference Architectures

### 3.1 Monorepo (apps/libs) — NX, Turborepo, Lerna, or Custom

**Repo detection signals:** `nx.json`, `turbo.json`, `lerna.json`, `pnpm-workspace.yaml` with multiple apps, or `apps/` + `libs/` directory pair present.

**CLAUDE.md placement:**
```
repo-root/CLAUDE.md          # ≤100 lines: org conventions, build tool, routing rules, sub-agent dispatch
apps/api/CLAUDE.md           # ≤40 lines: backend-specific gotchas, port, key patterns
apps/web/CLAUDE.md           # ≤40 lines: frontend-specific gotchas, port, key patterns
libs/shared/CLAUDE.md        # ≤20 lines: "⚠️ HIGH IMPACT — changes here affect all consumers"
packages/[public]/CLAUDE.md  # Only for published packages with public API contracts
```

**.claude/ placement:** Root only. Skills and agents defined here apply to all sub-projects.

> ⚠️ **Known limitation (as of March 2026):** `skills/`, `agents/`, and `commands/` do NOT auto-inherit from parent directories when Claude is launched from a subdirectory. Only `CLAUDE.md` and `settings.json` traverse ancestors. All shared skills/agents must live in the root `.claude/` and be explicitly listed in subagent `skills:` frontmatter. ([GitHub #26489](https://github.com/anthropics/claude-code/issues/26489) — open, unscheduled.)

**Build tool–agnostic commands section in root CLAUDE.md:**
```markdown
## Commands
# Replace with your actual build tool
build:  nx run-many -t build           # or: turbo build, pnpm -r build
test:   nx affected -t test            # or: turbo test, pnpm -r test
lint:   nx run-many -t lint            # or: turbo lint
serve:  nx serve [app-name]            # or: turbo dev --filter=[app]
```

**Reference directory structure:**
```
my-monorepo/
├── CLAUDE.md
├── .claudeignore
├── .claude/
├── apps/
│   ├── api/          ← shell app (NestJS, FastAPI, Express, Spring, etc.)
│   │   └── CLAUDE.md
│   └── web/          ← shell app (Next.js, Angular, React, Vue, etc.)
│       └── CLAUDE.md
├── libs/  OR  packages/
│   ├── [domain-a]/
│   │   ├── api/      ← HTTP communication services
│   │   ├── data/     ← State management
│   │   ├── domain/   ← Models, interfaces, business rules
│   │   ├── feature/  ← Smart components / use cases
│   │   └── ui/       ← Presentational components
│   └── shared/       ← Cross-domain utilities
│       └── CLAUDE.md ← ⚠️ HIGH IMPACT label here
├── design/
├── docs/agentic/
└── [build-config]    ← nx.json, turbo.json, package.json workspaces
```

---

### 3.2 Monolith — Single Deployable Application

**Repo detection signals:** `src/` present, no `apps/` directory, single `package.json`/`pyproject.toml`/`go.mod` at root.

**CLAUDE.md placement:**
```
repo-root/CLAUDE.md             # ≤120 lines: all commands, src/ structure, gotchas
src/[large-domain]/CLAUDE.md    # Only if domain > 10k lines AND has distinct patterns
```

No nested CLAUDE.md proliferation. One root file with `@`-references for the two largest domains.

**Reference directory structure:**
```
my-monolith/
├── CLAUDE.md
├── .claudeignore
├── .claude/
├── src/
│   ├── [domain-a]/       ← auth, users, payments, etc.
│   │   └── CLAUDE.md     ← only if domain is large + complex
│   ├── [domain-b]/
│   ├── shared/           ← cross-domain utilities
│   ├── config/
│   └── main.[ext]        ← entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── design/
├── docs/agentic/
└── [framework-config]    ← package.json, Dockerfile, etc.
```

---

### 3.3 Poly-repo with Workspace Root

**Repo detection signals:** Multiple repositories cloned into a workspace directory, `.code-workspace` file, or top-level directory containing 5+ separate git repos.

**Pattern:** Virtual monorepo — no repo restructuring required. Purely additive.

**CLAUDE.md placement:**
```
workspace-root/CLAUDE.md        # Service map, cross-service conventions, ownership
workspace-root/.claude/         # Shared agents, shared skills — used via --add-dir
[service-repo]/CLAUDE.md        # Local service context (loaded when --add-dir is used)
```

**Usage:**
```bash
# Start Claude with cross-repo context
claude --add-dir ../workspace-root

# In a session: Claude now sees workspace CLAUDE.md + service CLAUDE.md
```

**workspace-root/CLAUDE.md template:**
```markdown
# [Org Name] Workspace

## Services
| Service | Repo | Port | Team | Purpose |
|---------|------|------|------|---------|
| auth-service | ./auth-service/ | 3001 | Platform | Authentication + sessions |
| user-service | ./user-service/ | 3002 | Platform | User profiles + preferences |
| billing-service | ./billing-service/ | 3003 | Revenue | Subscription + payments |

## Cross-Service Conventions
- Service communication: REST over HTTPS (internal) + events via [message broker]
- Auth: Bearer JWT in Authorization header. Verify with auth-service /introspect.
- Correlation IDs: X-Correlation-ID header required on all inter-service calls.

## Agent Navigation
- Full service map: workspace-root/docs/agentic/SERVICE-MAP.md
- Event catalog: workspace-root/docs/agentic/EVENT-CATALOG.md
```

---

## 4. CLAUDE.md — The Brain

**The Rule:** CLAUDE.md is advisory — Claude follows it ~80% of the time. For anything that must happen 100% of the time, use hooks. CLAUDE.md targets what Claude needs to know every single session.

**The WHY/WHAT/HOW pattern (universal template skeleton):**
```markdown
# [Project Name]
[One sentence: what this project does and why it exists]  ← WHY

[Repo type + primary stack]                              ← WHAT

## Commands                                              ← HOW
[The 4 commands used every day]

## [Structure or Architecture]
[What Claude needs to navigate the codebase]

## Standards
[The rules Claude gets wrong in this specific codebase]

## DO NOT USE
[Deprecated code, banned patterns, antipatterns under migration]

## Agent Navigation
[Pointers to docs/agentic/ files]
```

### CLAUDE.md Size Guide

| Repo State | Line Target | What to Include |
|------------|-------------|-----------------|
| Fresh/simple | 30-50 | Commands + one structure line + top 3 gotchas |
| Active project | 80-120 | Commands + architecture overview + standards + agent navigation |
| Legacy/complex | 100-150 | Add: tech debt hotspots, deprecated patterns, compliance (1-3 critical rules), sub-agent routing |

**Hard ceiling: 150 lines.** If you hit 150, move content to rules/ or skills.

> ⚠️ **Critical:** If Claude repeatedly ignores a rule even with MUST/NEVER capitalization, the file is too long. Important rules get lost in the noise.

### The "DO NOT USE" Section (highest-value addition for inherited codebases)

```markdown
## DO NOT USE
- `UserService.findAll()` — loads all records. Use `UserService.findPaginated()` instead.
- Direct database queries in controllers — use the service layer.
- `@ts-ignore` — fix the type error properly.
- The `legacy/` directory — it's being migrated. See DECISIONS.md ADR-007.
```

### Sub-Agent Routing Rules (add to monorepo/complex CLAUDE.md)

```markdown
## Sub-Agent Routing Rules

Parallel dispatch (ALL conditions must be met):
- 3+ unrelated tasks, independent domains
- No shared files between tasks
- Clear file boundaries with no overlap
- Each agent writes to RESULTS.md in its own working directory

Sequential dispatch (ANY condition triggers):
- Tasks have dependencies (B needs output from A)  
- Shared files or state (merge conflict risk)
- Unclear scope (understand before parallelizing)

Background dispatch:
- Research, analysis, audit tasks (not file modifications)
- Results aren't blocking current work
```

### Compaction Instructions (add to sessions with long-running work)

```markdown
## Compaction Instructions
When compacting, preserve:
- Full list of modified files and their current state
- Current test status (pass/fail counts)
- Active task requirements and acceptance criteria
- Any unresolved decisions or blockers
- If multi-phase: write state to docs/agentic/pipeline/session-state.md first
```

### Nested CLAUDE.md — App-Level Example

```markdown
# [App Name]
[Framework]. Port [N].

## Key Patterns
[5-8 most important patterns specific to this app]
[Things Claude consistently gets wrong here]

## Critical Paths
[The 2-3 files Claude must read before touching this app]
```

---

## 5. .claudeignore — The Filter

Keeps Claude from wasting context on noise. Same syntax as `.gitignore`.

```gitignore
# ═══════════════════════════════════════════════
# DEPENDENCIES & BUILD OUTPUTS
# ═══════════════════════════════════════════════
node_modules/
.npm/
.pnpm-store/
__pycache__/
*.pyc
.venv/
venv/
vendor/          # Go, PHP
target/          # Rust, Java
dist/
build/
out/
.next/
.nuxt/
.angular/
.svelte-kit/
coverage/
.nx/
.turbo/

# ═══════════════════════════════════════════════
# SECRETS & CREDENTIALS
# ═══════════════════════════════════════════════
.env
.env.*
*.pem
*.key
*.p12
*.pfx
.aws/
.ssh/
**/*secret*
**/*password*
**/*credential*
**/secrets/
**/.secrets/

# ═══════════════════════════════════════════════
# LOCK FILES & LARGE GENERATED FILES
# ═══════════════════════════════════════════════
package-lock.json
yarn.lock
pnpm-lock.yaml
Gemfile.lock
poetry.lock
Cargo.lock
*.lock
*.tfstate*
*.tfstate.backup

# ═══════════════════════════════════════════════
# MEDIA & BINARY ASSETS
# ═══════════════════════════════════════════════
**/*.png
**/*.jpg
**/*.jpeg
**/*.gif
**/*.webp
**/*.svg
**/*.ico
**/*.woff*
**/*.ttf
**/*.eot
**/*.mp4
**/*.mp3
**/*.pdf

# ═══════════════════════════════════════════════
# TEST ARTIFACTS (load on demand)
# ═══════════════════════════════════════════════
**/__snapshots__/
**/fixtures/large/
**/*.snap

# ═══════════════════════════════════════════════
# CI/CD (re-add specific files as needed)
# ═══════════════════════════════════════════════
.github/
.circleci/
.gitlab-ci.yml
.drone.yml
Jenkinsfile

# ═══════════════════════════════════════════════
# IDE
# ═══════════════════════════════════════════════
.idea/
.vscode/settings.json
*.swp
.DS_Store

# ═══════════════════════════════════════════════
# AGENT ARTIFACTS (prevent context feedback loops)
# ═══════════════════════════════════════════════
docs/agentic/pipeline/
.claude/agent-memory-local/
.claude/worktrees/

# ═══════════════════════════════════════════════
# HUMAN DOCS (agents use docs/agentic/)
# ═══════════════════════════════════════════════
docs/human/
```

> ⚠️ **Security note:** `.claudeignore` protects from accidental reads, but agents with bash access can still `cat` excluded files. The `block-dangerous.sh` hook must also block `cat .env*`, `cat *.key`, `cat *.pem` to fully enforce the boundary.

---

## 6. .claude/rules/ — Deterministic Guidelines

Rules load automatically into every session. Each file should be focused and concise.

**Hard limits:** Max 5 files. Max 50 lines per file.

> ⚠️ **Context warning (GitHub #32057):** Path-scoped rules files re-inject as `<system-reminder>` blocks on every tool call, consuming up to **46% of your 200K context window** after ~20 tool calls with a large rules library. Keep rules small. Prefer skills for domain-specific knowledge that isn't needed every session.

### Rules Decision Matrix

| Content | Put Here | Why |
|---------|----------|-----|
| "Always format with Prettier" | Hook (PostToolUse) | Must happen 100% — use hook |
| "TypeScript strict, no any" | rules/code-standards.md | Convention needed every session |
| "How to write a NestJS controller" | skills/api-conventions/ | On-demand knowledge only |
| "Never log PHI" | rules/compliance.md + hook | Rule for awareness, hook to catch |
| "Use Jest for tests" | CLAUDE.md | One-liner, doesn't need its own rule |

### Universal Rules Templates

**`rules/code-standards.md`**
```markdown
---
paths: ["**/*.[jt]s", "**/*.[jt]sx", "**/*.py", "**/*.go", "**/*.rb"]
---
# Code Standards

[Fill with your team's actual standards. Template:
- Type safety: [strict mode? any allowed? how to handle unknowns?]
- Comments: [inline docs policy? zero comments? JSDoc required?]
- Naming: [conventions for variables, functions, files, modules]
- Nesting: [max depth? extract-to-function threshold?]
- Dead code: [remove immediately? leave for refactor? flag with TODO?]
]
```

**`rules/testing.md`**
```markdown
---
paths: ["**/*.spec.*", "**/*.test.*"]
---
# Testing Rules

- Structure: Given (setup) / When (action) / Then (assertion)
- Mock at boundaries only. Never mock the thing being tested.
- [Coverage target: X%]
- [Test runner command: X]
- [Test file naming convention: X]
```

**`rules/git-workflow.md`**
```markdown
# Git Workflow

- Branch naming: [feat/ | fix/ | refactor/ | chore/] + [ticket-id or description]
- Commits: [conventional commits? free-form? squash policy?]
- No force push to [main/master/develop]
- PR requires: [passing tests | lint | type check | review count]
```

---

## 7. .claude/skills/ — Progressive Disclosure Knowledge

Skills load on demand — by `/skill-name` invocation or Claude's automatic detection. They keep your context lean by only loading when relevant.

**Key distinction:**
- CLAUDE.md = always loaded every session
- rules/ = always loaded every session
- Skills = loaded only when relevant

### Skill Structure

```
.claude/skills/
├── agentic/repo/quality/       # ← The quality skill namespace (§17)
│   ├── audit/SKILL.md
│   ├── sync/SKILL.md
│   ├── scaffold/SKILL.md
│   └── map/SKILL.md
├── [domain]-conventions/       # e.g., api-conventions, db-patterns, state-management
│   ├── SKILL.md
│   └── [supporting-files]      # Templates, examples, reference material
├── debug/SKILL.md
└── research/SKILL.md
```

### Skill Frontmatter Reference

```yaml
---
description: >
  [When Claude should invoke this skill. Write for the model:
   "Use this skill PROACTIVELY when X" or "Invoke when working with Y"]
user-invocable: true          # Allows /skill-name invocation
context: fork                 # Run in isolated subagent (fork context)
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Task                      # Required for sub-agent dispatch
  - Write                     # Only if skill creates files
---
```

### SKILL.md Document Header (universal standard)

Every agentic document — including skills — should include this header for staleness detection:

```markdown
---
agent-load: [when to load this: "when working in [domain]" or "for [trigger condition]"]
last-updated: YYYY-MM-DD
update-trigger: [specific event that invalidates this doc]
staleness-check: [bash command that verifies doc is still accurate]
token-cost: ~N lines (~Xk tokens)
---
```

### Example: Debug Skill

```markdown
---
description: Deep Trace debugging. Systematic root cause analysis for complex bugs.
user-invocable: true
---

# Deep Trace: $ARGUMENTS

## Phase 1: Observe
- Reproduce the exact failure
- Capture: error message, stack trace, request/response, state
- Identify: expected vs actual behavior

## Phase 2: Hypothesize
- List 3-5 candidate root causes ranked by likelihood
- For each: what evidence would confirm/refute it?

## Phase 3: Isolate
- Write a minimal reproduction test
- Binary search through the call chain

## Phase 4: Fix
- Implement the smallest possible fix
- Verify reproduction test now passes
- Check for similar patterns elsewhere (grep for the anti-pattern)

## Phase 5: Harden
- Add regression test
- If pattern is common, add rule to .claude/rules/
```

---

## 8. .claude/agents/ — Specialized Subagents

Subagents get their own context windows, tool restrictions, and system prompts. Use them to isolate concerns and keep the main thread clean.

### Subagent Frontmatter Reference

```yaml
---
name: [agent-name]            # Unique ID, lowercase-hyphen
description: >
  [When Claude should invoke. "PROACTIVELY" triggers auto-invocation.
   Be specific: what tasks, what files, what conditions]
model: sonnet                 # haiku (fast/cheap) | sonnet (balanced) | opus (complex reasoning)
tools:                        # Explicit tool list. Omit = inherits all session tools.
  - Read
  - Grep
  - Glob
memory: project               # user | project | local | (omit for none)
isolation: worktree           # Add for agents that write files
background: false             # true = always run async
---
```

> ⚠️ **Memory safety for parallel agents:** If you dispatch multiple instances of the same named agent in parallel, ALL instances write to the same `.claude/agent-memory/<name>/MEMORY.md` file. Last write wins. Silent data loss. **Solution:** Strip `memory:` from any agent you dispatch in multiples. Have each write to `RESULTS.md` in its worktree-local working directory. Run a sequential consolidator after the fleet completes.

### The Explorer Agent (always include)

```markdown
---
name: explorer
description: Reconnaissance agent. Scans codebase to build context before implementation.
             Use for unfamiliar areas, large refactors, or cross-domain changes.
tools: [Read, Grep, Glob, Bash]
context: fork
---

Your job: build a focused context map for a specific task.

1. Start from docs/agentic/CODEBASE-MAP.md
2. Identify files relevant to the task
3. Read key files: exports, dependencies, patterns
4. Return a spartan summary:
   - Files involved (paths only)
   - Key interfaces/types
   - Current patterns in use
   - Dependencies to be aware of
   - Potential conflicts or gotchas

Keep output under 50 lines. Main thread context is precious.
```

### Agent Scope Rules

- **Project agents** (`.claude/agents/`) — Specific to this codebase. Check into version control.
- **User agents** (`~/.claude/agents/`) — Personal agents available in all projects.
- **Scope conflict:** Project agents take precedence over user agents with the same name.
- **Depth limit:** Agents cannot spawn other agents (depth=1 enforced). Design orchestration in the main session.

---

## 9. .claude/org/ — Tribal Knowledge

The "day one new hire" section. Things that belong nowhere else.

```
.claude/org/
├── procedures.md          # Release, hotfix, on-call, deployment procedures
├── deviations.md          # "We deviate from [standard] because [reason]"
├── nuance.md              # "Things that will surprise you about this repo"
├── team-contacts.md       # Who owns what domains/services (for escalation context)
└── secrets-protocol.md   # How to reference secrets without handling them directly
```

**Not gitignored by default.** These files are valuable team knowledge that should be version-controlled. If your org requires it, add `.claude/org/secrets-protocol.md` to `.gitignore`.

**`.claude/org/nuance.md` template:**
```markdown
# Repo Nuance & Gotchas

## Things That Will Surprise You
- [gotcha 1: e.g., "The `legacy/` directory is not deprecated — it's a specific module name"]
- [gotcha 2: e.g., "Tests run in band (no parallel) because of database state"]
- [gotcha 3: e.g., "Port 3001 is used by the mock server in tests — don't use it for dev"]

## Why We Did [Unconventional Thing]
- [decision + reason: e.g., "We vendor dependencies because of air-gapped CI environment"]

## Migration In Progress
- [what's being migrated: from → to, rough ETA, files not yet migrated]
```

---

## 10. .claude/settings.json — Hooks & Configuration

**The rule:** Suggestion → CLAUDE.md. Requirement → Hook. External service → MCP. Reusable workflow → Skill.

Hooks are deterministic (100%). CLAUDE.md is advisory (~80%). When something must happen every time without exception, use a hook.

### Universal settings.json

```json
{
  "permissions": {
    "allow": [
      "Read", "Grep", "Glob",
      "Bash(git status)", "Bash(git diff *)", "Bash(git log *)",
      "Bash(cat *)", "Bash(ls *)", "Bash(find *)", "Bash(grep *)",
      "Bash(head *)", "Bash(tail *)", "Bash(wc *)", "Bash(echo *)",
      "Bash(mkdir *)", "Bash(cp *)", "Bash(mv *)",
      "[Bash(YOUR-BUILD-TOOL *)  e.g. Bash(nx *) or Bash(npm run *)]"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(*DROP TABLE*)",
      "Bash(*TRUNCATE*)",
      "Bash(*--force*)",
      "Bash(curl * | bash)",
      "Bash(wget * | bash)",
      "Bash(cat .env*)",
      "Bash(cat *.key)",
      "Bash(cat *.pem)"
    ]
  },
  "model": "sonnet",
  "hooks": {
    "SessionStart": [{
      "matcher": ".*",
      "hooks": [{ "type": "command", "command": ".claude/hooks/session-context-loader.sh" }]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": ".claude/hooks/block-dangerous.sh" }]
    }],
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [
        { "type": "command", "command": ".claude/hooks/format-on-edit.sh" },
        { "type": "command", "command": ".claude/hooks/typecheck-on-edit.sh" }
      ]
    }],
    "Stop": [{
      "hooks": [{ "type": "command", "command": ".claude/hooks/verify-tests-on-stop.sh" }]
    }]
  }
}
```

### Hook Scripts

**`session-context-loader.sh`** — Inject dynamic context at session start:
```bash
#!/bin/bash
echo "Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
echo "Modified: $(git status --porcelain 2>/dev/null | wc -l | tr -d ' ') files"
echo "Last commit: $(git log --oneline -1 2>/dev/null || echo 'none')"
```

**`block-dangerous.sh`** — Security gate (universal patterns):
```bash
#!/bin/bash
COMMAND=$(cat | jq -r '.tool_input.command // empty')
for pattern in "rm -rf /" "rm -rf ~" "DROP TABLE" "TRUNCATE TABLE" \
               "--force-with-lease" "--force" "curl.*|.*sh" "wget.*|.*sh" \
               "cat .env" "cat *.key" "cat *.pem" "chmod 777"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    jq -n --arg reason "Blocked: $pattern" \
      '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $reason}}'
    exit 0
  fi
done
exit 0
```

**`format-on-edit.sh`** — Auto-format on file write:
```bash
#!/bin/bash
FILE=$(cat | jq -r '.tool_input.file_path // .tool_input.path // empty')
if [ -n "$FILE" ]; then
  # Adapt to your formatter
  case "$FILE" in
    *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.scss|*.html)
      npx prettier --write "$FILE" 2>/dev/null ;;
    *.py)
      black "$FILE" 2>/dev/null ;;
    *.go)
      gofmt -w "$FILE" 2>/dev/null ;;
  esac
fi
exit 0
```

**`verify-tests-on-stop.sh`** — Block completion if tests fail:
```bash
#!/bin/bash
INPUT=$(cat)
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then exit 0; fi
# Adapt to your test runner
RESULT=$(YOUR-TEST-COMMAND 2>&1)
if echo "$RESULT" | grep -qE "FAIL|ERROR|failed"; then
  echo '{"decision": "block", "reason": "Tests are failing. Fix before completing."}'
  exit 2
fi
exit 0
```

---

## 11. MCP Server Configuration

### Scope Matrix (Universal)

| MCP Server | Dev Default | CI Allowed | Prod Allowed |
|------------|-------------|------------|--------------|
| GitHub | Read-only | Read + PR create | Read only |
| Postgres/SQL | Read + schema | None | Never |
| Filesystem | Scoped to repo | None | Never |
| AWS | Read (describe) | Targeted writes | Never |
| Slack | Read + draft | None | Never |
| Jira/Linear | Read + comment | Read only | Read only |
| Context7 | Full | Full | None |
| Playwright | Full | Full | Never |

### Universal MCP Recommendations

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx", "args": ["-y", "@context7/mcp-server"],
      "description": "Framework/library docs. Use before coding with any external API."
    },
    "github": {
      "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "[read-only PAT]" },
      "description": "GitHub issues, PRs, code search. Read-only by default."
    },
    "filesystem": {
      "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "[repo-root]"],
      "description": "Advanced file operations. Scoped to repo root."
    }
  }
}
```

> ⚠️ **Context budget warning:** Every registered MCP server loads its tool descriptions whether used or not. 10 servers can consume 25,000-50,000 tokens (12-25% of your window) before you type a word. Audit with `/context`. Remove servers you don't use in the current session.

---

## 12. design/ — Design Artifacts

A `design/` directory at repo root gives design documents a permanent home and makes them accessible to agents.

```
design/
├── README.md                    # What lives here and how to use it
├── system/                      # System design: C4 diagrams, flow charts, sequence diagrams
├── api/                         # API design: OpenAPI specs, gRPC protos, GraphQL schemas
├── data/                        # Data design: ERDs, schema diagrams, migration plans
├── ui/                          # UI/UX: wireframes, mockups, design system references
├── decisions/                   # ADRs — see format below
└── experiments/                 # Design spikes, POCs, proposals under consideration
```

**Design document frontmatter (agents use this for filtering):**
```markdown
---
type: system-design | api-design | data-design | ui-design | adr | experiment
status: draft | approved | superseded | deprecated
scope: [paths this design applies to, e.g., "apps/api/src/auth/**"]
supersedes: design/decisions/ADR-003.md
---
```

### ADR Format (Universal)

```markdown
## ADR-[NNN]: [Decision Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-NNN
**Deciders:** [Team / Person]

### Context
[1-3 sentences: the problem or situation forcing a decision]

### Decision
[1-2 sentences: what was decided]

### Consequences

**Positive:**
- [what this enables]

**Negative / Constraints:**
- [what this costs or constrains going forward]

### Alternatives Considered
| Option | Why Rejected |
|--------|-------------|
| [alt1] | [reason] |
| [alt2] | [reason] |
```

**Key principle:** Every major architectural choice — including "why we kept the legacy approach" and "why we chose NOT to use X" — belongs as an ADR. Agents reading `DECISIONS.md` should be able to answer "why does this work this way?" without asking.

---

## 13. docs/agentic/ — Agent-Optimized Reference Docs

These documents are the agent's navigational system. They must be **spartan**, **navigational**, and **current**. Prose belongs in `docs/human/`.

### Document Health Standard

Every agentic document includes a staleness detection header:

```markdown
---
last-updated: YYYY-MM-DD
update-trigger: [specific event: new app/lib, schema migration, major refactor]
staleness-check: find . -path "[key-path]*" -maxdepth 6 | head -3
token-cost: ~N lines (~Xk tokens)
---
```

The `agentic:repo:quality:audit` skill runs `staleness-check` commands and flags documents where the command returns empty results (referenced paths no longer exist).

### Document Tiers

| Tier | Files | Maintained By | Staleness Tolerance |
|------|-------|---------------|---------------------|
| 1 — Auto-generated | CODEBASE-MAP.md | `:map` skill (run in CI) | 0 days |
| 2 — On structural change | ARCHITECTURE.md, DATA-MODEL.md, schemas/ | Hooks + developer | 30 days |
| 3 — On decision/change | DECISIONS.md, design/**, API-CONTRACTS.md | Developer | 90 days |

### CODEBASE-MAP.md Format

```markdown
---
last-updated: YYYY-MM-DD
update-trigger: new app, lib, package, or major structural change
staleness-check: find apps libs packages src -maxdepth 1 -type d 2>/dev/null | wc -l
---

# Codebase Map

> Auto-generated by agentic:repo:quality:map

## Apps / Services
| Name | Path | Port | Framework | Purpose |
|------|------|------|-----------|---------|
| api | apps/api/ | 3000 | NestJS | REST API |

## Libraries / Packages
| Name | Path | Type | Depends On |
|------|------|------|------------|
| auth-domain | libs/auth/domain/ | domain | — |

## Key File Locations
| What | Path |
|------|------|
| Entities/Models | libs/common/entities/ |
| DB Migrations | apps/api/src/migrations/ |
| Environment config | apps/*/src/config/ |

## Dependency Graph
[high-level: which apps use which libs]
```

### DATA-MODEL.md Format (Index)

```markdown
---
last-updated: YYYY-MM-DD
update-trigger: new table, schema migration, model change
---

# Data Model Index

| Domain | Schema File | Tables/Collections | Last Migration |
|--------|-------------|-------------------|----------------|
| users | schemas/users-schema.md | 4 tables | YYYY-MM-DD |

## Cross-Domain Dependencies
- users.id → referenced by N other tables
- audit_events: written by ALL domains, owned by shared-schema.md

## Cross-Store Summary
| Store | Technology | Purpose | Schema File |
|-------|-----------|---------|-------------|
| Primary DB | PostgreSQL 15 | Transactional data | schemas/sql/ |
| Cache | Redis 7 | Sessions, rate limits | schemas/cache.md |
```

### Per-Domain Schema Files

**SQL schema (`docs/agentic/schemas/[domain]-schema.md`):**
```markdown
## Table: [table_name]
**Purpose:** [one sentence — what this table stores and why]
**DO NOT STORE:** [what explicitly should NOT go here]

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid | N | gen_random_uuid() | PK |

**Indexes:** [list key indexes]
**Relationships:** [FK relationships to other tables]
**Business Rules:**
- [rule 1: e.g., "Soft delete via deleted_at — never hard delete"]
- [rule 2: e.g., "email must be normalized to lowercase before insert"]
```

**NoSQL schema (`docs/agentic/schemas/[domain]-schema.md`):**
```markdown
## Collection: [collection_name]
**Store:** [MongoDB | DynamoDB | Firestore | etc.]
**Purpose:** [one sentence]
**DO NOT STORE:** [what explicitly should NOT go here]

**Document Shape:**
- _id / pk: [type] — [description]
- [field]: [type] — [description]

**Indexes:** [list key indexes]
**Access Patterns:** [how this data is queried]
**Consistency:** [eventual | strong | session] — [implications]
```

### MIGRATIONS.md

```markdown
---
last-updated: YYYY-MM-DD
update-trigger: new migration file created or applied
---

# Migration Tracker

> Agents: CHECK THIS before generating new migration files.
> If breaking changes are pending, STOP and ask for explicit confirmation.

## ⚠️ Breaking Changes Pending
[List any migrations that require data backfill, column drops, or breaking API changes]

## Pending (must run before next deploy)
| ID | Name | Created | Affects | Notes |
|----|------|---------|---------|-------|

## Recent (last 30 days)
| ID | Name | Applied | Status |
|----|------|---------|--------|

## Rollback Instructions
[How to roll back the last migration in this codebase]
```

### DECISIONS.md (ADR Log)

```markdown
---
last-updated: YYYY-MM-DD
---

# Architecture Decision Records

## Index
| ADR | Title | Status | Date |
|-----|-------|--------|------|
| 001 | [title] | Accepted | YYYY-MM-DD |

---

[Full ADR content using the universal ADR format from §12]
```

### docs/agentic/pipeline/ — Multi-Agent Stage Artifacts

For pipelines with multiple stages (research → architecture → implementation → review → fix):

```markdown
# Stage Contract (docs/agentic/pipeline/STAGE-CONTRACT.md)

## Stage Files
Each stage writes a completion artifact. Orchestrator reads file paths, NOT content.

| Stage | Input | Writes | Consumed By |
|-------|-------|--------|------------|
| 1: Analysis | prompt | stage-01-analysis.md | Stage 2 |
| 2: Guides | stage-01-analysis.md | stage-02-guides/*.md | Stage 3 |
| 3: Execution | stage-02-guides/*.md | stage-03-status.md | Stage 4 |
| 4: Review | changed files | stage-04-findings/*.md | Stage 5 |
| 5: Fix | stage-04-findings/*.md | stage-05-pr-ready.md | Human |

## Rules
- Orchestrator holds file paths only — never content in-context
- Each fleet agent writes to RESULTS.md in its worktree working directory
- Consolidator runs sequentially after each fleet
- Loop termination: check stage-04-findings/ for 0 critical findings, or max 3 iterations
```

---

## 14. Memory Management & Parallel Agent Safety

### Memory Scope Reference

| Scope | Location | Shared Across | Safe for Parallel? |
|-------|----------|---------------|-------------------|
| `user` | `~/.claude/agent-memory/<name>/` | All projects, this machine | ❌ No |
| `project` | `.claude/agent-memory/<name>/` | All sessions in this repo | ❌ No |
| `local` | `~/.claude/agent-memory-local/<name>/` | All sessions on this machine | ❌ No |
| (none) | — | — | ✅ Yes |

> ⚠️ **Critical:** No memory scope is worktree-aware. All three scopes are shared across parallel sessions. Dispatching 5 instances of the same named agent means 5 agents writing to the same `MEMORY.md` with no locking. Last write wins. Silent data loss.

### Safe Patterns for Parallel Agent Fleets

**Pattern 1 — Strip memory, write to worktree-local files (recommended):**
```yaml
---
name: code-reviewer
tools: [Read, Grep, Glob]   # No Write = read-only, no memory conflicts
# no memory: field
---
Review the target files. Write all findings to REVIEW-RESULTS.md
in your current working directory.
```

**Pattern 2 — Role separation (readers vs. writers):**
- Parallel fleet agents: `tools: [Read, Grep, Glob]` → no Write = auto-read-only memory
- Sequential consolidator: `tools: [Read, Write, Edit]` + `memory: project` → writes after fleet completes

**Pattern 3 — Unique names for uniquely-scoped memory:**
```
code-reviewer-feat-1024     → .claude/agent-memory/code-reviewer-feat-1024/
code-reviewer-fix-987       → .claude/agent-memory/code-reviewer-fix-987/
```
Each agent gets its own memory path. Named by ticket ID at dispatch.

### Session State Handoff

For long-running work spanning multiple sessions:
```markdown
<!-- docs/agentic/pipeline/session-state.md -->
# Session State
Task: [description]
Phase: N of N — [current phase]

## Completed
- [x] [file or step] — [path]

## In Progress
- [ ] [current work]

## Blocked
- [blocker and who to contact]

## Key Decisions Made
- [decision + reason]

## Files Modified This Session
- [path] (CREATED | MODIFIED)
```

---

## 15. Context Management

### Context Budget (Typical Session)

| Layer | Tokens | % of 200K |
|-------|--------|-----------|
| System prompt | ~30,000 | 15% |
| Autocompact buffer | ~45,000 | 22% |
| CLAUDE.md | ~2,000-8,000 | 1-4% |
| rules/ (5 files × 50 lines) | ~3,000-8,000 | 1-4% |
| MCP tool schemas | ~3,000/server | ~2%/server |
| **Available for work** | **~100,000-120,000** | **50-60%** |

### Context Management Thresholds

| Usage | Action |
|-------|--------|
| 0-50% | Work freely |
| 50-70% | Be selective: avoid loading large reference docs |
| 70-90% | Run `/compact` with explicit preservation instructions |
| 90%+ | Complete current unit, then `/compact` or `/clear` |

### .claudeignore Impact

A well-configured `.claudeignore` can save 30-50% of token budget by excluding:
- `package-lock.json` alone: 30,000-80,000 tokens
- `*.snap` test snapshots: up to 100,000 tokens per large snapshot
- `dist/` build artifacts: variable but significant

### Context Commands Quick Reference

```
/context              View current context window usage breakdown
/compact              Compress conversation history (with focus instructions)
/compact [instruction] Example: "/compact Preserve: modified files, test status, blockers"
/clear                Reset to fresh context (CLAUDE.md + rules reload)
/btw [question]       Quick Q&A that doesn't enter conversation history
```

---

## 16. Composability — How It All Connects

### The Extension Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                    ALWAYS LOADED                         │
│  CLAUDE.md          What Claude knows every session      │
│  .claude/rules/     Non-negotiable guidelines            │
│  .claudeignore      What Claude never sees               │
│  settings.json      Hooks, permissions, model            │
├─────────────────────────────────────────────────────────┤
│                    LOADED ON DEMAND                      │
│  Skills             Progressive disclosure knowledge     │
│  Agents             Isolated specialist subagents        │
│  MCP Servers        External service integrations        │
│  docs/agentic/      Reference docs (loaded by agents)    │
│  design/            Design docs (loaded by agents)       │
├─────────────────────────────────────────────────────────┤
│                    DETERMINISTIC                         │
│  Hooks              Guaranteed execution (100%)          │
│  Permissions        Allow/deny tool access               │
│  .claudeignore      Hard file exclusion                  │
├─────────────────────────────────────────────────────────┤
│                    ADVISORY                              │
│  CLAUDE.md          Followed ~80% of the time            │
│  Rules              Followed ~80% of the time            │
│  Skills             Guidance, not enforcement            │
│  Agent prompts      Best-effort behavioral shaping       │
└─────────────────────────────────────────────────────────┘
```

### Placement Decision Matrix

| Need | Put It In | Why |
|------|-----------|-----|
| Must format every file | Hook (PostToolUse) | 100% deterministic |
| Coding style preferences | CLAUDE.md or rules/ | Session context |
| "How to write a controller" | Skill | On-demand only |
| "Review this PR for security" | Agent | Isolated context + specialized prompt |
| "Block rm -rf" | Hook (PreToolUse) | Safety gate |
| "Fetch GitHub issues" | MCP Server | External service |
| "Why we chose PostgreSQL" | DECISIONS.md | Reference doc |
| "How our auth works" | ARCHITECTURE.md | Reference doc |
| "Don't use UserService.findAll()" | CLAUDE.md "DO NOT USE" | Session context |
| Team release procedures | .claude/org/procedures.md | Tribal knowledge |
| Compliance rules | rules/compliance.md | Session context |

---


---

## 17. The Quality Skills: audit, sync, scaffold, map

These four skills form the self-maintaining backbone of any Claude-configured repository.

```
.claude/skills/agentic/repo/quality/
├── audit/SKILL.md      # Read-only visual compliance report
├── sync/SKILL.md       # Write: auto-fix configuration issues
├── scaffold/SKILL.md   # Bootstrap any repo from scratch
└── map/SKILL.md        # Regenerate CODEBASE-MAP.md
```

---

### 17.1 agentic:repo:quality:audit

`.claude/skills/agentic/repo/quality/audit/SKILL.md`

```markdown
---
description: >
  Audits this repository for Claude Code best-practice compliance.
  Returns a visual scorecard with token budget, cost estimate, outdated doc
  detection, and a specific fix command for every failing check.
  Invoke: "audit", "audit full", "audit partial", "agentic:repo:quality:audit"
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash]
---

# agentic:repo:quality:audit $ARGUMENTS

## Argument Parsing
- `full` (default): run all 12 checks
- `partial`: run only checks for files modified since last commit (git diff --name-only HEAD)

## Phase 1: Collect Metrics (run in parallel, store results)

```bash
# Token estimation
CLAUDE_LINES=$(wc -l CLAUDE.md 2>/dev/null | awk '{print $1}')
RULES_LINES=$(find .claude/rules -name "*.md" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
MCP_COUNT=$(grep -c "mcpServers" .claude/settings.json 2>/dev/null || echo 0)
AGENTS=$(find .claude/agents -name "*.md" 2>/dev/null | wc -l)

# Git state
BRANCH=$(git branch --show-current 2>/dev/null)
LAST_COMMIT=$(git log --oneline -1 2>/dev/null)

# Token formula
SYSTEM=30000; AUTOCOMPACT=45000
CLAUDE_TOKENS=$(echo "$CLAUDE_LINES * 1.3" | bc 2>/dev/null || echo 2000)
RULES_TOKENS=$(echo "$RULES_LINES * 1.3" | bc 2>/dev/null || echo 3000)
MCP_TOKENS=$(echo "$MCP_COUNT * 3000" | bc 2>/dev/null || echo 0)
STARTUP=$(($SYSTEM + $AUTOCOMPACT + $CLAUDE_TOKENS + $RULES_TOKENS + $MCP_TOKENS))
AVAILABLE=$((200000 - $STARTUP))
```

## Phase 2: Run 12 Checks

Run ultrathink before scoring. Read files before judging them.

| # | Check | Pass | Warn | Fail |
|---|-------|------|------|------|
| 1 | CLAUDE.md exists | present | — | missing |
| 2 | CLAUDE.md size | ≤150 lines | 151-200 | >200 |
| 3 | CLAUDE.md required sections | Commands + Structure/Arch + Agent Nav | missing 1 | missing 2+ |
| 4 | .claudeignore exists | present | — | missing |
| 5 | .claudeignore secrets coverage | .env, *.key, *.pem present | partial | missing |
| 6 | rules/ file count | ≤5 files | 6-8 | 9+ |
| 7 | rules/ file sizes | all ≤50 lines | any 51-80 | any >80 |
| 8 | Quality skills present | .claude/skills/agentic/repo/quality/ exists | exists empty | missing |
| 9 | Explorer agent present | .claude/agents/explorer.md exists | — | missing |
| 10 | Hooks configured | settings.json has PostToolUse + PreToolUse | missing one type | no hooks |
| 11 | CODEBASE-MAP.md freshness | exists + ≤30 days old | 31-90 days | missing or >90 days |
| 12 | Agent memory safety | no agent with memory: project that's dispatched in parallel | 1 such agent | 2+ such agents |

## Phase 3: Staleness Detection

For each file in docs/agentic/:
1. Extract all path-like references (matching libs/, apps/, src/, packages/)
2. For each path: `find . -path "*[path]*" -maxdepth 8 | head -1`
   - Empty result → STALE
3. Read `last-updated:` from frontmatter
4. `git log --oneline --since="[last-updated]" -- [paths] | wc -l`
   - >0 commits since last-updated → POTENTIALLY STALE
5. Run `staleness-check:` command from frontmatter if present

## Phase 4: Render Output

Display this exact format:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REPO QUALITY AUDIT — [repo-name] — [date]
  Branch: [branch] | Last commit: [hash message]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌───────────────────────────────────┬────────┬─────────────────────────────────────┐
│ Check                             │ Status │ Fix Command                         │
├───────────────────────────────────┼────────┼─────────────────────────────────────┤
│ CLAUDE.md exists                  │   ✅   │ —                                   │
│ CLAUDE.md size (247 lines)        │   ⚠️   │ agentic:repo:quality:sync narrow claude│
│ CLAUDE.md required sections       │   ✅   │ —                                   │
│ .claudeignore exists              │   ❌   │ agentic:repo:quality:sync isolated  │
│ .claudeignore secrets coverage    │   ❌   │ agentic:repo:quality:sync isolated  │
│ rules/ count (9 files)            │   ❌   │ Consolidate → agentic:repo:quality:sync│
│ rules/ file sizes                 │   ✅   │ —                                   │
│ Quality skills present            │   ✅   │ —                                   │
│ Explorer agent                    │   ✅   │ —                                   │
│ Hooks configured                  │   ⚠️   │ Missing Stop hook → :sync claude    │
│ CODEBASE-MAP.md (47 days old)     │   ⚠️   │ agentic:repo:quality:map            │
│ Agent memory safety               │   ❌   │ 2 agents with memory: project       │
└───────────────────────────────────┴────────┴─────────────────────────────────────┘

Score: 7/12 (58%) │ ✅ 7  ⚠️ 3  ❌ 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TOKEN BUDGET (estimated at session start)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  System:              30,000  (15%)
  Autocompact buffer:  45,000  (22%)
  CLAUDE.md:            3,200   (2%)
  rules/ (9 files):    11,700   (6%)  ← ⚠️ reduce to ≤5 to save ~7k
  MCP schemas (4):     12,000   (6%)
  ─────────────────────────────────────
  Consumed at startup: 101,900  (51%)
  Available for work:   98,100  (49%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ESTIMATED COST PER SESSION (startup tokens × model rate)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Haiku:   ~$0.014/session │ 5 parallel agents: ~$0.07/run
  Sonnet:  ~$0.067/session │ 5 parallel agents: ~$0.34/run
  Opus:    ~$0.343/session │ 5 parallel agents: ~$1.72/run

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DOCUMENTATION HEALTH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ┌─────────────────────────┬──────────────────┬──────────────────────────┐
  │ Document                │ Status           │ Notes                    │
  ├─────────────────────────┼──────────────────┼──────────────────────────┤
  │ CODEBASE-MAP.md         │ ⚠️ POTENTIALLY   │ 47 days old, 12 commits  │
  │ DATA-MODEL.md           │ ✅ CURRENT       │ 3 days ago               │
  │ ARCHITECTURE.md         │ ❌ STALE         │ libs/search/ not found   │
  │ DECISIONS.md            │ ✅ CURRENT       │ 8 days ago               │
  │ API-CONTRACTS.md        │ ⚠️ POTENTIALLY   │ 22 days, 5 commits since │
  └─────────────────────────┴──────────────────┴──────────────────────────┘
  Coverage: 5/5 required docs present ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  QUICK FIX COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Fix all claude config:      agentic:repo:quality:sync isolated claude
  Fix stale docs:             agentic:repo:quality:sync narrow docs
  Regenerate codebase map:    agentic:repo:quality:map
  Fix everything:             agentic:repo:quality:sync full all
```
```

---

### 17.2 agentic:repo:quality:sync

`.claude/skills/agentic/repo/quality/sync/SKILL.md`

```markdown
---
description: >
  Synchronizes this repository's Claude Code configuration and agentic docs
  to best-practice compliance. Runs Socratic probing first, applies changes
  atomically. Zero HITL restrictions — infers as much as possible from the repo.
  Invoke: "sync", "sync full", "sync isolated", "sync narrow docs", etc.
user-invocable: true
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, Task]
---

# agentic:repo:quality:sync $ARGUMENTS

## Argument Parsing
SCOPE: `full` (default) | `isolated` (.claude/ only, safe on any repo) | `narrow`
TARGET: `all` (default) | `docs` | `code` | `claude`

## Phase 1: Reconnaissance (ultrathink)

Read in parallel:
- CLAUDE.md (if exists), package.json/pyproject.toml/go.mod, README.md (50 lines)
- git log --oneline -5
- find .claude -type f (inventory current state)
- Glob: apps/*, libs/*, packages/*, src/* (one level deep)

Auto-detect without asking:
- Repo type: monorepo | monolith | poly-repo
- Primary language + framework
- Build tool, test framework
- Existing .claude/ state: empty | partial | complete | none
- Compliance signals from README/code

## Phase 2: Socratic Probing (5 questions max)

Present detection summary first:
```
I've scanned your repository. Here's what I found:
─────────────────────────────────────────────────
Repo type:  [detected — e.g., NX Monorepo (nx.json present)]
Language:   [detected]
Framework:  [detected]
Build tool: [detected]
Tests:      [detected]
.claude/:   [current state]
─────────────────────────────────────────────────
```

Ask ONLY what you cannot determine from the repo:

Q1 (compliance): "Any compliance requirements? HIPAA / SOC2 / GDPR / PCI / none / other"
Q2 (banned patterns): "Patterns, APIs, or libraries Claude should NEVER use? (deprecated code, banned packages)"
Q3 (destructive commands): "When Claude proposes rm -rf, DROP TABLE, force push: block / warn / allow?"
Q4 (existing .claude/): Only if .claude/ has content: "Merge / replace / skip existing files?"
Q5 (org nuance): "Team-specific gotchas for .claude/org/nuance.md? (things that surprise new people)"

Skip any question answerable from the repo with high confidence.

## Phase 3: Show Plan, Confirm Once

Display planned changes as a tree with [CREATE] / [UPDATE] / [SKIP] labels.
Include a `show [filename]` option so users can preview contents before confirming.
One "Proceed? (yes / no / show [filename])" prompt. Not per-file.

## Phase 4: Execute Atomically

Apply all changes. On failure: log to .claude/sync-errors.md, continue with others.
After: automatically run `agentic:repo:quality:audit partial` to verify.

## Phase 5: Report

```
Sync complete ─────────────────────────────────
✅ Created: N files
✅ Updated: N files
⏭️ Skipped: N files (already current)
❌ Failed:  N files (see .claude/sync-errors.md)

Post-sync audit: N/12 checks passing
Time: ~Xs | Cost: ~$X.XX (Sonnet)
```
```

---

### 17.3 agentic:repo:quality:scaffold

`.claude/skills/agentic/repo/quality/scaffold/SKILL.md`

```markdown
---
description: >
  Scaffolds a complete Claude Code configuration for any new or inherited
  repository. Auto-detects stack, asks 5 Socratic questions, generates
  everything: CLAUDE.md, .claudeignore, rules/, skills/, agents/, hooks/,
  docs/agentic/, design/, .claude/org/. Self-audits after completion.
  Perfect result guaranteed regardless of starting repo state.
  Invoke: "scaffold", "setup claude", "configure this repo", "agentic:repo:quality:scaffold"
user-invocable: true
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, Task]
---

# agentic:repo:quality:scaffold

Think ultrathink throughout. Your goal: produce a complete, correct, tailored
Claude configuration that makes every future session significantly more effective
in this specific codebase.

## Phase 1: Deep Reconnaissance

Read everything before asking anything:
```bash
# Discover structure
find . -maxdepth 3 -type f \( -name "*.json" -o -name "*.toml" -o -name "*.yaml" -o -name "*.mod" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" | head -30

# Stack detection
cat package.json 2>/dev/null | head -60    # Node/JS stacks
cat pyproject.toml 2>/dev/null | head -40  # Python stacks
cat go.mod 2>/dev/null | head -20          # Go stacks
cat Cargo.toml 2>/dev/null | head -20      # Rust stacks
cat pom.xml 2>/dev/null | head -30         # Java/Maven stacks

# Context clues
head -100 README.md 2>/dev/null
git log --oneline -10 2>/dev/null
ls -la
ls apps/ libs/ packages/ src/ 2>/dev/null
cat CLAUDE.md 2>/dev/null
find .claude -type f 2>/dev/null
```

Infer with high confidence:
- Repo archetype (monorepo | monolith | poly-repo)
- Language(s), frameworks, build/task runner, test framework
- CI/CD system, deployment target
- Database type (SQL | NoSQL | both) from dependencies
- Compliance signals from README, code patterns, config files
- Existing documentation quality and coverage
- Team size and code maturity from git history

## Phase 2: Present Inference Summary

Show exactly what you found. Reference actual files.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REPOSITORY ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Type:        [detected, with evidence]
  Language:    [detected]
  Framework:   [detected, with source]
  Build:       [detected]
  Tests:       [detected]
  CI:          [detected]
  Database:    [detected from deps]
  Deploy:      [detected from config files]
  Maturity:    [N commits, N months old]
  .claude/:    [current state]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Phase 3: Socratic Questions (5 maximum, skip if already known)

Q1: "Any compliance/data sensitivity? HIPAA / SOC2 / GDPR / PCI / none / other"
Q2: "Patterns, APIs, libraries Claude should NEVER use? (deprecated, banned, antipatterns)"
Q3: "Destructive commands (rm -rf, DROP TABLE, force push): block / warn / allow?"
Q4: [only if .claude/ has content] "Existing .claude/: merge / replace / skip existing?"
Q5: "Team-specific day-one surprises for .claude/org/nuance.md?"

## Phase 4: Generate Everything (in dependency order)

1.  .claudeignore — universal + stack-specific
2.  CLAUDE.md — root, sized for repo maturity, WHY/WHAT/HOW structure
3.  apps/[each]/CLAUDE.md — if monorepo with ≥2 apps
4.  libs/[high-impact]/CLAUDE.md — shared libs only
5.  .claude/settings.json — hooks + permissions
6.  .claude/rules/ — 3-5 files for detected stack + compliance
7.  .claude/hooks/ — all scripts, chmod +x applied
8.  .claude/agents/explorer.md — always
9.  .claude/agents/[stack-relevant].md — based on detected tech
10. .claude/skills/agentic/repo/quality/audit/SKILL.md
11. .claude/skills/agentic/repo/quality/sync/SKILL.md
12. .claude/skills/agentic/repo/quality/map/SKILL.md
13. .claude/org/nuance.md — from Q5 answer
14. .claude/org/procedures.md — stub with fill-in-prompts
15. .claude/org/deviations.md — stub
16. docs/agentic/CODEBASE-MAP.md — auto-generated from actual structure
17. docs/agentic/ARCHITECTURE.md — stub from detected patterns
18. docs/agentic/DATA-MODEL.md — stub with schema index if DB detected
19. docs/agentic/DECISIONS.md — stub with ADR template
20. docs/agentic/MIGRATIONS.md — stub if DB detected
21. design/ — directory structure with README
22. docs/agentic/pipeline/STAGE-CONTRACT.md — if multi-agent pipeline use detected

## Phase 5: Self-Audit

Run agentic:repo:quality:audit full immediately after.
Target: ≥10/12 checks passing. Fix failing checks before reporting.

## Phase 6: Report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SCAFFOLD COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Files created:    N
  Audit score:      N/12 ✅
  Token budget:     ~Nk tokens available per session

  What changed:
  • CLAUDE.md — N lines, covers [detected topics]
  • .claude/rules/ — N files for [stack + compliance]
  • .claude/hooks/ — [list installed hooks]
  • .claude/agents/ — [list agents created]
  • docs/agentic/ — [docs created/stubbed]
  • design/ — directory structure ready
  • .claude/org/ — nuance.md populated, stubs ready

  Next steps:
  1. Review CLAUDE.md — add any gotchas specific to your codebase
  2. Fill .claude/org/procedures.md with your team's release process
  3. Run: agentic:repo:quality:audit to verify everything

  Try it: ask Claude to describe the project structure.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
```

---

### 17.4 agentic:repo:quality:map

`.claude/skills/agentic/repo/quality/map/SKILL.md`

```markdown
---
description: >
  Regenerates docs/agentic/CODEBASE-MAP.md from actual repository structure.
  Zero questions. Zero confirmation. Just runs. Use after structural changes.
  Invoke: "map", "update codebase map", "agentic:repo:quality:map"
user-invocable: true
allowed-tools: [Read, Write, Glob, Bash]
---

# agentic:repo:quality:map

No questions. No confirmation. Run immediately.

1. Discover all apps, libs, packages, services (maxdepth 3)
2. For each: read package.json / go.mod / pyproject.toml for name and description
3. Detect framework from dependencies
4. Build dependency relationships (who imports whom) from tsconfig paths / go.mod / requirements
5. Write docs/agentic/CODEBASE-MAP.md with today's date as last-updated
6. Report: "CODEBASE-MAP.md regenerated — N apps, N libs mapped"

Use the format from §13 (Codebase Map Format).
```

---

## 18. The "Noise to Signal" Talk Guide

*For engineering leadership presenting to 20 inherited teams*

### Talk Overview
- **Title:** Noise to Signal — Setting Up Your Repository for Claude
- **Duration:** 25-30 minutes
- **Format:** Live demo + guide distribution
- **Follows:** "Ticket to Merge" intro session

---

### Segment 1: The Problem (5 min)

**Open with a live demo in an unconfigured real team repo:**

Ask Claude: "How does our authentication work?"

Claude asks clarifying questions, doesn't know the codebase, gives generic answers.

Show the context window: "200,000 tokens of capacity. Approximately 2,000 tokens of relevant signal. That's 1%. Claude has been working with 1% efficiency in your repository."

**Key line:** "Claude isn't broken. It's running without a map. Every session starts cold. It rediscovers your architecture every single time."

---

### Segment 2: What Claude Needs (3 min)

Show the extension hierarchy diagram (§16).

**Key points:**
- CLAUDE.md = always loaded = Claude's standing brief
- Hooks = 100% deterministic = the things that MUST happen
- Skills = on-demand = loaded when relevant, not every session
- Agents = isolated specialists = keep the main session clean

"We're going to give Claude a map. And then we're going to make sure that map stays current automatically."

---

### Segment 3: Live Setup (10 min)

**In the presenter's own team repo (live, not rehearsed):**

```bash
# In Claude Code
agentic:repo:quality:scaffold
```

Show Claude reading the repo. Show the inference summary ("I can see this is a...").
Answer 3-5 questions. Watch the `.claude/` directory appear.

```bash
agentic:repo:quality:audit
```

Show the ASCII table. Point to the token budget section: "We went from ~2k signal to ~60k signal."

Show cost estimate: "About $0.07 per Sonnet session. For a team of 5 developers doing 20 sessions a week, that's $7/week for everyone to have a properly-informed AI."

**Ask Claude again:** "How does our authentication work?"
Claude answers correctly and immediately.

"Same repo. 10 minutes. Completely different experience."

---

### Segment 4: The Self-Maintenance Pitch (5 min)

Show the sync skill: "What happens next week when your repo changes?"

```bash
agentic:repo:quality:sync
```

Show the planned changes, confirm, watch it run.

**The CI pitch:**
```yaml
# Add to your CI pipeline
- run: claude -p "agentic:repo:quality:sync narrow docs"
  when: changes in apps/ or libs/ or src/ or docs/
```

"Set it up once. Maintenance happens automatically. Your Claude config stays current without any manual work."

---

### Segment 5: Guide Distribution (2 min)

Share this document. 

"Everything we just did is in here. Reference for any repo — new projects, your team's existing repos, the messes you inherited. Same process, same result."

---

### Segment 6: Fresh Repo Demo (5 min, optional if time allows)

In a brand new empty git repository:
```bash
git init empty-demo && cd empty-demo
git commit --allow-empty -m "init"
# Open Claude Code
agentic:repo:quality:scaffold
```

Five questions. Complete `.claude/` + `docs/agentic/` + `design/` structure in under 5 minutes.

"From nothing to fully configured. One command."

---

### Handling Skeptic Objections

| Objection | Response |
|-----------|----------|
| "We don't have time to maintain this" | The sync skill maintains it. Add it to CI. |
| "Our codebase is too messy for this" | That's exactly why you need it — messy codebases benefit most. |
| "Our patterns are proprietary" | `.claude/org/procedures.md` lives in your repo, stays in your repo. |
| "We'll just use Cursor" | This config works with Cursor too — Cursor supports CLAUDE.md via its .cursorrules integration. |
| "What about security?" | `.claudeignore` + `block-dangerous.sh` handle secrets exposure and destructive commands. |
| "Will this work with our stack?" | The scaffold skill detects your stack. If it doesn't exist in Claude's training, it asks. |

---

## 19. Quick Setup Checklist

```
FOUNDATION
[ ] CLAUDE.md — correct size for repo type (§4)
[ ] .claudeignore — secrets + generated files + media (§5)
[ ] .claude/settings.json — hooks + permissions (§10)
[ ] .claude/hooks/ — block-dangerous + format + typecheck + verify-tests, all chmod +x

KNOWLEDGE LAYERS
[ ] .claude/rules/ — max 5 files, max 50 lines each (§6)
[ ] .claude/skills/agentic/repo/quality/ — all four skills (§17)
[ ] .claude/agents/explorer.md — minimum required agent (§8)

TRIBAL KNOWLEDGE
[ ] .claude/org/nuance.md — team-specific gotchas
[ ] .claude/org/procedures.md — release + deployment process

REFERENCE DOCS
[ ] docs/agentic/CODEBASE-MAP.md — current (auto-generate with :map)
[ ] docs/agentic/ARCHITECTURE.md — current
[ ] docs/agentic/DATA-MODEL.md — exists (with schemas/ if multiple domains)
[ ] docs/agentic/DECISIONS.md — ADR log current
[ ] docs/agentic/MIGRATIONS.md — [if database project]

DESIGN ARTIFACTS
[ ] design/ directory structure created
[ ] design/decisions/ — at minimum, placeholder for ADRs

NESTED CONTEXT [Monorepo only]
[ ] apps/[each]/CLAUDE.md — ≤40 lines each
[ ] libs/shared/CLAUDE.md — HIGH IMPACT label included

MCP
[ ] context7 — minimum global installation
[ ] Project-specific servers installed per-project

VERIFICATION
[ ] Run: agentic:repo:quality:audit
[ ] Score ≥ 10/12
[ ] Ask Claude: "Describe the project structure" — verify it answers correctly
[ ] Ask Claude: "How do tests work here?" — verify it knows
```

---

## 20. Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|--------------|-------------|-----|
| CLAUDE.md over 200 lines | Important rules get lost; Claude ignores them | Move to rules/ or skills |
| More than 5 rules files | Re-injection consumes 46% of context window | Consolidate to ≤5 files |
| Rules files over 50 lines | Same re-injection problem | Split or move to skills |
| @-inlining docs in CLAUDE.md | Embeds entire file every run, burns token budget | Use pointer-reference instead |
| `memory: project` on parallel agents | Silent last-write-wins collision | Strip memory from parallel agents |
| Skills for always-needed info | Loaded on demand = missed when always needed | Move to CLAUDE.md or rules/ |
| Hooks for preferences | Hooks block execution — use only for hard gates | Move preference to CLAUDE.md |
| Agents without tool restrictions | Unrestricted agent = full blast radius | Always define explicit `tools:` list |
| Giant CODEBASE-MAP.md | Verbose context waste | Keep navigational: paths + purposes only |
| Skipping compaction | Context rot degrades quality at 70%+ | Use :map skill for auto-maintenance |
| 10+ MCP servers | 30k+ tokens of tool schemas loaded at startup | Keep ≤5 active at once |
| Inlining files into agent prompts | Identical data loaded N times for N agents | Use file paths + worktree-local reads |
| Monolith patterns in monorepo | Each archetype needs its own conventions | Use the reference architecture for your repo type |
| Stale agentic docs | Claude makes wrong decisions from outdated info | Run :sync in CI to keep docs current |

---

*Council of Experts synthesis — 5 rounds, 10 experts, evolved from the Aegient reference implementation.*  
*Universal edition — applies to any team, any stack, any repo state.*
*Version: 2026-03-26*
