"""Tests for the /health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_status_ok_and_version(client: TestClient) -> None:
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.0.1-test"
