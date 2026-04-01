"""Smoke test: create_app() registers all blueprints without import errors."""
from __future__ import annotations

from typing import Any


EXPECTED_BLUEPRINTS = {
    "health",
    "skills",
    "users",
    "social",
    "submissions",
    "flags",
    "feedback",
    "roadmap",
    "admin",
    "analytics",
    "exports",
    "review_queue",
}


class TestAppSmoke:
    def test_all_blueprints_registered(self, app: Any) -> None:
        registered = set(app.blueprints.keys())
        missing = EXPECTED_BLUEPRINTS - registered
        assert not missing, f"Blueprints not registered: {missing}"

    def test_health_endpoint(self, client: Any) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
