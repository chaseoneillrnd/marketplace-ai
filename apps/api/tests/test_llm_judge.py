"""Tests for LLM Judge service — Gate 2 evaluation."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skillhub.schemas.submission import GateFinding, JudgeVerdict
from skillhub.services.llm_judge import LLMJudgeService, evaluate_gate2_sync


# --- evaluate_gate2_sync ---


class TestEvaluateGate2Sync:
    def test_disabled_returns_pass(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": True},
            score=85,
            findings=[],
            summary="Skipped",
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_passed"
        assert data["result"] == "passed"
        assert data["score"] == 85

    def test_critical_finding_fails(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": False},
            score=60,
            findings=[
                GateFinding(severity="critical", category="security", description="SQL injection risk"),
            ],
            summary="Critical issue found",
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_failed"
        assert data["result"] == "failed"

    def test_score_below_70_fails(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": True},
            score=65,
            findings=[],
            summary="Low quality",
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_failed"
        assert data["result"] == "failed"

    def test_score_above_70_no_critical_passes(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": True},
            score=82,
            findings=[
                GateFinding(severity="low", category="style", description="Minor style issue"),
            ],
            summary="Good quality",
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_passed"
        assert data["result"] == "passed"
        assert data["score"] == 82

    def test_high_finding_flagged(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": True},
            score=75,
            findings=[
                GateFinding(severity="high", category="quality", description="Potential issue"),
            ],
            summary="Flagged for review",
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_flagged"
        assert data["result"] == "flagged"

    def test_pass_false_fails(self) -> None:
        verdict = JudgeVerdict(
            **{"pass": False},
            score=80,
            findings=[],
            summary="Failed by judge",
        )
        status, data = evaluate_gate2_sync(verdict)
        assert status == "gate2_failed"
        assert data["result"] == "failed"


# --- LLMJudgeService ---


class TestLLMJudgeService:
    @pytest.mark.asyncio
    async def test_disabled_skips(self) -> None:
        service = LLMJudgeService(router_url="http://fake", enabled=False)
        verdict = await service.evaluate("some content")
        assert verdict.pass_ is True
        assert verdict.score == 85
        assert verdict.summary == "Skipped — LLM judge disabled"

    @pytest.mark.asyncio
    async def test_empty_url_skips(self) -> None:
        service = LLMJudgeService(router_url="", enabled=True)
        verdict = await service.evaluate("some content")
        assert verdict.pass_ is True
        assert verdict.score == 85

    @pytest.mark.asyncio
    async def test_timeout_returns_failure(self) -> None:
        import httpx

        service = LLMJudgeService(router_url="http://fake", enabled=True)
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("timeout")):
            verdict = await service.evaluate("content")
        assert verdict.pass_ is False
        assert verdict.score == 0
        assert any("timed out" in f.description for f in verdict.findings)

    @pytest.mark.asyncio
    async def test_http_error_returns_failure(self) -> None:
        import httpx

        service = LLMJudgeService(router_url="http://fake", enabled=True)
        with patch("httpx.AsyncClient.post", side_effect=httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock())):
            verdict = await service.evaluate("content")
        assert verdict.pass_ is False
        assert verdict.score == 0

    @pytest.mark.asyncio
    async def test_successful_evaluation(self) -> None:
        service = LLMJudgeService(router_url="http://fake", enabled=True)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "pass": True,
                        "score": 88,
                        "findings": [],
                        "summary": "Good skill",
                    }),
                },
            }],
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            verdict = await service.evaluate("good content")

        assert verdict.pass_ is True
        assert verdict.score == 88
        assert verdict.summary == "Good skill"
