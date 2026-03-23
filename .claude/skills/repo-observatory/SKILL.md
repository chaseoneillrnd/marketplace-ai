---
name: repo-observatory
description: Comprehensive repository visualization, analysis, and observatory for Benefitly. Use when "visualize the repo", "show me bottlenecks", "where are test gaps", "what are the scaling concerns", "generate repo report", "update observatory", "show dependency graph", "identify antipatterns", "dead code scan", "repo health dashboard", "infrastructure topology", "concern map", "action plan for improvements", "what needs attention", "repo overview", or any request to analyze, visualize, or report on codebase health, architecture, test coverage, data flows, or areas of concern. Operates in three modes: dashboard (full scan), analyst (targeted query), observatory (persistent docs). Orchestrates via subagent dispatch to codebase-health-check, codebase-map-generator, observability-master, and other existing skills. Produces Mermaid diagrams, scored reports, and action plans with file:line citations.
---

<ALIGNMENT-GATE>
Before executing action plans from observatory findings, read `docs/benefitly-master-agent-docs/MANIFEST.md`. If the target area shows SUMMON → invoke benefitly-expert before acting on findings. If no entry exists for this work → invoke benefitly-expert (mandatory). Observatory analysis can run freely; acting on findings requires alignment.
</ALIGNMENT-GATE>

# Repo Observatory

Orchestrate repository-wide analysis, produce Mermaid visualizations, and maintain a persistent observatory of health reports and action plans.

## Mode Detection

Classify the user's request into exactly one mode:

| Mode | Match When | Behavior |
|------|-----------|----------|
| **Dashboard** | "visualize the repo", "full scan", "repo health", "repo overview", "dashboard", or no specific dimension requested | Run all 7 dimensions, write observatory docs, present summary |
| **Analyst** | Request names a specific concern: "test gaps", "bottlenecks", "scaling", "dead code", "antipatterns", a specific domain like "plan domain" | Run targeted dimension(s), present focused report, offer to update observatory |
| **Observatory** | "update observatory", "sync repo docs", "regenerate reports" | Run analysis, write only to `docs/ai-agent-docs/`, confirm changes |

**Scope parsing:**
- Domain filter: "in plan domain" → scope all analysis to `libs/plan/` and related `apps/api/src/handlers/plans/`
- Dimension filter: "only test coverage" → run dimension 4 only
- No filter → all 7 dimensions, all domains

Announce detected mode: "Running **[mode]** mode — [dimensions] across [scope]."

## Seven Analysis Dimensions

Each dimension maps to a subagent dispatch. Subagents receive focused prompts and return structured findings.

### Dispatch Table

| # | Dimension | Subagent Skill(s) | Subagent Prompt Summary | Mermaid Type |
|---|-----------|-------------------|------------------------|--------------|
| 1 | Infrastructure Topology | `observability-master` | "Scan CDK stacks in `infrastructure/src/stacks/`, map Lambda→service→database connections. Return: list of nodes (service name, type, stack) and edges (source→target, connection type)." | `graph TD` with subgraphs per wave |
| 2 | Concern Areas | `codebase-health-check` | "Run full health check. Return: all findings as structured list with `{file, line, severity, category, description}`." | `graph TD` color-coded by severity |
| 3 | Data Flows | `rag-pipeline-principal-engineer` + `benefitly-expert` | "Trace the document processing pipeline from upload to chat retrieval. Return: ordered list of steps with `{step, service, file, description}`." | `sequenceDiagram` |
| 4 | Test Coverage Map | `codebase-health-check` | "Run checks 3a and 3b only. Return: per-domain `{domain, sourceFiles, testFiles, ratio, untestedFiles[]}`." | `graph TD` colored by ratio |
| 5 | Dependency Graph | `codebase-map-generator` | "Analyze cross-domain imports. Return: list of edges `{from, to, importCount}` and circular deps." | `graph LR` with labeled edges |
| 6 | Deployment Architecture | `observability-master` | "Map CDK wave dependencies from `infrastructure/src/stacks/`. Return: waves with stack lists and inter-wave dependencies." | `graph TD` wave layers |
| 7 | Complexity Heatmap | `codebase-health-check` | "Run check 2b (files >500 LOC). Also count total LOC and file count per domain. Return: `{domain, totalLOC, fileCount, hotspots[]}`." | `graph TD` with LOC annotations |

### Subagent Grouping for Parallel Dispatch

Use the `dispatching-parallel-agents` pattern. Group into 4 parallel agents:

```
Agent A (codebase-health-check): Dimensions 2, 4, 7
  → "Run the full codebase-health-check skill. Additionally, count LOC per domain
     and list per-domain test:source ratios. Return ALL findings as structured
     JSON with {file, line, severity, category, description} plus domain-level
     metrics {domain, totalLOC, fileCount, sourceFiles, testFiles, testRatio,
     hotspots[], untestedFiles[]}."

Agent B (codebase-map-generator): Dimension 5
  → "Analyze cross-domain import relationships across libs/ and apps/. Return
     structured JSON: {edges: [{from, to, importCount}], circularDeps: [{cycle}]}."

Agent C (observability-master): Dimensions 1, 6
  → "Scan infrastructure/src/stacks/ to map: (1) all CDK stacks with their
     resources (Lambdas, DynamoDB tables, S3 buckets, API Gateways, etc.) and
     connections between them, (2) CDK wave groupings and inter-wave dependencies.
     Return structured JSON: {stacks: [{name, wave, resources[], dependencies[]}],
     waves: [{number, stacks[]}]}."

Agent D (rag-pipeline + benefitly-expert): Dimension 3
  → "Trace the complete document processing pipeline: PDF upload → S3 → SQS →
     Step Functions (all 9 steps) → DynamoDB/Aurora PG. Also trace the chat
     request flow: user message → API → RAG retrieval → Bedrock → response.
     Return structured JSON: {pipelines: [{name, steps: [{name, service, file,
     description}]}]}."
```

## Synthesis Layer

After all subagents return, synthesize results into reports and diagrams.

### Mermaid Generation

For each dimension, generate a Mermaid diagram from the structured findings:

**Infrastructure Topology** — `graph TD` with `subgraph` per CDK wave. Nodes = services/resources, edges = connections.

**Concern Areas** — `graph TD` with domain nodes. Apply `style` fills:
- Red `#ff6b6b` = has Critical findings
- Yellow `#ffd93d` = has High findings (no Critical)
- Green `#6bff6b` = clean or Low only
- Node label includes finding count

**Data Flows** — `sequenceDiagram` with participants for each service. One diagram per pipeline (document processing, chat request).

**Test Coverage** — `graph TD` with domain nodes. Color by ratio: Red < 0.3, Yellow 0.3-0.6, Green > 0.6. Label shows "N/M files tested."

**Dependency Graph** — `graph LR` with domain nodes and labeled edges showing import count. Highlight circular deps in red.

**Deployment Architecture** — `graph TD` with horizontal subgraph layers per wave. Stack nodes inside each wave.

**Complexity Heatmap** — `graph TD` with domain nodes. Label includes LOC count. Color: Red >5000, Yellow 2000-5000, Green <2000.

### Scoring

Score each dimension 1-10:
- **Finding-based dimensions** (2, 4, 5, 7): Start at 10. Deductions: Critical -3, High -1.5, Medium -0.5, Low -0.1. Minimum: 1.
- **Structural dimensions** (1, 3, 6): Score based on completeness. 10 = all expected nodes/steps mapped with files. -2 per missing expected component. -1 per connection that couldn't be traced. Minimum: 1.

### Fallback for Missing Data

If a subagent skill is unavailable or returns no data for a dimension:
- Note the gap in the report: "Dimension could not be scored — subagent returned no data."
- Score as `—/10` (unscored), do not include in overall health summary average.
- Flag in action plan: "P1: Enable [dimension] analysis — [reason for gap]."

### Action Plan Generation

1. Collect all findings across dimensions, sort by severity then frequency
2. Assign priority: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
3. Group related findings into remediation batches by theme/domain
4. Per batch: estimate effort (S <1hr, M 1-4hr, L 4hr+), note scope, suggest `technical-guide-architect` guide title

## Output Writing

### Dashboard Mode

1. Write 7 individual reports to `docs/ai-agent-docs/[dimension].md`
2. Write master `docs/ai-agent-docs/repo-observatory.md`
3. Write action plan to `docs/ai-agent-docs/action-plans/YYYY-MM-DD-action-plan.md`
4. Present summary to user: health table + top 5 concerns + Mermaid overview

### Analyst Mode

1. Present findings + Mermaid diagram in console only
2. Do NOT write observatory docs unless user asks
3. Offer: "Want me to update the observatory with these findings?"

### Observatory Mode

1. Same writes as Dashboard but do not present the full health table or Mermaid diagrams
2. Confirm only: "Observatory updated. [N] findings across [M] dimensions."

### Delta Tracking

When updating existing reports:
- Read existing report, count previous findings by severity
- After writing, note delta in header: "Delta: +N new, -M resolved"
- Master dashboard trend arrows: ↑ (improved), ↓ (declined), → (unchanged)

## Report Templates

### Master Dashboard (`repo-observatory.md`)

```
# Benefitly Repository Observatory

**Last scan**: YYYY-MM-DD | **Branch**: [branch] | **Commit**: [short SHA]

## Health Summary

| Dimension | Score | Trend | Top Finding |
|-----------|-------|-------|-------------|
| Infrastructure Topology | X/10 | ↑↓→ | [1-line] |
| Concern Areas | X/10 | ↑↓→ | [1-line] |
| Data Flows | X/10 | ↑↓→ | [1-line] |
| Test Coverage | X/10 | ↑↓→ | [1-line] |
| Dependencies | X/10 | ↑↓→ | [1-line] |
| Deployment | X/10 | ↑↓→ | [1-line] |
| Complexity | X/10 | ↑↓→ | [1-line] |

## Architecture Overview
[Compact infrastructure topology Mermaid]

## Hottest Concerns
[Top 5 findings with file:line citations]

## Reports
- [Infrastructure Topology](infrastructure-topology.md)
- [Concern Areas](concern-areas.md)
- [Data Flows](data-flows.md)
- [Test Coverage Map](test-coverage-map.md)
- [Dependency Graph](dependency-graph.md)
- [Deployment Architecture](deployment-architecture.md)
- [Complexity Heatmap](complexity-heatmap.md)

## Latest Action Plan
- [YYYY-MM-DD Action Plan](action-plans/YYYY-MM-DD-action-plan.md)
```

### Individual Report (`[dimension].md`)

```
# [Dimension Name]

**Last updated**: YYYY-MM-DD | **Score**: X/10 | **Delta**: +N new, -M resolved

## Diagram
[Full Mermaid diagram]

## Findings

### Critical
- `file:line` — description

### High / Medium / Low
- `file:line` — description

## Recommendations
1. [action] — effort: S/M/L — guide-ready: yes/no
```

### Action Plan (`action-plans/YYYY-MM-DD-action-plan.md`)

```
# Action Plan — YYYY-MM-DD

**Total findings**: N (C critical, H high, M medium, L low)

## Prioritized Checklist
- [ ] **P0**: [finding] — `file:line` — effort: S
- [ ] **P1**: [finding] — `file:line` — effort: M

## Remediation Batches (technical-guide-architect ready)

### Batch 1: [Theme] (effort: S)
- Findings: [list]
- Scope: `libs/[domain]/`
- Suggested guide: "[title]"
```

## Critical Guidelines

**DO:**
- Dispatch to existing skills — never analyze code directly
- Use `dispatching-parallel-agents` pattern for subagent grouping
- Generate Mermaid diagrams dynamically from structured findings
- Include `file:line` citations on every finding
- Score dimensions consistently (10-point scale)
- Track deltas between runs
- Group action plans into `technical-guide-architect`-ready batches

**DO NOT:**
- Grep, Glob, or Read source files directly (subagents do this)
- Duplicate analysis logic from existing skills
- Generate static/hardcoded Mermaid diagrams
- Skip delta tracking when updating existing reports
- Write observatory docs in Analyst mode unless user asks
- Run all dimensions when user asked for a specific one
