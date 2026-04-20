---
name: agentic:repo:quality:scaffold
description: >
  Scaffolds a complete Claude Code configuration for any new or inherited
  repository. Auto-detects stack and structure, asks at most 5 Socratic
  questions, then generates everything: CLAUDE.md, .claudeignore, rules/,
  skills/, agents/, hooks/, docs/agentic/, design/, .claude/org/.
  Self-audits after completion. Perfect result guaranteed regardless of
  starting repo state — empty, messy, or partially configured.
  Invoke: "scaffold", "setup claude", "configure this repo",
          "agentic:repo:quality:scaffold"
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

# agentic:repo:quality:scaffold

Think ultrathink throughout.

Your goal: produce a complete, correct, tailored Claude Code configuration
that makes every future session in this repository significantly more effective.
The output must feel like it was written by someone who has worked in this
codebase for months — not generated from a template.

---

## Phase 1: Deep Reconnaissance

Read everything available before asking a single question.

```bash
# Discover all config and manifest files (3 levels deep)
find . -maxdepth 3 -type f \
  \( -name "*.json" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" \
     -o -name "*.mod" -o -name "Makefile" -o -name "Dockerfile" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/dist/*" \
  ! -path "*/build/*" ! -path "*/.nx/*" | head -40

# Primary manifest
cat package.json 2>/dev/null | head -80
cat pyproject.toml 2>/dev/null | head -50
cat go.mod 2>/dev/null | head -25
cat Cargo.toml 2>/dev/null | head -25
cat pom.xml 2>/dev/null | head -40

# Human context
head -150 README.md 2>/dev/null
head -50 CONTRIBUTING.md 2>/dev/null

# Git signals (maturity + active areas)
git log --oneline -15 2>/dev/null
git shortlog -sn --no-merges HEAD 2>/dev/null | head -10

# Existing Claude config
cat CLAUDE.md 2>/dev/null
find .claude -type f 2>/dev/null

# Project structure
ls -la
ls apps/ libs/ packages/ src/ services/ 2>/dev/null
```

**Auto-detect — no questions for these:**

| What | How |
|------|-----|
| Repo type | `nx.json`/`turbo.json` → monorepo; `src/` without `apps/` → monolith; multiple `.git` repos → poly-repo |
| Language | Manifest files present |
| Framework | Dependencies in manifest |
| Build tool | Config file presence |
| Test framework | devDependencies |
| CI/CD | Workflow directory presence |
| Database | ORM/client dependencies |
| Compliance | README keywords: HIPAA, PHI, SOC2, GDPR, PCI |
| Team size | `git shortlog` contributor count |
| Maturity | Commit count + oldest commit age |

---

## Phase 2: Present Inference Summary

Show exactly what you found. Reference actual files and values.
This display builds trust with skeptical teams.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REPOSITORY ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Type:        [detected] ← [evidence file]
  Language:    [detected]
  Framework:   [detected] ← [dep name + version]
  Build:       [detected] ← [evidence file]
  Tests:       [detected]
  CI:          [detected or "none detected"]
  Database:    [detected or "none detected"]
  Compliance:  [detected or "none detected"]
  Maturity:    [N commits, N months, N contributors]
  .claude/:    [none | empty | partial (N files) | complete]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Phase 3: Socratic Questions (5 maximum)

Skip any question you already know the answer to with high confidence.

**Q1 — Compliance** (skip if README names one):
> "Any compliance or data sensitivity requirements?
> (HIPAA / SOC2 / GDPR / PCI / SOX / none / other)"

**Q2 — Banned patterns** (always ask):
> "Patterns, APIs, or libraries Claude should NEVER use?
> Think: deprecated code under migration, banned packages, antipatterns
> that keep appearing in PRs."

**Q3 — Destructive commands**:
> "When Claude proposes rm -rf, DROP TABLE, force push to main:
> block entirely / warn first / allow?"

**Q4 — Existing .claude/** (only if `.claude/` has files):
> "Found existing .claude/ with [N] files.
> Merge (add new, keep existing) / replace (overwrite all) / skip (no overwrites)?"

**Q5 — Day-one surprises** (always ask):
> "What would surprise a new developer on their first day?
> Things not in the README — gotchas, quirks, non-standard decisions.
> Goes in .claude/org/nuance.md."

---

## Phase 4: Generate Everything

Create in dependency order. Tailor every file to the detected stack.
No generic placeholder content.

```
1.  .claudeignore
        Universal patterns + stack-specific additions

2.  CLAUDE.md (root)
        30–50 lines (fresh) / 80–120 lines (active) / 100–150 lines (legacy)
        Sections: purpose, commands, architecture, code standards,
                  DO NOT USE, agent navigation

3.  apps/[each-app]/CLAUDE.md
        Only if monorepo with ≥2 apps. ≤40 lines each.

4.  libs/[shared-lib]/CLAUDE.md
        Only for high-impact shared libs. ≤20 lines. ⚠️ HIGH IMPACT label.

5.  .claude/settings.json
        Allowlist: common safe commands for detected build tool
        Deny: rm -rf, DROP TABLE, force push, cat .env*, curl|bash
        Hooks: SessionStart, PreToolUse, PostToolUse, Stop
        Model: sonnet

6.  .claude/hooks/block-dangerous.sh       chmod +x
7.  .claude/hooks/format-on-edit.sh        chmod +x (detect: prettier/black/gofmt)
8.  .claude/hooks/typecheck-on-edit.sh     chmod +x (typed languages only)
9.  .claude/hooks/verify-tests-on-stop.sh  chmod +x (use detected test runner)
10. .claude/hooks/session-context-loader.sh chmod +x

11. .claude/rules/code-standards.md    (tailored to detected language)
12. .claude/rules/testing.md           (tailored to detected test framework)
13. .claude/rules/git-workflow.md      (universal, ≤30 lines)
14. .claude/rules/architecture.md      (only if monorepo or complex structure)
15. .claude/rules/[compliance].md      (only if compliance detected in Q1)

16. .claude/agents/explorer.md         (always — reconnaissance agent)
17. .claude/agents/[relevant-specialist].md  (based on detected tech + compliance)

18. .claude/skills/agentic/repo/quality/audit/SKILL.md   (skip if present)
19. .claude/skills/agentic/repo/quality/sync/SKILL.md    (skip if present)
20. .claude/skills/agentic/repo/quality/map/SKILL.md     (skip if present)

21. .claude/org/nuance.md      (from Q5 answer or stub if skipped)
22. .claude/org/procedures.md  (stub with fill-in sections)
23. .claude/org/deviations.md  (stub)
24. .claude/org/secrets-protocol.md  (stub)

25. docs/agentic/CODEBASE-MAP.md   (auto-generated, include last-updated header)
26. docs/agentic/ARCHITECTURE.md   (stub from detected patterns)
27. docs/agentic/DATA-MODEL.md     (only if database detected)
28. docs/agentic/DECISIONS.md      (stub with ADR template)
29. docs/agentic/MIGRATIONS.md     (only if database detected)

30. design/system/    design/api/    design/data/
    design/ui/        design/decisions/    design/experiments/
    design/README.md  (what belongs in each subdirectory)

31. docs/agentic/pipeline/STAGE-CONTRACT.md
        Only if multi-agent pipeline evidence detected
        (existing subagent dispatch in skills, multiple agents defined)
```

---

## Phase 5: Self-Audit

Immediately after all writes, run:

```
agentic:repo:quality:audit full
```

Target: ≥10/12 checks passing.
If below 10/12, fix the failing checks before reporting to user.
Do not surface a failing audit score — fix it first.

---

## Phase 6: Final Report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SCAFFOLD COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Files created:    N
  Files updated:    N
  Files skipped:    N
  Audit score:      N/12 ✅
  Token budget:     ~[N]k tokens available per session

  What was created:
  • CLAUDE.md — [N] lines, covers [detected topics]
  • .claude/rules/ — [N] files ([rule topics])
  • .claude/hooks/ — [hooks installed]
  • .claude/agents/ — [agents created]
  • docs/agentic/ — [docs created/stubbed]
  • design/ — directory structure ready
  • .claude/org/ — nuance.md populated, stubs ready

  Next steps:
  1. Review CLAUDE.md — add codebase-specific gotchas you know
  2. Fill .claude/org/procedures.md with your release process
  3. Complete stub sections in docs/agentic/ARCHITECTURE.md
  4. Run: agentic:repo:quality:audit to verify
  5. Commit .claude/ to version control

  ─────────────────────────────────────────────────────
  Try it: ask Claude "describe the project structure"
  Before: Claude would ask clarifying questions.
  After:  Claude answers from its loaded context.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Quality Standards for Generated Files

**CLAUDE.md must:**
- Use WHY/WHAT/HOW structure
- Contain actual commands — not `[your-test-command]` placeholders
- Include "DO NOT USE" section if deprecated patterns are detectable
- Never exceed 150 lines
- End with Agent Navigation pointing to docs/agentic/

**rules/ files must:**
- Be scoped with `paths:` frontmatter where applicable
- Contain only conventions Claude actually gets wrong in this stack
- Never exceed 50 lines

**hooks/ scripts must:**
- Be executable (chmod +x applied)
- Handle missing tools gracefully (check existence before running)
- Exit 0 for all non-blocking cases
- Exit 2 only for true blocking failures (failing tests, dangerous commands)
