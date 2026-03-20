---
name: systematic-debugging
description: Use when facing bugs, test failures, or unexpected behavior — requires root cause investigation before any fix attempts.
---

# Systematic Debugging

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

## Four-Phase Framework

### Phase 1: Root Cause Investigation
- Examine error messages thoroughly
- Reproduce issue consistently
- Review recent modifications
- Gather diagnostic evidence

### Phase 2: Pattern Analysis
- Locate comparable working implementations
- Consult reference materials
- Identify specific differences
- Understand all dependencies

### Phase 3: Hypothesis and Testing
- Formulate explicit hypothesis
- Make minimal test change
- Verify result before proceeding

### Phase 4: Implementation
- Create failing test case
- Implement single correction
- Verify success

## Escalation Rule

If 3+ fix attempts fail: STOP. Question whether the underlying pattern or architecture needs fundamental reconsideration.

## Red Flags — STOP

- Proposing solutions before understanding data flow
- Attempting multiple simultaneous fixes
- Rationalizing shortcuts under time pressure
- Guess-and-check without hypothesis
