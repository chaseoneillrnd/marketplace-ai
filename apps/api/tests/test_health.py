"""Tests for the health check endpoint."""

from __future__ import annotations


class TestHealthEndpoint:
    """Health check should be publicly accessible."""

    def test_health_returns_200(self, client: any) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_has_status_ok(self, client: any) -> None:
        response = client.get("/health")
        data = response.get_json()
        assert data["status"] == "ok"

    def test_health_response_has_version(self, client: any) -> None:
        response = client.get("/health")
        data = response.get_json()
        assert "version" in data
        assert data["version"] == "0.0.1-test"
