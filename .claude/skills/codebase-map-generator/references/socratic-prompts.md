# Socratic Probing Questions — Exact Prompts

Use these exact prompts (with placeholders filled in) during socratic probing phase. Ask one question at a time, listen to answers, then ask the next.

## Question 1: Domain Boundaries Validation

**Prompt**:
```
I scanned your repo and detected these top-level directory groupings:

[LIST DETECTED DIRECTORIES]

Are these your core architectural domains, or should I reorganize them?
```

**Options**:
- "Yes, that's right"
- "Close, but rename [domain] to [new name]"
- "No, here's the actual structure: [user input]"
- "A mix—I'll tell you which to keep/change"

**What to listen for**:
- User confirms domain structure, or
- User corrects domain names/boundaries
- User identifies missing domains
- User merges/splits domains

**Store**: Updated domain list for template selection.

---

## Question 2: Naming Preferences

**Prompt**:
```
For domain sections, would you prefer:

A) Path-accurate (e.g., "libs/auth/feature")
B) Concise labels (e.g., "Auth Domain")
C) Mix of both (e.g., "Auth Domain (libs/auth/feature)")
```

**Options**:
- A (path-accurate)
- B (concise)
- C (mixed)
- D (custom style)

**What to listen for**:
- User's preference for readability vs. specificity

**Store**: Naming style for all domain sections.

---

## Question 3: Optional Sections

**Prompt**:
```
I found the following in your repo:

☐ Prisma schema (database models)
☐ CDK/Terraform infrastructure code
☐ Feature flags / configuration
☐ [Other detected optional content]

Which of these should I include in the codebase map?
```

**Options**:
- Checkboxes (user selects which to include)
- "All of them"
- "None of them"
- "Only [user specifies]"

**What to listen for**:
- Which optional sections matter to the user
- Whether repo has DB schema, infra code, config complexity

**Store**: Selected optional sections for map generation.

---

## Question 4: Architectural Focus

**Prompt**:
```
When agents navigate your codebase, which areas should they find first? 

Select your top 3 priorities:

☐ [Domain 1]
☐ [Domain 2]
☐ [Domain 3]
☐ [Domain 4]
☐ [Domain 5]
☐ Configuration & Setup
☐ Testing & Quality
☐ Infrastructure & Deployment
```

**Options**:
- Checkboxes (user selects top 3)
- "Everything equally important"
- "List your priorities in order"

**What to listen for**:
- Which domains are most critical for agent understanding
- Whether testing, config, or infra matter for navigation

**Store**: Domain priority order (affects template emphasis + section ordering).

---

## Question 5: Map Location

**Prompt**:
```
Where should I save your codebase map?

A) docs/ai-agent-context/codebase-map.md (recommended)
B) docs/codebase-map.md
C) [Custom path]
```

**Options**:
- A (recommended default)
- B (alternative)
- C (custom input)

**What to listen for**:
- User's documentation structure preference
- Whether they already have a docs/ directory

**Store**: File path for map output.

---

## Question 6: Post-Creation Doc Updates (After Map Finalized)

**Prompt**:
```
Your codebase map is ready. I can update up to 2 of your "always-in-context" project files to reference it:

Detected files:
☐ constitution.md (immutable project rules)
☐ CLAUDE.md (Claude Code project memory)
☐ .ruler/AGENTS.md (agent instructions)
☐ [Other relevant file]

Which 2 should I update with references to the codebase map?
```

**Options**:
- Checkboxes (user selects up to 2)
- "None, just save the map"
- "All of them" (if user confirms context budget)

**What to listen for**:
- User's preference for which docs to keep in sync
- Whether they want CLAUDE.md vs. constitution vs. .ruler/ updated

**Store**: Files to update + changes to preview.

---

## Conditional Question: Discrepancy Detection (If needed during iteration)

**Prompt**:
```
I noticed a potential inconsistency:

[DESCRIBE DISCREPANCY]

How should I handle this?
```

**Example discrepancies**:
- Directory path in map doesn't match current git state
- Domain listed in one section but not another
- Import patterns suggest domain boundary differs from stated structure

**Options**:
- "Update to match [user preference]"
- "Remove [stale item]"
- "It's fine, keep as is"

**Store**: User decision for sync logic.

---

## Conditional Question: Sync Mode (If regenerating existing map)

**Prompt**:
```
I'm regenerating your codebase map. I found:

+ [N] new files/domains
- [M] deleted/stale items
~ [K] partially changed items

Should I:

A) Fully regenerate (replace everything based on current state)
B) Surgical update (keep your edits, update facts only)
C) Interactive (show me changes, you approve each one)
```

**Options**:
- A (full regen)
- B (surgical/smart)
- C (interactive)

**What to listen for**:
- User's tolerance for automated changes
- Whether they've customized the previous map heavily

**Store**: Sync strategy for regeneration.

---

## Flow Diagram

```
Q1: Domain Boundaries?
  ↓ (user confirms/corrects)
Q2: Naming preference?
  ↓ (user selects style)
Q3: Optional sections?
  ↓ (user selects what to include)
Q4: Architectural focus?
  ↓ (user selects top 3 areas)
Q5: Map location?
  ↓ (user confirms path)
→ Generate map in artifact
  ↓ (user reviews/iterates)
→ Finalize map to disk
Q6: Post-creation doc updates?
  ↓ (user selects up to 2 files)
→ Preview proposed changes
→ Execute with consent
→ Done
```

---

## Tips for Asking Questions

1. **One at a time**: Don't overwhelm with all 5 questions at once
2. **Use checkboxes**: Multiple-choice is faster than open-ended text
3. **Provide context**: Show what you detected before asking preference
4. **Listen actively**: If user says something unexpected, ask a follow-up clarifying question
5. **Validate answers**: "So you want me to [restate]—correct?"
6. **Store responses**: Keep user answers in memory for templating logic
7. **Skip if obvious**: If tech stack clearly tells the story (e.g., pnpm-workspace.yaml), skip Q2 naming
