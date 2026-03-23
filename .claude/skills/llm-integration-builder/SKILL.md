---
name: llm-integration-builder
description: Use when integrating LLM calls via LiteLLM/Bedrock for evaluation or content generation
---

# LLM Integration Builder

## OpenAI-Spec Endpoint

```python
import httpx

async def call_llm(prompt: str, content: str) -> dict:
    if not settings.LLM_ROUTER_URL:
        return {"pass": True, "score": 85, "findings": [], "skipped": True}

    response = await httpx.AsyncClient().post(
        f"{settings.LLM_ROUTER_URL}/v1/chat/completions",
        json={
            "model": "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": content}
            ]
        },
        timeout=30.0
    )
    return parse_verdict(response.json())
```

## Feature Flag Gate

```python
flag = db.query(FeatureFlag).filter_by(key="llm_judge_enabled").first()
if not flag or not flag.enabled:
    return JudgeVerdict(passed=True, score=85, findings=[], skipped=True)
```

## Verdict Schema

```json
{"pass": true, "score": 82, "findings": [
  {"severity": "medium", "category": "quality", "message": "..."}
], "summary": "..."}
```

Score >= 70 = pass. Any CRITICAL finding = auto-fail.

## References

- LLM judge: `apps/api/skillhub/services/llm_judge.py`
- Submission service: `apps/api/skillhub/services/submission.py`
- Flag: `llm_judge_enabled` in seed data
