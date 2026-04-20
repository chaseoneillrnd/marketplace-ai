---
name: agentic:repo:quality:sync
description: >
  Synchronizes this repository's Claude Code configuration and agentic docs
  to best-practice compliance. Runs Socratic probing first, applies all changes
  atomically. Infers as much as possible from the repo — minimal HITL.
  Invoke: "sync", "sync full", "sync isolated", "sync narrow docs", etc.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
---

# agentic:repo:quality:sync $ARGUMENTS

## Argument Parsing

**SCOPE** (how broadly to operate):
- `full` — all checks, all targets (default)
- `isolated` — only `.claude/` directory, safe on any repo at any time
- `narrow` — only files matching the TARGET

**TARGET** (what to operate on):
- `all` — everything (default)
- `docs` — `docs/agentic/` only
- `code` — source files only (triggers CODEBASE-MAP.md regeneration)
- `claude` — `.claude/` directory only

**Examples:**
- `sync` → full, all
- `sync isolated` → isolated, claude
- `sync narrow docs` → narrow, docs
- `sync full claude` → full, claude only

---

## Phase 1: Reconnaissance

Think ultrathink. Read everything before asking anything. Run in parallel:

```bash
# Stack detection
cat package.json 2>/dev/null | head -60
cat pyproject.toml 2>/dev/null | head -40
cat go.mod 2>/dev/null | head -20
cat Cargo.toml 2>/dev/null | head -20
cat pom.xml 2>/dev/null | head -30

# Context
head -100 README.md 2>/dev/null
git log --oneline -5 2>/dev/null

# Current Claude state
cat CLAUDE.md 2>/dev/null
find .claude -type f 2>/dev/null

# Structure
ls -la
ls apps/ libs/ packages/ src/ 2>/dev/null
```

**Auto-detect without asking:**

| Signal | Detection |
|--------|-----------|
| Repo type | `nx.json`/`turbo.json` → monorepo; `src/` without `apps/` → monolith |
| Language | Manifest files present |
| Framework | Dependencies in manifest |
| Build tool | `nx.json` → NX; `turbo.json` → Turborepo; `Makefile` → Make |
| Test framework | `jest`/`vitest` → Jest; `pytest` → Pytest; `rspec` → RSpec |
| Compliance | Keywords in README: HIPAA, PHI, SOC2, GDPR, PCI |
| CI/CD | `.github/workflows/`, `.circleci/`, `.gitlab-ci.yml` |
| .claude/ state | `find .claude -type f | wc -l` |

---

## Phase 2: Socratic Probing

**First, display your inference summary:**

```
I've scanned your repository. Here's what I found:
────────────────────────────────────────────────────
Repo type:    [detected] — [evidence, e.g., "nx.json present"]
Language:     [detected]
Framework:    [detected] — [evidence]
Build tool:   [detected]
Tests:        [detected]
Compliance:   [detected or "none detected"]
.claude/:     [empty | partial (N files) | complete | none]
────────────────────────────────────────────────────
```

**Then ask ONLY questions you cannot answer from the repo. Maximum 5.**

Skip any question where you already have high confidence.

**Q1 — Compliance** (skip if README names a compliance framework):
> "Any compliance or data sensitivity requirements?
> HIPAA / SOC2 / GDPR / PCI / SOX / none / other"

**Q2 — Banned patterns** (always ask — cannot be inferred):
> "Patterns, APIs, or libraries Claude should NEVER use?
> Think: deprecated code, banned packages, antipatterns under migration."

**Q3 — Destructive commands** (skip if `block-dangerous.sh` exists):
> "When Claude proposes rm -rf, DROP TABLE, force push:
> block entirely / warn first / allow?"

**Q4 — Existing .claude/ handling** (only if `.claude/` has content):
> "Existing .claude/ found. Should I:
> merge (add new, keep existing), replace (overwrite all), or skip (no overwrites)?"

**Q5 — Org nuance** (always ask):
> "What would surprise a new developer on day one?
> Goes in .claude/org/nuance.md."

---

## Phase 3: Show Plan, Confirm Once

Display ALL planned changes before writing anything:

```
Planned changes — agentic:repo:quality:sync [scope] [target]
────────────────────────────────────────────────────────────────
[CREATE] CLAUDE.md (~85 lines)
[CREATE] .claudeignore
[CREATE] .claude/settings.json
[CREATE] .claude/rules/code-standards.md
[UPDATE] .claude/rules/testing.md (exists — adding 3 lines)
[CREATE] .claude/hooks/block-dangerous.sh
[CREATE] .claude/agents/explorer.md
[CREATE] .claude/org/nuance.md
[CREATE] docs/agentic/CODEBASE-MAP.md (auto-generated)
[SKIP]   docs/agentic/ARCHITECTURE.md (exists and current)
────────────────────────────────────────────────────────────────
N files to create/update, N to skip.

Proceed? (yes / no / show [filename] to preview a specific file)
```

One confirmation prompt total — not per file.
If user types `show [filename]`, display exact content, then re-ask "Proceed?"

---

## Phase 4: Execute Atomically

Apply all changes in dependency order:

1. `.claudeignore`
2. `.claude/settings.json`
3. `.claude/hooks/*.sh` — `chmod +x` each
4. `CLAUDE.md` — root, sized for repo maturity
5. `apps/[each]/CLAUDE.md` — if monorepo ≥2 apps
6. `.claude/rules/` — 3–5 files, ≤50 lines each
7. `.claude/agents/explorer.md`
8. `.claude/agents/[relevant]` — based on detected tech
9. `.claude/org/nuance.md` — from Q5
10. `docs/agentic/CODEBASE-MAP.md` — auto-generated
11. Any missing `docs/agentic/` stubs

On failure: log to `.claude/sync-errors.md`, continue with remaining files.
After all writes: automatically run `agentic:repo:quality:audit partial` to verify.

---

## Phase 5: Report

```
Sync complete — agentic:repo:quality:sync [scope] [target]
────────────────────────────────────────────────────────────────
✅ Created:  N files
✅ Updated:  N files
⏭️ Skipped:  N files (already current)
❌ Failed:   N files → see .claude/sync-errors.md

Post-sync audit: N/12 checks passing

Time:  ~Xs  |  Cost:  ~$X.XX (Sonnet)
────────────────────────────────────────────────────────────────
Next: commit .claude/ to version control so your team shares this config.
```

---

## Content Generation Standards

**CLAUDE.md size target:**
| Repo state | Target |
|------------|--------|
| Fresh / simple | 30–50 lines |
| Active project | 80–120 lines |
| Legacy / complex | 100–150 lines |

**CLAUDE.md required sections (always):**
1. Project name + one-sentence purpose
2. Commands (build, test, lint, serve)
3. Architecture / structure overview
4. Code standards (what Claude gets wrong here specifically)
5. DO NOT USE (deprecated patterns, banned libraries)
6. Agent Navigation (pointers to docs/agentic/)

**rules/ files:** One per concern. Never more than 5. Never more than 50 lines each.

**Compliance additions:**
- HIPAA → add `rules/hipaa-compliance.md`, extend block-dangerous.sh
- SOC2 → add `rules/security.md`
- GDPR → add `rules/data-privacy.md`
