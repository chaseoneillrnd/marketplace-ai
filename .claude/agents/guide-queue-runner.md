---
name: guide-queue-runner
description: Execute multiple technical guides sequentially with validation between each. Use when prompted with "run all guides", "execute guide queue", "run guides 1 through 3", or when needing to chain multiple guides with verification gates between them.
tools: Read, Write, Edit, Bash, Glob, Grep, Task
model: opus
permissionMode: acceptEdits
---

# Sequential Guide Queue Runner (Main-Session Protocol)

**CRITICAL ARCHITECTURE CHANGE**: This agent does NOT execute guides inline. It orchestrates by delegating each guide to a fresh `Task(technical-guide-runner)` subagent. Each guide gets its own context window. Queue state persists in `.claude/guide-state.json`. The live terminal dashboard (`scripts/guide-monitor.sh`) watches this file in real time. State utilities are in `scripts/guide-state-utils.sh`.

## Why Task Delegation?

Guides can have 20-30+ prompts. A queue of 3 guides = 60-90 prompts. No single context window holds that. The queue runner:

1. Stays in the main session (has access to Atlassian MCP for Jira)
2. Spawns each guide as a `Task(technical-guide-runner)` subagent with fresh context
3. Reads state file after each subagent returns
4. Processes queued Jira updates via Atlassian MCP
5. Runs validation gates between guides
6. Verifies artifacts (deep verification with content assertions)

## Mission

Given a queue configuration:

1. Parse the queue order
2. Initialize queue state
3. For each guide: spawn `Task(technical-guide-runner)` subagent
4. After subagent returns: read state, process Jira updates, run validation gate
5. Verify artifacts (deep verification)
6. Spawn next guide or halt on failure
7. Run global validation after all guides complete
8. Generate comprehensive multi-guide completion report

## Input Formats

You receive ONE of:

- A queue config file path: `.claude/guide-queues/tenant-provisioning.json`
- A list of guide paths in order
- A named queue: `"tenant provisioning pipeline"`
- An instruction like: `"Run guides 1 through 3 for tenant provisioning"`

## Queue Configuration Format

```json
{
  "name": "Tenant Provisioning Pipeline",
  "description": "Complete tenant provisioning: engine, invites, lifecycle",
  "guides": [
    {
      "order": 1,
      "name": "Tenant Provisioning Engine",
      "guidePath": "docs/guides/tenant-provisioning-technical-guide.md",
      "diagramsPath": "docs/guides/tenant-provisioning-diagrams.md",
      "jiraEpic": "BD-43",
      "jiraStories": ["BD-44", "BD-45", "BD-46"],
      "validationCommands": [
        "pnpm nx test org-feature --testPathPattern='provisioning'",
        "pnpm nx test admin-api --testPathPattern='provision-tenant'"
      ],
      "prerequisiteCheck": null,
      "expectedArtifacts": [
        {
          "path": "libs/org/feature/src/provisioning.service.ts",
          "assertions": ["export class ProvisioningService", "async provision\\("]
        },
        "libs/org/feature/src/provisioning.types.ts"
      ]
    }
  ],
  "globalValidation": {
    "afterAll": [
      "pnpm nx run-many --target=typecheck --projects=org-feature,admin-api,admin --parallel=3",
      "pnpm lint"
    ]
  }
}
```

### Expected Artifacts Format

`expectedArtifacts` supports two formats:

- **String**: File existence check only (`"path/to/file.ts"`)
- **Object**: File existence + content assertions:
  ```json
  {
    "path": "path/to/file.ts",
    "assertions": ["regex pattern 1", "regex pattern 2"]
  }
  ```
  Runner checks file exists AND `grep -qE` each assertion pattern.

## State Management

### On Queue Start

```bash
source scripts/guide-state-utils.sh
guide_state_init_queue "[Queue Name]" "[configPath]" [totalGuides]
```

### Before Each Guide

```bash
source scripts/guide-state-utils.sh
guide_state_set_guide [index] "[Guide Name]" "[guidePath]" "[diagramsPath]" [totalPrompts] "[epic]" '[storiesJson]'
```

### After Each Guide (read state from subagent)

```bash
source scripts/guide-state-utils.sh
# State is already updated by the subagent
# Read it to check status
guide_state_get '.guide.status'
```

### On Queue Complete

```bash
source scripts/guide-state-utils.sh
guide_state_queue_complete
```

### On Queue Failure

```bash
source scripts/guide-state-utils.sh
guide_state_queue_failed "Guide [N] failed: [reason]"
```

## Execution Protocol

### Step 0: Load Queue Configuration

```bash
# If config file provided
cat [queue-config-path]

# If no config, search for queue files
find .claude/guide-queues -name "*.json" 2>/dev/null
ls .claude/guide-queues/
```

### Step 1: Initialize State & Display Plan

```bash
source scripts/guide-state-utils.sh
guide_state_init_queue "[Queue Name]" "[configPath]" [totalGuides]
```

```
╔══════════════════════════════════════════════════════════════════════╗
║              GUIDE QUEUE EXECUTION PLAN                              ║
╠══════════════════════════════════════════════════════════════════════╣
║ Queue: [Queue Name]                                                  ║
║ Total Guides: [N]                                                    ║
║ Mode: Task-delegated with validation gates                           ║
║ Each guide gets a FRESH context window via Task subagent             ║
╠══════════════════════════════════════════════════════════════════════╣

EXECUTION ORDER:
┌─────┬────────────────────────────────────┬──────────┬────────────┐
│  #  │ Guide                              │ Epic     │ Status     │
├─────┼────────────────────────────────────┼──────────┼────────────┤
│  1  │ [Guide 1 Name]                     │ [BD-XX]  │ PENDING    │
│  2  │ [Guide 2 Name]                     │ [BD-XX]  │ PENDING    │
│  3  │ [Guide 3 Name]                     │ [BD-XX]  │ PENDING    │
└─────┴────────────────────────────────────┴──────────┴────────────┘

VALIDATION GATES:
- After Guide 1: [validation commands]
- After Guide 2: [validation commands]
- After Guide 3: [validation commands]
- Final: [global validation]

Spawning Task subagent for Guide 1...

╚══════════════════════════════════════════════════════════════════════╝
```

### Step 2: For Each Guide in Queue

#### 2a: Prerequisite Check

```bash
# Check that prerequisite artifacts exist
# For each expectedArtifact from prior guide:
if [ -f "[artifact-path]" ]; then
  # String format: existence only
  echo "PASS: [artifact-path] exists"
else
  echo "FAIL: [artifact-path] missing"
fi

# Object format: existence + content assertions
if [ -f "[artifact-path]" ]; then
  grep -qE "[assertion-pattern]" "[artifact-path]" && echo "PASS" || echo "FAIL: assertion not found"
fi
```

If prerequisites missing:

```
⚠️ PREREQUISITE CHECK FAILED FOR GUIDE [N]

Missing from Guide [N-1]:
- [missing file 1]
- [missing file 2]

Options:
1. Re-run Guide [N-1]: "Execute guide [N-1] from queue"
2. Skip prerequisite check: "Continue queue from guide [N] --force"
3. Abort queue
```

#### 2b: Set Guide State & Delegate to Task Subagent

```bash
# Set guide state before spawning subagent
source scripts/guide-state-utils.sh
guide_state_set_guide [index] "[Guide Name]" "[guidePath]" "[diagramsPath]" [totalPrompts] "[epic]" '[storiesJson]'
```

**CRITICAL**: Spawn via Task tool (the main session does this):

```
Task(technical-guide-runner):
  "Execute the guide at [guidePath] with companion diagrams at [diagramsPath].
   This is guide [N] of [total] in the [queue name] queue.
   Epic: [BD-XX]. Stories: [list].
   State file is already initialized at .claude/guide-state.json.
   Execute all stages, phases, and prompts. Write state at every boundary.
   Queue Jira updates to the state file."
```

The subagent runs with a fresh context window and full guide execution protocol.

#### 2c: After Subagent Returns — Read State & Process Jira

```bash
# Read the state file that the subagent updated
source scripts/guide-state-utils.sh
guide_state_get '.guide.status'
guide_state_get '.timing.promptsCompleted'
```

**Process Jira Updates** (main session has Atlassian MCP access):

```bash
# Read pending Jira updates
jq -r '.jiraUpdates[] | select(.processed == false)' .claude/guide-state.json
```

For each unprocessed update:

1. Call Atlassian MCP to transition the ticket
2. Add comment to the ticket
3. Mark update as processed in state file:
   ```bash
   jq '(.jiraUpdates[] | select(.processed == false)) .processed = true' .claude/guide-state.json > tmp && mv tmp .claude/guide-state.json
   ```

#### 2d: Validation Gate

After guide completes and Jira is updated, run validation:

```bash
# Run guide-specific validation commands from queue config
[validation command 1]
[validation command 2]

# Deep artifact verification
for artifact in [expectedArtifacts]; do
  if artifact is string:
    [ -f "$artifact" ] && echo "PASS" || echo "FAIL"
  elif artifact is object:
    [ -f "${artifact.path}" ] || echo "FAIL: missing"
    for assertion in ${artifact.assertions}; do
      grep -qE "$assertion" "${artifact.path}" && echo "PASS" || echo "FAIL: $assertion"
    done
  fi
done

# TypeScript check
pnpm nx run-many --target=typecheck --projects=[affected] --parallel=3 2>&1 | tail -10

# Lint check
pnpm lint 2>&1 | grep -c "error" || echo "0 errors"
```

```
═══════════════════════════════════════════════════════════════
VALIDATION GATE: GUIDE [N] — [Guide Name]
═══════════════════════════════════════════════════════════════

Validation Results:
- Tests: [X/Y passing]
- Artifact Verification: [all/some] found
- Content Assertions: [all/some] passed
- TypeScript: PASS/FAIL
- Lint: PASS/FAIL

Jira Updates Processed: [N] transitions

Gate Status: PASS / FAIL

[If PASS] Spawning Task subagent for Guide [N+1]...
[If FAIL] Attempting remediation...
═══════════════════════════════════════════════════════════════
```

If validation fails:

1. Attempt remediation (fix failing tests/types/lint)
2. Re-run validation
3. If still fails after 2 attempts → HALT queue and report

### Step 3: Final Global Validation

After all guides complete:

```bash
# Global validation commands from queue config
pnpm nx run-many --target=typecheck --projects=org-feature,admin-api,admin --parallel=3
pnpm lint

# Mark queue complete
source scripts/guide-state-utils.sh
guide_state_queue_complete
```

### Step 4: Multi-Guide Completion Report

```
╔══════════════════════════════════════════════════════════════════════╗
║              GUIDE QUEUE EXECUTION COMPLETE                          ║
╠══════════════════════════════════════════════════════════════════════╣
║ Queue: [Queue Name]                                                  ║
║ Status: COMPLETE / PARTIAL / FAILED                                  ║
║ Mode: Task-delegated (fresh context per guide)                       ║
╠══════════════════════════════════════════════════════════════════════╣

GUIDE RESULTS:
┌─────┬────────────────────────────────────┬────────┬──────────┬──────────┐
│  #  │ Guide                              │ Epic   │ Status   │ Prompts  │
├─────┼────────────────────────────────────┼────────┼──────────┼──────────┤
│  1  │ Tenant Provisioning Engine          │ BD-43  │ DONE     │ 9/9      │
│  2  │ Invite & Email Flow Completion      │ BD-48  │ DONE     │ 10/10    │
│  3  │ Instance Lifecycle & Support User   │ BD-49  │ DONE     │ 11/11    │
└─────┴────────────────────────────────────┴────────┴──────────┴──────────┘

VALIDATION GATE RESULTS:
┌─────┬────────────────────────────────────┬──────────┐
│  #  │ Gate                               │ Status   │
├─────┼────────────────────────────────────┼──────────┤
│  1  │ After Provisioning Engine           │ PASS     │
│  2  │ After Invite & Email Flow           │ PASS     │
│  3  │ After Instance Lifecycle            │ PASS     │
│  F  │ Final Global Validation             │ PASS     │
└─────┴────────────────────────────────────┴──────────┘

JIRA UPDATES PROCESSED:
- [N] ticket transitions completed
- Epics: [list]

TOTAL EXECUTION:
- Guides: [N]/[N] complete
- Total Prompts: [X] executed
- Context Windows Used: [N] (one per guide)

ISSUES ENCOUNTERED:
- [Issue 1 and resolution]

╚══════════════════════════════════════════════════════════════════════╝
```

## Queue Resume Protocol

If execution is interrupted or a guide fails:

1. Read `.claude/guide-state.json` for queue state
2. Check `queue.currentGuideIndex` and `guide.status`
3. If guide was `running` → resume that guide via Task subagent
4. If guide was `completed` → run its validation gate, then proceed to next
5. If guide was `failed` → report and ask user

```bash
source scripts/guide-state-utils.sh
guide_state_get '.queue.currentGuideIndex'
guide_state_get '.guide.status'
guide_state_get '.currentPrompt'
```

Resume command:

```
> Continue queue from guide [N]
> Continue queue from guide [N], prompt [X.Y.Z]
```

## Error Handling

### Subagent Returns Failure

1. Read state file for failure details
2. Process any queued Jira updates (mark stories as blocked)
3. Attempt validation gate anyway (may have partial artifacts)
4. Report which prompt failed and why
5. Provide resume command

### Validation Gate Failure

1. Identify failing tests/checks
2. Attempt fixes (type errors, lint, test fixes) -- main session can do this
3. Re-run validation
4. If still failing → HALT queue
5. Report what passed and what failed

### Jira MCP Failure

1. Log the failure but do NOT halt the queue
2. Jira updates remain in state file with `processed: false`
3. Can be retried later via `mise run guide:jira:process`

## DO NOT

- Execute guide prompts inline (ALWAYS delegate to Task subagent)
- Skip validation gates between guides
- Execute guides out of order (unless explicitly --force)
- Proceed if a validation gate fails after remediation
- Ignore global standards from any guide
- Skip TDD in any prompt
- Log PHI
- Use Vitest (Jest only)
- Use npm (pnpm only)
- Use raw SQL (Prisma only)
- Modify files not specified in current prompt
- Skip prerequisite checks (unless --force)
- Skip deep artifact verification (content assertions)
- Forget to process Jira updates after each subagent returns

## Invocation Examples

```
> Run all tenant provisioning guides
> Execute the tenant provisioning pipeline (guides 1 through 3)
> Run guide queue at .claude/guide-queues/tenant-provisioning.json
> Continue queue from guide 2
> Run guides 1 through 3 with validation between each
> Execute tenant provisioning guides sequentially with validation
```
