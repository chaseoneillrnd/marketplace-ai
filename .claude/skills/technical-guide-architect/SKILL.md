---
name: technical-guide-architect
description: Elite technical documentation architect for agent-executable implementation guides. Use when creating technical handoff documents, Claude Code guides, development playbooks, implementation plans, or documentation guiding AI agents through multi-phase builds. Triggers on "create technical guide", "implementation guide", "Claude Code handoff", "development playbook", "build roadmap", or requests needing structured bite-sized prompts for complete implementations. ALWAYS begins with rigorous Socratic clarification to crystallize scope, stack, quality standards, and compliance before writing. Produces hierarchical guides (Stage-Phase-Prompt), TDD-first prompts with acceptance criteria, global standards, architecture overviews, quick-reference sequences, clear DO/DO NOT boundaries, AND a comprehensive Visual Architecture Companion document with Mermaid diagrams.
---

# Technical Guide Architect

Create comprehensive, agent-executable technical implementation guides through systematic Socratic clarification followed by structured documentation that baby-walks toward completion through bite-sized, focused prompts.

**ALWAYS produces TWO deliverables:**
1. **Technical Implementation Guide** — The main executable guide with prompts
2. **Visual Architecture Companion** — Mermaid diagram document for visual reference

## Core Philosophy

**Clarity compounds. Ambiguity multiplies.** Every minute spent on requirements clarification saves hours of rework. This skill front-loads understanding to produce laser-focused implementation guides.

**Path of least resistance.** Each prompt should accomplish the minimum viable vertical slice, establishing plumbing before polish. Guides spiral through the stack—broad first, then deep.

**Agents need guardrails.** Each prompt includes explicit acceptance criteria, task boundaries (DO/DO NOT), and definition of done. No room for interpretation drift.

**Visuals accelerate comprehension.** Complex systems require visual representation. Mermaid diagrams provide orientation before execution.

## The Guide Creation Protocol

### Phase 1: Rigorous Socratic Clarification

Upon receiving any technical guide request, immediately enter clarification mode. Do NOT write documentation until Phase 4.

**Round 1 - Project Scope (4-6 questions)**

Ask boundary-defining questions with concrete options:

```
QUESTION: [Probing question about scope/technology/constraints]
OPTIONS:
  A) [Most likely interpretation based on context]
  B) [Alternative interpretation]
  C) [Broader scope]
  D) [Narrower scope]
  E) Other: [invite specification]
```

**Essential Round 1 Questions:**
- What is the end deliverable? (Working MVP / Proof of concept / Production system / Architecture blueprint)
- Who is the guide's audience? (Claude Code / Human developer / Mixed team / Self-reference)
- What is the starting point? (Empty folder / Existing codebase / Partial implementation)
- What is the technology stack? (Specify or let me recommend based on requirements)
- What is the timeline/complexity? (Hours / Days / Weeks / Ongoing iteration)
- Are there compliance requirements? (HIPAA / SOC2 / GDPR / PCI-DSS / None / Other)

**Round 2 - Technical Depth (4-6 questions)**

Build from Round 1 answers:

- If MVP → "What features are in-scope for MVP vs future phases?"
- If compliance required → "What specific controls must be implemented from day one?"
- If Claude Code audience → "What context/memory will Claude Code have access to?"
- If existing codebase → "What architectural patterns must be followed?"

**Essential Round 2 Questions:**
- Testing philosophy? (TDD strict / Test-after / Coverage targets)
- Security requirements? (OWASP compliance / Specific threat model / Standard practices)
- Infrastructure approach? (IaC specific tool / Manual setup / Hybrid)
- Deployment target? (Cloud provider / On-prem / Hybrid / Local-first)
- Performance requirements? (Latency targets / Throughput / Scale expectations)
- Integration points? (APIs / Databases / External services / Auth providers)

**Round 3 - Quality Standards (3-4 questions)**

Define acceptance criteria framework:

- "What code quality standards are non-negotiable?" (Linting / Type safety / Coverage thresholds)
- "What documentation must accompany the code?" (Inline comments / README / API docs)
- "What defines 'done' for a prompt?" (Tests pass / Deploys / Manual verification)
- "What architectural principles must be enforced?" (Clean architecture / Domain-driven / Microservices)

**Round 4 - Success Criteria (2-3 questions)**

Crystallize completion:

- "What does the user see/do when MVP is complete?"
- "What would make this guide insufficient?"
- "What must be true for handoff to the next phase?"

### Phase 2: Project Context Documentation

Before writing prompts, document the crystallized understanding:

```
═══════════════════════════════════════════════════════════════════
PROJECT CONTEXT
═══════════════════════════════════════════════════════════════════

PROJECT: [Name]
DESCRIPTION: [One paragraph summary]

DELIVERABLE: [What the guide produces]
AUDIENCE: [Who executes the guide]
STARTING POINT: [What exists before the guide]

TECHNOLOGY STACK:
| Layer | Technology | Rationale |
|-------|------------|-----------|
| [layer] | [tech] | [why] |

COMPLIANCE REQUIREMENTS:
- [Requirement 1]: [Specific controls]
- [Requirement 2]: [Specific controls]

SUCCESS CRITERIA:
1. [Measurable outcome 1]
2. [Measurable outcome 2]
3. [Measurable outcome 3]

OUT OF SCOPE:
- [Explicit exclusion 1]
- [Explicit exclusion 2]

═══════════════════════════════════════════════════════════════════
Confirm this captures intent before proceeding.
```

Await explicit confirmation.

### Phase 3: Architecture Overview

Document the target architecture visually and textually:

**Data Flow Diagram:**
```
[Component] → [Connection] → [Component] → [Storage]
     ↑
[Auth Layer]
```

**Project Structure:**
```
project/
├── [directory]/
│   ├── [subdirectory]/
│   └── [file]
└── [config files]
```

**Architecture Decisions:**
- Why [choice A] over [choice B]: [Rationale tied to requirements]

### Phase 4: Global Standards & Acceptance Criteria

Define standards that apply to EVERY prompt:

```yaml
Code Quality:
  - [Standard 1 with specific threshold]
  - [Standard 2 with specific threshold]
  - [Standard 3 with specific threshold]

Testing Requirements:
  - [Test type]: [Coverage/approach]
  - [Test type]: [Coverage/approach]
  - TDD: Tests written BEFORE implementation

Security Requirements:
  - [Security control 1]
  - [Security control 2]
  - [Compliance-specific control]

Definition of Done (Every Prompt):
  - [ ] Tests pass (written first, TDD)
  - [ ] No type errors
  - [ ] No linting warnings
  - [ ] Security scan clean
  - [ ] Acceptance criteria met
```

### Phase 5: Prompt Architecture Design

Structure the guide hierarchically:

```
Stage [N]: [Major Milestone]
├── Phase [N.M]: [Feature Area]
│   ├── Prompt [N.M.P]: [Specific Task]
│   │   ├── Requirements
│   │   ├── File Structure
│   │   ├── Test-First Instructions
│   │   ├── Acceptance Criteria
│   │   └── DO NOT instructions
│   └── Prompt [N.M.P+1]: [Next Task]
└── Phase [N.M+1]: [Next Feature Area]
```

**Prompt Sequencing Principles:**
1. Vertical slices first (end-to-end plumbing before features)
2. Each prompt builds on previous prompts
3. No prompt assumes context not established by prior prompts
4. Prompts can be executed independently after prerequisites complete
5. Stage N+1 extends Stage N without rewrites

### Phase 6: Prompt Template

Every prompt follows this structure:

````markdown
#### Prompt [N.M.P]: [Descriptive Title]

```
[Complete prompt text that can be copy-pasted to Claude Code]

Requirements:
- [Specific requirement 1]
- [Specific requirement 2]
- [Specific requirement 3]

File structure:
[path]/
├── [file1]
├── [file2]
└── [file3]

Write tests FIRST for:
- [Test case 1]
- [Test case 2]
- [Test case 3]

Do NOT:
- [Anti-pattern 1]
- [Anti-pattern 2]

Acceptance Criteria:
- [ ] [Verifiable criterion 1]
- [ ] [Verifiable criterion 2]
- [ ] [Verifiable criterion 3]
- [ ] [Verifiable criterion 4]
```
````

**Prompt Design Rules:**
- 15-45 minutes estimated execution time per prompt
- Single responsibility—one coherent deliverable
- TDD instruction explicit in every prompt
- Acceptance criteria are binary (pass/fail)
- "Do NOT" section prevents common drift
- File structure explicit to prevent confusion

### Phase 7: Quick Reference Generation

Create a summary table at the end:

```markdown
## Quick Reference: Prompt Sequence

### Stage [N] (Execute in Order)

| # | Prompt | Est. Time | Key Output |
|---|--------|-----------|------------|
| N.M.P | [Title] | [X min] | [Deliverable] |
| N.M.P+1 | [Title] | [X min] | [Deliverable] |

**Stage [N] Total: ~X-Y hours**
```

Include:
- Total time estimate per stage
- Dependency indicators if non-linear
- Stage-to-stage handoff requirements

### Phase 8: Appendices

Include supporting reference material:

```markdown
## Appendices

### Appendix A: Environment Variables
[All env vars needed across the guide]

### Appendix B: IAM/Permissions
[Required permissions/roles]

### Appendix C: Testing Commands
[Commands to run tests]

### Appendix D: Deployment Commands
[Commands to deploy]

### Appendix E: Meta-Prompts for Quality
[Prompts to verify quality during execution]
```

### Phase 9: Visual Architecture Companion (REQUIRED)

**ALWAYS create a separate Mermaid diagram document** that provides visual architecture reference for the guide. This is NOT optional.

**File naming:** `[project]-diagrams.md`

**Required sections in the Visual Architecture Companion:**

```markdown
# [Project] — Visual Architecture Guide

> Supplementary diagrams for the Technical Implementation Guide
> Last Updated: [Date]

---

## Table of Contents
1. [Executive Overview](#1-executive-overview)
2. [Complete Architecture](#2-complete-architecture)
3. [Stage 1: [Name]](#3-stage-1-name)
4. [Stage 2: [Name]](#4-stage-2-name)
... (one section per stage)
N. [Data Models & State Transitions](#n-data-models)
N+1. [Infrastructure & Deployment](#n1-infrastructure)

---

## 1. Executive Overview

### 1.1 High-Level System Diagram
[Mermaid flowchart showing entire system]

### 1.2 Before/After Comparison (if migration/refactor)
[Side-by-side comparison diagrams]

### 1.3 Key Changes Summary
[Mermaid diagram highlighting what's new/changed]

---

## 2. Complete Architecture

### 2.1 End-to-End Flow
[Mermaid flowchart with all components]

### 2.2 Infrastructure Components
[Mermaid diagram of cloud/infrastructure resources]

### 2.3 Data Flow Sequence
[Mermaid sequence diagram showing full data path]

---

## 3. Stage 1: [Stage Name]

### 3.1 [Relevant Diagram Type]
[Class diagram / flowchart / etc.]

### 3.2 Implementation Flow
[Mermaid flowchart showing prompt sequence for this stage]

### 3.3 [Additional diagrams as needed]

---

[Repeat for each stage...]

---

## N. Data Models & State Transitions

### N.1 Entity Relationships
[Mermaid ERD or class diagram]

### N.2 State Machine (if applicable)
[Mermaid state diagram]

### N.3 Lifecycle Diagrams
[State transitions, object lifecycles]

---

## N+1. Infrastructure & Deployment

### N+1.1 Deployment Architecture
[Mermaid diagram of deployment topology]

### N+1.2 CI/CD Pipeline
[Mermaid flowchart of deployment steps]

### N+1.3 IAM/Permission Flow
[Mermaid diagram of permission relationships]

---

## Quick Reference: All Diagrams

| Section | Diagram | Purpose |
|---------|---------|---------|
| 1.1 | [Name] | [Purpose] |
| 1.2 | [Name] | [Purpose] |
... (table of all diagrams)
```

**Diagram requirements per stage:**
- Minimum 2-3 diagrams per stage
- At least one flowchart showing implementation sequence
- At least one diagram showing component relationships
- Include input/output contracts where applicable

**Mermaid diagram types to use:**
- `flowchart TB/LR` — Process flows, decision trees, component relationships
- `sequenceDiagram` — API calls, data flow, multi-actor interactions  
- `classDiagram` — Type systems, object models, interfaces
- `stateDiagram-v2` — State machines, lifecycles, status transitions
- `erDiagram` — Database schemas, entity relationships
- `gantt` — Timeline/schedule visualization (if relevant)

**Cross-reference in main guide:**

Add diagram references throughout the main Technical Implementation Guide:

```markdown
## Stage N: [Name]

> 📊 **Visual Reference:** See Section N+2 of `[project]-diagrams.md` for 
> [specific diagram descriptions and numbers].

### Phase N.1: [Name]
```

Add a Supplementary Materials block after the header:

```markdown
## Supplementary Materials

┌─────────────────────────────────────────────────────────────────────────────┐
│ COMPANION DOCUMENT                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  📊 [project]-diagrams.md                                                   │
│                                                                             │
│  Visual architecture guide with [N] Mermaid diagrams covering:              │
│  • Executive Overview: [summary] (Section 1)                                │
│  • Complete Architecture (Section 2)                                        │
│  • Stage-by-stage implementation flows (Sections 3-N)                       │
│  • Data models & state transitions (Section N+1)                            │
│  • Infrastructure & deployment (Section N+2)                                │
│                                                                             │
│  USAGE: Reference diagrams by section number when executing prompts.        │
│  Example: "See Diagram 5.3 for state machine visualization"                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Guide Structure Template

Final guide structure:

```markdown
# [Project] Technical Implementation Guide

## For [Audience] - Complete Handoff Document

**Project:** [Name]
**Starting Point:** [Prerequisites]
**Approach:** [Methodology summary]

---

## Supplementary Materials

┌─────────────────────────────────────────────────────────────────────────────┐
│ COMPANION DOCUMENT                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  📊 [project]-diagrams.md                                                   │
│  Visual architecture guide with [N] Mermaid diagrams                        │
└─────────────────────────────────────────────────────────────────────────────┘

---

## Table of Contents
1. [Project Context](#project-context)
2. [Architecture Overview](#architecture-overview)
3. [Global Standards & Acceptance Criteria](#global-standards)
4. [Pre-Flight Setup](#pre-flight-setup)
5. [Stage 1: [Milestone 1]](#stage-1)
6. [Stage 2: [Milestone 2]](#stage-2)
7. [Appendices](#appendices)

---

## Project Context
[From Phase 2]

## Architecture Overview

> 📊 **Visual Reference:** See Section 2 of `[project]-diagrams.md`

[From Phase 3]

## Global Standards & Acceptance Criteria
[From Phase 4]

## Pre-Flight Setup
[Prompts 0.1, 0.2, etc. for initial setup]

## Stage 1: [First Major Milestone]

> 📊 **Visual Reference:** See Section 3 of `[project]-diagrams.md`

### Phase 1.1: [First Feature Area]

#### Prompt 1.1.1: [First Task]
[Full prompt with all sections]

#### Prompt 1.1.2: [Second Task]
[Full prompt with all sections]

### Phase 1.2: [Second Feature Area]
...

### Phase 1.N: [Milestone N] Final Verification
[Verification checklist prompt]

## Stage 2: [Second Major Milestone]

> 📊 **Visual Reference:** See Section 4 of `[project]-diagrams.md`

### Phase 2.1: [Builds on Stage 1]
...

## Quick Reference: Prompt Sequence
[Summary tables]

## Appendices

> 📊 **Visual Reference:** See Section N+2 of `[project]-diagrams.md` for deployment diagrams

[Reference material]
```

## Critical Guidelines

**DO:**
- Ask 12-20 clarifying questions across 4 rounds before writing
- Include TDD instructions in EVERY prompt
- Provide explicit file structures
- Make acceptance criteria binary (verifiable yes/no)
- Include "Do NOT" sections to prevent drift
- Build prompts sequentially with clear dependencies
- Provide time estimates for planning
- Create verification prompts at milestone boundaries
- Include meta-prompts for quality checks
- Structure for copy-paste execution
- **ALWAYS create the Visual Architecture Companion document**
- **Include diagram references in every stage section**
- **Provide minimum 2-3 diagrams per stage**

**DO NOT:**
- Write any documentation before completing Socratic clarification
- Create prompts that assume context not established
- Leave acceptance criteria vague or subjective
- Skip the "Do NOT" section on any prompt
- Combine unrelated tasks in a single prompt
- Exceed 45 minutes estimated work per prompt
- Assume the executor knows unstated conventions
- Create prompts that require rewriting previous work
- Include "nice to have" items in MVP prompts
- Skip the quick reference summary
- **Skip the Visual Architecture Companion document**
- **Omit diagram references from the main guide**

## Efficiency Principles

1. **Scope Discipline**: Every prompt serves stated MVP goals. Defer everything else.

2. **Vertical Before Horizontal**: Establish end-to-end plumbing before adding features.

3. **Spiral Approach**: First pass creates skeleton, subsequent passes add flesh.

4. **Stage Independence**: Each stage produces a working state. Guides can pause between stages.

5. **Prompt Atomicity**: Each prompt can be re-run independently after prerequisites are met.

6. **Visual First**: Create architecture diagrams before writing prompts to ensure shared understanding.

## Output Delivery

After creating a guide, deliver **TWO files**:

1. **Technical Implementation Guide:** `[project]-technical-guide.md`
2. **Visual Architecture Companion:** `[project]-diagrams.md`

```markdown
**Deliverables:**

1. [View Technical Guide](link-to-guide)
2. [View Visual Architecture Companion](link-to-diagrams)

**Estimated Total Time:** X-Y hours
**Stages:** N
**Prompts:** M
**Diagrams:** D
**Recommended Session Breaks:** After Stage [X], [Y]
```

Both documents should be created and presented together. The Visual Architecture Companion is NOT optional—it is a required deliverable for every technical guide.