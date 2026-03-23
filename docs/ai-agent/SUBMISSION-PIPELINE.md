# Submission Pipeline

3-gate review pipeline for skill submissions.

## State Machine

```
[*] → submitted → gate1_passed → gate2_passed → approved → published
                 → gate1_failed   → gate2_flagged → rejected
                                  → gate2_failed   → gate3_changes_requested
```

## Gate Details

### Gate 1: Automated Validation (sync)
- Runs synchronously on `POST /api/v1/submissions`
- Checks: required frontmatter fields, slug uniqueness, min 3 trigger phrases, short_desc ≤80 chars
- Jaccard similarity check on trigger phrases (threshold >0.7 against existing skills)
- Auto-triggers Gate 2 via `BackgroundTasks` when `llm_judge_enabled` flag is true
- Result: `passed` or `failed`

### Gate 2: LLM Judge Scan (async)
- Auto-triggered as background task after Gate 1 pass (when flag enabled)
- Also manually triggerable: `POST /api/v1/admin/submissions/{id}/scan`
- When `llm_judge_enabled=false`: returns `skipped=True`, `score=0`, auto-pass
- When enabled: calls Bedrock router, evaluates security/quality/sensitivity
- Result: `passed`, `flagged`, or `failed`

### Gate 3: Human Review
- `POST /api/v1/admin/submissions/{id}/review` (platform team only)
- Decision: `approved`, `rejected`, or `changes_requested`
- On approval: creates Skill + SkillVersion, sets `published_at` to current time
- `content_hash` is SHA256 of submission content

## Statuses

| Status | Meaning |
|---|---|
| `submitted` | Awaiting Gate 1 |
| `gate1_passed` | Passed validation, awaiting Gate 2 |
| `gate1_failed` | Failed validation |
| `gate2_passed` | LLM approved, awaiting human review |
| `gate2_flagged` | LLM flagged concerns |
| `gate2_failed` | LLM rejected |
| `gate3_changes_requested` | Reviewer requested changes |
| `approved` | Ready to publish |
| `rejected` | Rejected |
| `published` | Live in marketplace |

## Key Files

- `apps/api/skillhub/routers/submissions.py` — endpoints
- `apps/api/skillhub/services/submissions.py` — gate logic + publish
- `apps/api/skillhub/services/llm_judge.py` — LLM judge service
- `libs/db/skillhub_db/models/submission.py` — models
