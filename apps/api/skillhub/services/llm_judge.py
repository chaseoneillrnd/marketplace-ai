"""LLM Judge service — Gate 2 evaluation via Bedrock router."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from skillhub.schemas.submission import GateFinding, JudgeVerdict

logger = logging.getLogger(__name__)

# System prompt for the LLM judge
JUDGE_SYSTEM_PROMPT = """You are a skill quality evaluator for SkillHub.
Evaluate the submitted skill content for quality, security, and usefulness.
Return a JSON object with:
- pass: boolean (true if score >= 70 and no critical findings)
- score: integer 0-100
- findings: array of {severity: "low"|"medium"|"high"|"critical", category: string, description: string}
- summary: string (brief evaluation summary)
"""


class LLMJudgeService:
    """Evaluates skill content via LLM router."""

    def __init__(self, router_url: str, enabled: bool = True) -> None:
        self.router_url = router_url
        self.enabled = enabled

    async def evaluate(self, content: str) -> JudgeVerdict:
        """Evaluate skill content. Returns JudgeVerdict.

        If disabled or router_url is empty, returns a skip verdict.
        On HTTP error/timeout, returns a safe failure verdict.
        """
        if not self.enabled or not self.router_url:
            return JudgeVerdict(
                **{"pass": True},
                score=85,
                findings=[],
                summary="Skipped — LLM judge disabled",
            )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.router_url}/v1/chat/completions",
                    json={
                        "model": "skillhub-judge",
                        "messages": [
                            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                            {"role": "user", "content": content},
                        ],
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                data = response.json()
                message_content = data["choices"][0]["message"]["content"]

                import json

                verdict_data = json.loads(message_content)
                return JudgeVerdict(**verdict_data)

        except httpx.TimeoutException:
            logger.warning("LLM judge timed out")
            return JudgeVerdict(
                **{"pass": False},
                score=0,
                findings=[
                    GateFinding(
                        severity="high",
                        category="quality",
                        description="Judge unavailable — request timed out",
                    ),
                ],
                summary="Judge unavailable — timeout",
            )
        except Exception:
            logger.exception("LLM judge error")
            return JudgeVerdict(
                **{"pass": False},
                score=0,
                findings=[
                    GateFinding(
                        severity="high",
                        category="quality",
                        description="Judge unavailable",
                    ),
                ],
                summary="Judge unavailable — error",
            )


def evaluate_gate2_sync(
    verdict: JudgeVerdict,
) -> tuple[str, dict[str, Any]]:
    """Determine Gate 2 status from a JudgeVerdict.

    Returns (status_value, gate_result_dict).
    """
    has_critical = any(f.severity == "critical" for f in verdict.findings)

    if has_critical or not verdict.pass_:
        status = "gate2_failed"
        result = "failed"
    elif verdict.score < 70:
        status = "gate2_failed"
        result = "failed"
    elif any(f.severity == "high" for f in verdict.findings):
        status = "gate2_flagged"
        result = "flagged"
    else:
        status = "gate2_passed"
        result = "passed"

    findings = [
        {"severity": f.severity, "category": f.category, "description": f.description}
        for f in verdict.findings
    ]

    return status, {
        "result": result,
        "score": verdict.score,
        "findings": findings,
        "summary": verdict.summary,
    }
