---
name: test-driven-development
description: Use when writing any production code, implementing features, or fixing bugs — requires writing failing tests before implementation code; RED-GREEN-REFACTOR cycle enforced.
---

# Test-Driven Development

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Code written before tests must be deleted entirely — keeping it as reference violates the methodology.

## The Cycle

### RED
1. Write a minimal failing test
2. Run it — watch it FAIL
3. Failure proves the test actually tests something

### GREEN
1. Write the SIMPLEST code to pass the test
2. No more, no less
3. Run tests — watch them PASS

### REFACTOR
1. Clean up while green
2. Run tests after each change
3. Never refactor while red

## Verification Checklist

Before claiming TDD compliance:
- [ ] Every function has corresponding tests
- [ ] Each test failed before implementation
- [ ] All tests use real code paths (not mocked behavior)
- [ ] Tests are minimal (one behavior each)
- [ ] Tests have clear, descriptive names

## Common Rationalizations (All Invalid)

| Excuse | Reality |
|--------|---------|
| "Tests written after still verify" | They pass immediately, proving nothing |
| "I tested manually" | Not systematic, not re-runnable |
| "The code is simple" | Simple code still needs tests |
| "Hard to test" | Design problem — fix the design |
| "Spirit matters more than ritual" | The ritual IS the spirit |

## Red Flags — STOP

- Writing implementation before test
- Test passes on first run (never saw red)
- Rationalizing shortcuts as exceptions
- Mocking the thing you're testing
- Tests that test the test framework
