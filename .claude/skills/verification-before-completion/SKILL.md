---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing — requires running verification commands and confirming output before making any success claims; evidence before assertions always.
---

# Verification Before Completion

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status:
1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command: 0 failures | Previous run, "should pass" |
| Linter clean | Linter: 0 errors | Partial check |
| Build succeeds | Build: exit 0 | Linter passing |
| Bug fixed | Original symptom passes | Code changed, assumed fixed |

## Red Flags — STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification
- About to commit without verification
- Trusting agent success reports without evidence
- Relying on partial verification

## The Bottom Line

Run the command. Read the output. THEN claim the result. Non-negotiable.
