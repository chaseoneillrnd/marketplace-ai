---
name: agentic:repo:quality:audit
description: >
  Audits this repository for Claude Code best-practice compliance.
  Returns a visual scorecard with token budget, cost estimate, outdated doc
  detection, and a specific fix command for every failing check.
  Invoke: "audit", "audit full", "audit partial", "agentic:repo:quality:audit"
user-invocable: true
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# agentic:repo:quality:audit $ARGUMENTS

## Argument Parsing

- `full` (default): run all 12 checks against the entire repo
- `partial`: run checks only for files modified since last commit (`git diff --name-only HEAD`)

---

## Phase 1: Collect Baseline Metrics

Run these commands first. Store all results. Do NOT display anything yet.

```bash
# Line counts
CLAUDE_LINES=$(wc -l CLAUDE.md 2>/dev/null | awk '{print $1}' || echo 0)
RULES_FILES=$(find .claude/rules -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
RULES_LINES=$(find .claude/rules -name "*.md" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
MCP_COUNT=$(grep -c '"command"' .claude/settings.json 2>/dev/null || echo 0)

# Git state
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
LAST_COMMIT=$(git log --oneline -1 2>/dev/null || echo "no commits")

# Token budget estimation
SYSTEM=30000
AUTOCOMPACT=45000
CLAUDE_TOKENS=$(echo "$CLAUDE_LINES * 13 / 10" | bc 2>/dev/null || echo 2000)
RULES_TOKENS=$(echo "$RULES_LINES * 13 / 10" | bc 2>/dev/null || echo 3000)
MCP_TOKENS=$(echo "$MCP_COUNT * 3000" | bc 2>/dev/null || echo 0)
STARTUP=$(($SYSTEM + $AUTOCOMPACT + $CLAUDE_TOKENS + $RULES_TOKENS + $MCP_TOKENS))
AVAILABLE=$((200000 - $STARTUP))
```

---

## Phase 2: Run 12 Checks

Think ultrathink before scoring. Read the actual files — do not guess at their contents.

For each check, record STATUS and FIX_COMMAND.

**STATUS values:** ✅ PASS | ⚠️ WARN | ❌ FAIL

| # | Check | ✅ Pass | ⚠️ Warn | ❌ Fail |
|---|-------|---------|---------|--------|
| 1 | CLAUDE.md exists | file present | — | not found |
| 2 | CLAUDE.md size | ≤150 lines | 151–200 | >200 |
| 3 | CLAUDE.md required sections | Commands + Structure + Agent Navigation | missing 1 | missing 2+ |
| 4 | .claudeignore exists | file present | — | not found |
| 5 | .claudeignore secrets coverage | `.env`, `*.key`, `*.pem` all present | some missing | none |
| 6 | rules/ file count | ≤5 files | 6–8 files | 9+ files |
| 7 | rules/ file sizes | all ≤50 lines | any 51–80 | any >80 |
| 8 | Quality skills present | `.claude/skills/agentic/repo/quality/` exists + non-empty | exists but empty | missing |
| 9 | Explorer agent present | `.claude/agents/explorer.md` exists | — | missing |
| 10 | Hooks configured | settings.json has PostToolUse + PreToolUse | missing one type | no hooks |
| 11 | CODEBASE-MAP.md freshness | exists + last-updated ≤30 days | 31–90 days old | missing or >90 days |
| 12 | Agent memory safety | no agents with `memory: project` dispatched in parallel | 1 such agent | 2+ such agents |

**Check 11 implementation:**
```bash
MAP_FILE="docs/agentic/CODEBASE-MAP.md"
if [ ! -f "$MAP_FILE" ]; then
  CHECK11="FAIL"
else
  LAST_UPDATED=$(grep "last-updated:" "$MAP_FILE" | head -1 | grep -oE "[0-9]{4}-[0-9]{2}-[0-9]{2}" || echo "")
  if [ -z "$LAST_UPDATED" ]; then
    CHECK11="WARN"
  else
    DAYS_OLD=$(( ($(date +%s) - $(date -d "$LAST_UPDATED" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$LAST_UPDATED" +%s 2>/dev/null || echo 0)) / 86400 ))
    if [ "$DAYS_OLD" -le 30 ]; then CHECK11="PASS"
    elif [ "$DAYS_OLD" -le 90 ]; then CHECK11="WARN"
    else CHECK11="FAIL"; fi
  fi
fi
```

**Check 12 implementation:**
```bash
MEMORY_AGENTS=$(grep -l "memory: project" .claude/agents/*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$MEMORY_AGENTS" -eq 0 ]; then CHECK12="PASS"
elif [ "$MEMORY_AGENTS" -eq 1 ]; then CHECK12="WARN"
else CHECK12="FAIL"; fi
```

---

## Phase 3: Staleness Detection

For each file in `docs/agentic/`:

**Pass 1 — Path existence:**
```bash
for doc in docs/agentic/*.md; do
  paths=$(grep -oE "(apps|libs|src|packages|services)/[a-z/_.-]+" "$doc" | sort -u)
  for path in $paths; do
    if ! find . -path "./$path*" -maxdepth 8 2>/dev/null | grep -q .; then
      echo "STALE_PATH in $doc: $path not found"
    fi
  done
done
```

**Pass 2 — Age + git activity:**
```bash
for doc in docs/agentic/*.md; do
  last_updated=$(grep "last-updated:" "$doc" | head -1 | grep -oE "[0-9]{4}-[0-9]{2}-[0-9]{2}" || echo "")
  if [ -n "$last_updated" ]; then
    commit_count=$(git log --oneline --since="$last_updated" -- . 2>/dev/null | wc -l | tr -d ' ')
    if [ "$commit_count" -gt 0 ]; then
      echo "POTENTIALLY_STALE: $doc — $commit_count commits since $last_updated"
    fi
  fi
done
```

**Pass 3 — Run `staleness-check:` command from doc frontmatter if present. Empty result = STALE.**

---

## Phase 4: Render Output

Display this exact format with actual computed values:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REPO QUALITY AUDIT — [repo-name] — [YYYY-MM-DD]
  Branch: [branch] | Last commit: [hash] [message]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌───────────────────────────────────┬────────┬──────────────────────────────────────┐
│ Check                             │ Status │ Fix Command                          │
├───────────────────────────────────┼────────┼──────────────────────────────────────┤
│ CLAUDE.md exists                  │   ✅   │ —                                    │
│ CLAUDE.md size ([N] lines)        │   ⚠️   │ agentic:repo:quality:sync narrow claude│
│ CLAUDE.md required sections       │   ✅   │ —                                    │
│ .claudeignore exists              │   ❌   │ agentic:repo:quality:sync isolated   │
│ .claudeignore secrets coverage    │   ❌   │ agentic:repo:quality:sync isolated   │
│ rules/ count ([N] files)          │   ❌   │ Consolidate → agentic:repo:quality:sync│
│ rules/ file sizes                 │   ✅   │ —                                    │
│ Quality skills present            │   ✅   │ —                                    │
│ Explorer agent                    │   ✅   │ —                                    │
│ Hooks configured                  │   ⚠️   │ Missing Stop hook → :sync claude     │
│ CODEBASE-MAP.md ([N] days old)    │   ⚠️   │ agentic:repo:quality:map             │
│ Agent memory safety               │   ❌   │ Strip memory: from parallel agents   │
└───────────────────────────────────┴────────┴──────────────────────────────────────┘

Score: [N]/12 ([%]%) │ ✅ [N]  ⚠️ [N]  ❌ [N]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TOKEN BUDGET (estimated at session start)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  System prompt:         30,000 tokens  (15%)
  Autocompact buffer:    45,000 tokens  (22%)
  CLAUDE.md:            [N] tokens  ([%]%)
  rules/ ([N] files):   [N] tokens  ([%]%)
  MCP schemas ([N]):    [N] tokens  ([%]%)
  ──────────────────────────────────────────
  Consumed at startup:  [N] tokens  ([%]%)
  Available for work:   [N] tokens  ([%]%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ESTIMATED COST PER SESSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Model    Startup cost   Avg session   5 agents/run
  ──────────────────────────────────────────────────
  Haiku    ~$0.006        ~$0.014       ~$0.07
  Sonnet   ~$0.029        ~$0.067       ~$0.34
  Opus     ~$0.147        ~$0.343       ~$1.72

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DOCUMENTATION HEALTH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ┌─────────────────────────┬──────────────────┬─────────────────────────────┐
  │ Document                │ Status           │ Notes                       │
  ├─────────────────────────┼──────────────────┼─────────────────────────────┤
  │ CODEBASE-MAP.md         │ [status]         │ [age + commit count]        │
  │ ARCHITECTURE.md         │ [status]         │ [staleness reason if any]   │
  │ DATA-MODEL.md           │ [status]         │ [age]                       │
  │ DECISIONS.md            │ [status]         │ [age]                       │
  │ API-CONTRACTS.md        │ [status]         │ [age + commit count]        │
  └─────────────────────────┴──────────────────┴─────────────────────────────┘
  Coverage: [N]/5 required docs present

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  QUICK FIX COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Fix all claude config:      agentic:repo:quality:sync isolated claude
  Fix stale docs:             agentic:repo:quality:sync narrow docs
  Regenerate codebase map:    agentic:repo:quality:map
  Fix everything:             agentic:repo:quality:sync full all
```

---

## Rules

- Always read files before scoring — never infer from filenames alone
- If a file exists but is empty, treat as FAIL for its check
- If docs/agentic/ does not exist, mark all doc checks as ❌ FAIL
- Token numbers are estimates — label them as such
- Cost estimates use current Anthropic API pricing — note they may drift
