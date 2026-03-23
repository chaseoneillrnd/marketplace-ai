---
name: submission-gate-builder
description: Use when extending the 3-gate submission pipeline or adding new validation gates
---

# Submission Gate Builder

## State Machine

```
submitted → gate1_running → gate1_passed → gate2_running → gate2_passed → gate3_pending → gate3_approved → published
                          → gate1_failed                  → gate2_failed                  → rejected
                                                          → gate2_flagged → gate3_pending → gate3_changes_requested → submitted
```

## Gate Pattern

```python
def run_gate(submission_id: str, db: Session):
    submission = db.query(Submission).get(submission_id)
    submission.status = "gateN_running"

    result = evaluate(submission)

    gate_result = SubmissionGateResult(
        submission_id=submission.id,
        gate=N,
        result="pass" | "fail" | "flagged",
        findings=result.findings,  # JSONB
        score=result.score,
    )
    db.add(gate_result)
    submission.status = f"gateN_{'passed' if result.passed else 'failed'}"
```

## Gate Actors

| Gate | Actor | Trigger |
|------|-------|---------|
| 1 | Schema validator | Sync on POST /submissions |
| 2 | LLM Judge (Bedrock) | Async, feature-flagged |
| 3 | Platform Team human | POST /admin/submissions/{id}/review |

## LLM Judge (Gate 2)

- Feature flag: `llm_judge_enabled`
- If disabled: auto-pass with score=85, skipped=true
- Score >= 70 required. Any CRITICAL finding = auto-fail.

## References

- Submission service: `apps/api/skillhub/services/submission.py`
- LLM judge: `apps/api/skillhub/services/llm_judge.py`
- Models: `libs/db/skillhub_db/models/submission.py`
