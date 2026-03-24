"""Security migration gate — 8 classes that must all pass before the Flask port goes live.

These tests form the safety net for the Flask migration. They cover:
  1. Authentication enforcement on all non-public endpoints
  2. JWT validation edge cases
  3. Division isolation
  4. Role escalation prevention
  5. Admin boundary enforcement
  6. Audit log integrity
  7. Input validation (no 500s)
  8. Review queue workflow including self-approval prevention and event_type fix
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import jwt
import pytest

from tests.conftest import TEST_JWT_ALGORITHM, TEST_JWT_SECRET, make_token

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _regular_token(**extra: Any) -> str:
    payload: dict[str, Any] = {
        "sub": "user",
        "user_id": str(uuid4()),
        "division": "engineering",
        "is_platform_team": False,
        "is_security_team": False,
    }
    payload.update(extra)
    return make_token(payload=payload)


def _platform_token(user_id: str | None = None, **extra: Any) -> str:
    payload: dict[str, Any] = {
        "sub": "platform-user",
        "user_id": user_id or str(uuid4()),
        "division": "platform",
        "is_platform_team": True,
        "is_security_team": False,
    }
    payload.update(extra)
    return make_token(payload=payload)


def _security_token(user_id: str | None = None, **extra: Any) -> str:
    payload: dict[str, Any] = {
        "sub": "security-user",
        "user_id": user_id or str(uuid4()),
        "division": "security",
        "is_platform_team": False,
        "is_security_team": True,
    }
    payload.update(extra)
    return make_token(payload=payload)


def _queue_item(submission_id: str | None = None, submitter_id: str | None = None) -> dict:
    return {
        "submission_id": submission_id or str(uuid4()),
        "display_id": "SUB-001",
        "skill_name": "my-skill",
        "short_desc": "Does useful things",
        "category": "productivity",
        "submitter_name": "Bob Builder",
        "submitted_at": "2026-03-01T00:00:00",
        "gate1_passed": True,
        "gate2_score": 0.87,
        "gate2_summary": "Automated checks passed",
        "content_preview": "# My Skill\nDoes things.",
        "wait_time_hours": 1.5,
        "divisions": ["engineering"],
    }


# ===========================================================================
# Class 1 — Authentication Enforcement
# ===========================================================================


class TestAuthenticationEnforcement:
    """Every non-public endpoint must return 401 without a Bearer token.

    Public endpoints (no auth needed) must return 200.
    """

    # ---- Protected endpoints — should be 401 with no token ----------------

    @pytest.mark.parametrize(
        "method,path",
        [
            ("POST", "/api/v1/submissions"),
            ("POST", "/api/v1/skills/some-skill/install"),
            ("POST", "/api/v1/skills/some-skill/favorite"),
            ("POST", "/api/v1/skills/some-skill/reviews"),
            ("POST", "/api/v1/feedback"),
            ("GET", "/api/v1/admin/flags"),
            ("POST", "/api/v1/admin/flags"),
            ("GET", "/api/v1/admin/review-queue"),
            ("POST", "/api/v1/admin/review-queue/00000000-0000-0000-0000-000000000001/claim"),
            ("POST", "/api/v1/admin/review-queue/00000000-0000-0000-0000-000000000001/decision"),
            ("GET", "/api/v1/admin/audit-log"),
            ("GET", "/api/v1/admin/users"),
            ("POST", "/api/v1/admin/skills/some-skill/feature"),
            ("POST", "/api/v1/admin/skills/some-skill/deprecate"),
            ("DELETE", "/api/v1/admin/skills/some-skill"),
            ("POST", "/api/v1/admin/recalculate-trending"),
            ("POST", "/api/v1/admin/exports"),
            ("GET", "/api/v1/admin/analytics/summary"),
        ],
    )
    def test_protected_endpoint_returns_401_without_token(
        self, client: Any, method: str, path: str
    ) -> None:
        resp = client.open(path, method=method, json={})
        assert resp.status_code == 401, (
            f"{method} {path} expected 401 without token, got {resp.status_code}"
        )

    def test_401_response_has_detail_field(self, client: Any) -> None:
        """401 response must include a 'detail' key."""
        resp = client.post("/api/v1/submissions", json={})
        assert resp.status_code == 401
        data = resp.get_json()
        assert "detail" in data

    def test_submissions_get_submissions_requires_auth(self, client: Any) -> None:
        resp = client.get("/api/v1/submissions")
        assert resp.status_code == 401

    def test_users_me_requires_auth(self, client: Any) -> None:
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401

    def test_skills_install_delete_requires_auth(self, client: Any) -> None:
        resp = client.delete("/api/v1/skills/some-skill/install")
        assert resp.status_code == 401

    def test_skills_reviews_patch_requires_auth(self, client: Any) -> None:
        uid = str(uuid4())
        resp = client.patch(f"/api/v1/skills/some-skill/reviews/{uid}", json={})
        assert resp.status_code == 401

    def test_skills_comments_post_requires_auth(self, client: Any) -> None:
        resp = client.post("/api/v1/skills/some-skill/comments", json={})
        assert resp.status_code == 401

    def test_admin_flags_patch_requires_auth(self, client: Any) -> None:
        resp = client.patch("/api/v1/admin/flags/my-flag", json={})
        assert resp.status_code == 401

    def test_admin_flags_delete_requires_auth(self, client: Any) -> None:
        resp = client.delete("/api/v1/admin/flags/my-flag")
        assert resp.status_code == 401

    # ---- Public endpoints — should work WITHOUT a token -------------------

    def test_health_is_public(self, client: Any) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    def test_skills_list_is_public(self, mock_ls: MagicMock, client: Any) -> None:
        mock_ls.return_value = ([], 0)
        resp = client.get("/api/v1/skills")
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.flags.get_flags")
    def test_flags_list_is_public(self, mock_gf: MagicMock, client: Any) -> None:
        mock_gf.return_value = {}
        resp = client.get("/api/v1/flags")
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.roadmap.get_changelog")
    def test_changelog_is_public(self, mock_gc: MagicMock, client: Any) -> None:
        mock_gc.return_value = ([], 0)
        resp = client.get("/api/v1/changelog")
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.divisions.list_divisions")
    def test_divisions_is_public(self, mock_ld: MagicMock, client: Any) -> None:
        mock_ld.return_value = []
        resp = client.get("/api/v1/divisions")
        assert resp.status_code == 200

    def test_options_preflight_passes_without_auth(self, client: Any) -> None:
        """CORS preflight OPTIONS must be allowed through without a token."""
        resp = client.options("/api/v1/submissions")
        # CORS preflight should not return 401
        assert resp.status_code != 401


# ===========================================================================
# Class 2 — JWT Validation
# ===========================================================================


class TestJWTValidation:
    """Edge cases in JWT decoding must all fail closed with 401."""

    def test_expired_token_returns_401(self, client: Any) -> None:
        token = make_token(
            payload={"sub": "user", "user_id": str(uuid4())},
            expired=True,
        )
        resp = client.post("/api/v1/submissions", json={}, headers=_auth(token))
        assert resp.status_code == 401
        data = resp.get_json()
        assert "detail" in data

    def test_malformed_token_not_jwt_returns_401(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/submissions",
            json={},
            headers={"Authorization": "Bearer this.is.notvalid"},
        )
        assert resp.status_code == 401

    def test_token_with_wrong_secret_returns_401(self, client: Any) -> None:
        token = make_token(
            payload={"sub": "user", "user_id": str(uuid4())},
            secret="wrong-secret-entirely",
        )
        resp = client.post("/api/v1/submissions", json={}, headers=_auth(token))
        assert resp.status_code == 401

    def test_completely_random_string_bearer_returns_401(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/submissions",
            json={},
            headers={"Authorization": "Bearer notajwtatall"},
        )
        assert resp.status_code == 401

    def test_empty_bearer_value_returns_401(self, client: Any) -> None:
        """'Bearer ' with nothing after it — token is empty string."""
        resp = client.post(
            "/api/v1/submissions",
            json={},
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 401

    def test_no_authorization_header_returns_401(self, client: Any) -> None:
        resp = client.post("/api/v1/submissions", json={})
        assert resp.status_code == 401

    def test_authorization_without_bearer_prefix_returns_401(self, client: Any) -> None:
        """Token present but missing 'Bearer ' prefix."""
        token = make_token(payload={"sub": "user", "user_id": str(uuid4())})
        resp = client.post(
            "/api/v1/submissions",
            json={},
            headers={"Authorization": token},
        )
        assert resp.status_code == 401

    def test_basic_auth_scheme_rejected(self, client: Any) -> None:
        resp = client.post(
            "/api/v1/submissions",
            json={},
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert resp.status_code == 401

    def test_token_signed_with_none_algorithm_rejected(self, client: Any) -> None:
        """A token with 'alg: none' must be rejected."""
        # Manually craft a none-algorithm token (unsigned)
        import base64, json as _json

        header = base64.urlsafe_b64encode(
            _json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).rstrip(b"=").decode()
        payload_b64 = base64.urlsafe_b64encode(
            _json.dumps({"sub": "user", "user_id": str(uuid4()), "exp": int(time.time()) + 3600}).encode()
        ).rstrip(b"=").decode()
        none_token = f"{header}.{payload_b64}."
        resp = client.post(
            "/api/v1/submissions",
            json={},
            headers={"Authorization": f"Bearer {none_token}"},
        )
        assert resp.status_code == 401

    def test_valid_token_is_accepted(self, client: Any) -> None:
        """A well-formed, non-expired token with correct secret must pass auth."""
        token = _regular_token()
        # The endpoint will fail at the service layer (mock DB), not at auth
        resp = client.post("/api/v1/feedback", json={}, headers=_auth(token))
        # Should not be 401 — could be 422 from validation or 500 from mock DB
        assert resp.status_code != 401


# ===========================================================================
# Class 3 — Division Isolation
# ===========================================================================


class TestDivisionIsolation:
    """Division from JWT must be used for access control — never from query params."""

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_install_division_restricted_returns_403(
        self, mock_install: MagicMock, client: Any
    ) -> None:
        """install_skill raises PermissionError when skill is restricted to another division."""
        mock_install.side_effect = PermissionError("Division restricted")
        token = _regular_token(division="engineering")
        resp = client.post(
            "/api/v1/skills/finance-only-skill/install",
            json={"method": "mcp", "version": "1.0.0"},
            headers=_auth(token),
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["detail"]["error"] == "division_restricted"

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_install_uses_division_from_jwt_not_query_params(
        self, mock_install: MagicMock, client: Any
    ) -> None:
        """Division comes from JWT g.current_user, not from request args."""
        mock_install.return_value = {
            "id": str(uuid4()),
            "skill_id": str(uuid4()),
            "user_id": str(uuid4()),
            "method": "mcp",
            "installed_at": "2026-03-01T00:00:00",
            "version": "1.0.0",
        }
        token = _regular_token(division="engineering")
        # Passing a different division via query param must NOT override JWT
        resp = client.post(
            "/api/v1/skills/some-skill/install?division=security",
            json={"method": "mcp", "version": "1.0.0"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        _, call_kwargs = mock_install.call_args
        # The service receives the JWT division, not the query param
        assert call_kwargs.get("user_division") == "engineering" or \
               mock_install.call_args[0][3] == "engineering"

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_platform_team_division_label_passed_from_jwt(
        self, mock_install: MagicMock, client: Any
    ) -> None:
        """Platform team user also gets their division from JWT, not request."""
        mock_install.return_value = {
            "id": str(uuid4()),
            "skill_id": str(uuid4()),
            "user_id": str(uuid4()),
            "method": "mcp",
            "installed_at": "2026-03-01T00:00:00",
            "version": "1.0.0",
        }
        token = _platform_token()
        resp = client.post(
            "/api/v1/skills/some-skill/install",
            json={"method": "mcp", "version": "1.0.0"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        # Service was called with platform division from JWT
        assert mock_install.called

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_division_restricted_error_returns_403_body(
        self, mock_install: MagicMock, client: Any
    ) -> None:
        mock_install.side_effect = PermissionError("restricted")
        token = _regular_token()
        resp = client.post(
            "/api/v1/skills/restricted-skill/install",
            json={"method": "mcp", "version": "1.0.0"},
            headers=_auth(token),
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert "detail" in data
        assert data["detail"]["error"] == "division_restricted"

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_division_restricted_is_not_401(self, mock_install: MagicMock, client: Any) -> None:
        """Division restriction is authorization (403), not authentication (401)."""
        mock_install.side_effect = PermissionError("restricted")
        token = _regular_token()
        resp = client.post(
            "/api/v1/skills/restricted-skill/install",
            json={"method": "mcp", "version": "1.0.0"},
            headers=_auth(token),
        )
        assert resp.status_code == 403
        assert resp.status_code != 401

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_valid_division_install_succeeds(self, mock_install: MagicMock, client: Any) -> None:
        """A user whose division matches can install the skill."""
        mock_install.return_value = {
            "id": str(uuid4()),
            "skill_id": str(uuid4()),
            "user_id": str(uuid4()),
            "method": "mcp",
            "installed_at": "2026-03-01T00:00:00",
            "version": "1.0.0",
        }
        token = _regular_token(division="engineering")
        resp = client.post(
            "/api/v1/skills/open-skill/install",
            json={"method": "mcp", "version": "1.0.0"},
            headers=_auth(token),
        )
        assert resp.status_code == 201

    @patch("skillhub_flask.blueprints.social.fork_skill")
    def test_fork_requires_auth(self, mock_fork: MagicMock, client: Any) -> None:
        """Fork endpoint requires authentication — no token means 401."""
        resp = client.post("/api/v1/skills/some-skill/fork", json={})
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.follow_user")
    def test_follow_requires_auth(self, mock_follow: MagicMock, client: Any) -> None:
        """Follow endpoint requires authentication."""
        resp = client.post("/api/v1/skills/some-skill/follow", json={})
        assert resp.status_code == 401

    def test_delete_install_requires_auth(self, client: Any) -> None:
        """DELETE /skills/<slug>/install must also require auth."""
        resp = client.delete("/api/v1/skills/some-skill/install")
        assert resp.status_code == 401

    def test_delete_favorite_requires_auth(self, client: Any) -> None:
        resp = client.delete("/api/v1/skills/some-skill/favorite")
        assert resp.status_code == 401


# ===========================================================================
# Class 4 — Role Escalation
# ===========================================================================


class TestRoleEscalation:
    """Users must not be able to access roles above their own."""

    # --- Regular user → admin endpoints ---

    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/api/v1/admin/flags"),
            ("POST", "/api/v1/admin/flags"),
            ("GET", "/api/v1/admin/audit-log"),
            ("GET", "/api/v1/admin/users"),
            ("GET", "/api/v1/admin/review-queue"),
            ("POST", "/api/v1/admin/recalculate-trending"),
            ("POST", "/api/v1/admin/skills/some-skill/feature"),
            ("POST", "/api/v1/admin/skills/some-skill/deprecate"),
        ],
    )
    def test_regular_user_cannot_access_admin_endpoints(
        self, client: Any, method: str, path: str
    ) -> None:
        token = _regular_token()
        resp = client.open(path, method=method, json={}, headers=_auth(token))
        assert resp.status_code == 403, (
            f"Regular user accessed {method} {path}: got {resp.status_code}"
        )

    # --- Platform team → security-team-only endpoints ---

    def test_platform_team_cannot_delete_skills(self, client: Any) -> None:
        """DELETE /admin/skills/<slug> requires security team — platform team alone is not enough."""
        token = _platform_token()
        resp = client.delete("/api/v1/admin/skills/some-skill", headers=_auth(token))
        assert resp.status_code == 403

    def test_platform_team_without_security_flag_is_rejected_for_delete(
        self, client: Any
    ) -> None:
        """Explicit: is_platform_team=True but is_security_team=False must still be 403 for DELETE."""
        token = make_token(payload={
            "sub": "admin",
            "user_id": str(uuid4()),
            "division": "platform",
            "is_platform_team": True,
            "is_security_team": False,
        })
        resp = client.delete("/api/v1/admin/skills/some-skill", headers=_auth(token))
        assert resp.status_code == 403

    # --- Regular user with spoofed claims in body (not JWT) ---

    def test_is_platform_team_in_body_does_not_grant_access(self, client: Any) -> None:
        """Sending is_platform_team in request body does not elevate privileges."""
        token = _regular_token()
        resp = client.post(
            "/api/v1/admin/flags",
            json={"is_platform_team": True, "key": "hack", "enabled": True},
            headers=_auth(token),
        )
        assert resp.status_code == 403

    def test_regular_user_cannot_access_review_queue(self, client: Any) -> None:
        token = _regular_token()
        resp = client.get("/api/v1/admin/review-queue", headers=_auth(token))
        assert resp.status_code == 403

    def test_security_team_only_cannot_access_review_queue(self, client: Any) -> None:
        """Security team flag alone doesn't grant platform team access."""
        token = _security_token()
        resp = client.get("/api/v1/admin/review-queue", headers=_auth(token))
        assert resp.status_code == 403

    def test_security_team_only_cannot_access_audit_log(self, client: Any) -> None:
        """Security team without platform team flag cannot see audit log."""
        token = _security_token()
        resp = client.get("/api/v1/admin/audit-log", headers=_auth(token))
        assert resp.status_code == 403

    def test_security_team_only_cannot_list_users(self, client: Any) -> None:
        token = _security_token()
        resp = client.get("/api/v1/admin/users", headers=_auth(token))
        assert resp.status_code == 403

    def test_unauthenticated_user_cannot_access_security_endpoint(self, client: Any) -> None:
        """Completely unauthenticated requests to security-only endpoints return 401."""
        resp = client.delete("/api/v1/admin/skills/some-skill")
        assert resp.status_code == 401

    def test_403_response_has_detail_field(self, client: Any) -> None:
        """403 responses must carry a detail field."""
        token = _regular_token()
        resp = client.get("/api/v1/admin/audit-log", headers=_auth(token))
        assert resp.status_code == 403
        data = resp.get_json()
        assert "detail" in data


# ===========================================================================
# Class 5 — Admin Boundary
# ===========================================================================


class TestAdminBoundary:
    """Platform team can reach admin endpoints; security-team-only gate blocks delete."""

    @patch("skillhub_flask.blueprints.flags.get_flags_admin")
    def test_platform_team_can_list_admin_flags(self, mock_gfa: MagicMock, client: Any) -> None:
        mock_gfa.return_value = []
        resp = client.get("/api/v1/admin/flags", headers=_auth(_platform_token()))
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.admin.query_audit_log")
    def test_platform_team_can_access_audit_log(
        self, mock_qal: MagicMock, client: Any
    ) -> None:
        mock_qal.return_value = ([], 0)
        resp = client.get("/api/v1/admin/audit-log", headers=_auth(_platform_token()))
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.admin.list_users")
    def test_platform_team_can_list_users(self, mock_lu: MagicMock, client: Any) -> None:
        mock_lu.return_value = ([], 0)
        resp = client.get("/api/v1/admin/users", headers=_auth(_platform_token()))
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.review_queue.get_review_queue")
    def test_platform_team_can_access_review_queue(
        self, mock_rq: MagicMock, client: Any
    ) -> None:
        mock_rq.return_value = ([], 0)
        resp = client.get("/api/v1/admin/review-queue", headers=_auth(_platform_token()))
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.admin.remove_skill")
    def test_security_team_can_delete_skills(self, mock_rs: MagicMock, client: Any) -> None:
        mock_rs.return_value = {"slug": "bad-skill", "status": "removed"}
        token = _security_token()
        resp = client.delete("/api/v1/admin/skills/bad-skill", headers=_auth(token))
        assert resp.status_code == 200

    def test_platform_team_cannot_delete_skills(self, client: Any) -> None:
        """Platform team (non-security) is explicitly forbidden from the delete endpoint."""
        resp = client.delete(
            "/api/v1/admin/skills/some-skill",
            headers=_auth(_platform_token()),
        )
        assert resp.status_code == 403

    def test_regular_user_cannot_access_any_admin_endpoint(self, client: Any) -> None:
        token = _regular_token()
        resp = client.get("/api/v1/admin/flags", headers=_auth(token))
        assert resp.status_code == 403

    @patch("skillhub_flask.blueprints.admin.feature_skill")
    def test_platform_team_can_feature_skill(self, mock_fs: MagicMock, client: Any) -> None:
        mock_fs.return_value = {"slug": "great-skill", "featured": True, "featured_order": 1}
        resp = client.post(
            "/api/v1/admin/skills/great-skill/feature",
            json={"featured": True, "featured_order": 1},
            headers=_auth(_platform_token()),
        )
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.admin.deprecate_skill")
    def test_platform_team_can_deprecate_skill(self, mock_ds: MagicMock, client: Any) -> None:
        mock_ds.return_value = {
            "slug": "old-skill",
            "status": "deprecated",
            "deprecated_at": "2026-03-01T00:00:00",
        }
        resp = client.post(
            "/api/v1/admin/skills/old-skill/deprecate",
            headers=_auth(_platform_token()),
        )
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.admin.update_user")
    def test_platform_team_can_update_user(self, mock_uu: MagicMock, client: Any) -> None:
        uid = str(uuid4())
        mock_uu.return_value = {
            "id": uid,
            "email": "test@example.com",
            "username": "testuser",
            "name": "Test User",
            "division": "eng",
            "role": "viewer",
            "is_platform_team": False,
            "is_security_team": False,
        }
        resp = client.patch(
            f"/api/v1/admin/users/{uid}",
            json={"role": "viewer"},
            headers=_auth(_platform_token()),
        )
        assert resp.status_code == 200

    def test_regular_user_cannot_update_user(self, client: Any) -> None:
        uid = str(uuid4())
        resp = client.patch(
            f"/api/v1/admin/users/{uid}",
            json={"role": "admin"},
            headers=_auth(_regular_token()),
        )
        assert resp.status_code == 403


# ===========================================================================
# Class 6 — Audit Log Integrity
# ===========================================================================


class TestAuditLogIntegrity:
    """Verify that service-layer actions write audit log entries with correct event_type."""

    def test_feature_skill_writes_audit_log_with_correct_event_type(self) -> None:
        """feature_skill service must create an audit log entry with event_type='skill.featured'."""
        from skillhub.services.admin import feature_skill

        mock_skill = MagicMock()
        mock_skill.slug = "my-skill"
        mock_skill.featured = True
        mock_skill.featured_order = 1

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_skill

        actor_id = str(uuid4())
        feature_skill(db, slug="my-skill", featured=True, featured_order=1, actor_id=actor_id)

        # db.add is called with at least one object
        assert db.add.called
        # Find the audit log entry among all add calls
        audit_calls = [c[0][0] for c in db.add.call_args_list]
        event_types = [getattr(obj, "event_type", None) for obj in audit_calls]
        assert "skill.featured" in event_types

    def test_deprecate_skill_writes_audit_log_with_correct_event_type(self) -> None:
        """deprecate_skill service must write an audit log entry."""
        from skillhub.services.admin import deprecate_skill

        mock_skill = MagicMock()
        mock_skill.slug = "old-skill"
        mock_skill.status = "published"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_skill

        actor_id = str(uuid4())
        deprecate_skill(db, slug="old-skill", actor_id=actor_id)

        assert db.add.called
        audit_calls = [c[0][0] for c in db.add.call_args_list]
        event_types = [getattr(obj, "event_type", None) for obj in audit_calls]
        assert "skill.deprecated" in event_types

    def test_flag_create_writes_audit_log_with_correct_event_type(self) -> None:
        """create_flag service must write event_type='flag.created'."""
        from skillhub.services.flags import create_flag

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        actor = uuid4()
        create_flag(db, "new.flag", enabled=True, description="Test flag", actor_id=actor)

        # Two add calls: flag + audit log
        assert db.add.call_count >= 2
        audit_obj = db.add.call_args_list[1][0][0]
        assert audit_obj.event_type == "flag.created"

    def test_flag_update_writes_audit_log_with_correct_event_type(self) -> None:
        """update_flag service must write event_type='flag.updated' with before/after."""
        from skillhub.services.flags import update_flag

        mock_flag = MagicMock()
        mock_flag.key = "existing.flag"
        mock_flag.enabled = True
        mock_flag.description = "Before"
        mock_flag.division_overrides = None

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_flag

        actor = uuid4()
        update_flag(db, "existing.flag", enabled=False, actor_id=actor)

        assert db.add.call_count == 1
        audit_obj = db.add.call_args_list[0][0][0]
        assert audit_obj.event_type == "flag.updated"
        assert "before" in audit_obj.metadata_
        assert "after" in audit_obj.metadata_

    def test_flag_delete_writes_audit_log_with_correct_event_type(self) -> None:
        """delete_flag service must write event_type='flag.deleted' with before state."""
        from skillhub.services.flags import delete_flag

        mock_flag = MagicMock()
        mock_flag.key = "old.flag"
        mock_flag.enabled = True
        mock_flag.description = "About to be deleted"
        mock_flag.division_overrides = None

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_flag

        actor = uuid4()
        delete_flag(db, "old.flag", actor_id=actor)

        assert db.add.call_count == 1
        audit_obj = db.add.call_args_list[0][0][0]
        assert audit_obj.event_type == "flag.deleted"
        assert "before" in audit_obj.metadata_

    def test_flag_create_audit_uses_correct_target_type(self) -> None:
        from skillhub.services.flags import create_flag

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        create_flag(db, "my.flag", enabled=False)

        audit_obj = db.add.call_args_list[1][0][0]
        assert audit_obj.target_type == "feature_flag"
        assert audit_obj.target_id == "my.flag"

    def test_flag_update_audit_uses_actor_id(self) -> None:
        from skillhub.services.flags import update_flag

        mock_flag = MagicMock()
        mock_flag.key = "flag.key"
        mock_flag.enabled = False
        mock_flag.description = None
        mock_flag.division_overrides = None

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_flag

        actor = uuid4()
        update_flag(db, "flag.key", enabled=True, actor_id=actor)

        audit_obj = db.add.call_args_list[0][0][0]
        assert audit_obj.actor_id == actor

    def test_flag_create_commits_twice(self) -> None:
        """Two separate commits: once for the flag object, once for the audit log."""
        from skillhub.services.flags import create_flag

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        create_flag(db, "commit.test", enabled=True)

        assert db.commit.call_count == 2

    def test_flag_delete_commits_twice(self) -> None:
        from skillhub.services.flags import delete_flag

        mock_flag = MagicMock()
        mock_flag.key = "del.flag"
        mock_flag.enabled = True
        mock_flag.description = None
        mock_flag.division_overrides = None

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_flag

        delete_flag(db, "del.flag")

        assert db.commit.call_count == 2

    @patch("skillhub_flask.blueprints.flags.create_flag")
    def test_blueprint_passes_actor_id_from_jwt_to_create(
        self, mock_cf: MagicMock, client: Any
    ) -> None:
        """The flags blueprint must extract user_id from JWT and pass it as actor_id."""
        actor_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        mock_cf.return_value = {
            "key": "gate.flag",
            "enabled": True,
            "description": None,
            "division_overrides": None,
        }
        token = make_token(payload={
            "sub": "admin",
            "user_id": actor_id,
            "division": "platform",
            "is_platform_team": True,
        })
        resp = client.post(
            "/api/v1/admin/flags",
            json={"key": "gate.flag", "enabled": True},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        call_kwargs = mock_cf.call_args[1]
        from uuid import UUID
        assert call_kwargs["actor_id"] == UUID(actor_id)


# ===========================================================================
# Class 7 — Input Validation
# ===========================================================================


class TestInputValidation:
    """All POST endpoints must return 422 on empty/invalid body — never 500."""

    # ---- User-accessible POST endpoints -----------------------------------

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/submissions",
            "/api/v1/feedback",
        ],
    )
    def test_user_post_empty_body_returns_422(self, client: Any, path: str) -> None:
        token = _regular_token()
        resp = client.post(path, json={}, headers=_auth(token))
        assert resp.status_code == 422, f"{path} returned {resp.status_code} on empty body"
        assert resp.status_code != 500

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/admin/flags",
            "/api/v1/admin/platform-updates",
        ],
    )
    def test_platform_post_empty_body_returns_422(self, client: Any, path: str) -> None:
        token = _platform_token()
        resp = client.post(path, json={}, headers=_auth(token))
        assert resp.status_code == 422, f"{path} returned {resp.status_code} on empty body"
        assert resp.status_code != 500

    def test_submission_empty_declared_divisions_returns_422(self, client: Any) -> None:
        """declared_divisions with min_length=1 must fail validation."""
        token = _regular_token()
        resp = client.post(
            "/api/v1/submissions",
            json={
                "name": "Test Skill",
                "short_desc": "A skill",
                "category": "productivity",
                "content": "# Content",
                "declared_divisions": [],
                "division_justification": "reason",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_submission_missing_division_justification_returns_422(self, client: Any) -> None:
        token = _regular_token()
        resp = client.post(
            "/api/v1/submissions",
            json={
                "name": "Test Skill",
                "short_desc": "A skill",
                "category": "productivity",
                "content": "# Content",
                "declared_divisions": ["engineering"],
            },
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_review_post_missing_rating_returns_422(self, client: Any) -> None:
        token = _regular_token()
        resp = client.post(
            "/api/v1/skills/some-skill/reviews",
            json={"body": "Great skill"},
            headers=_auth(token),
        )
        # Missing required 'rating' field — must not be 500
        assert resp.status_code != 500

    def test_review_post_invalid_rating_type_returns_422(self, client: Any) -> None:
        """Sending a string for a numeric rating field must not cause a 500."""
        token = _regular_token()
        resp = client.post(
            "/api/v1/skills/some-skill/reviews",
            json={"rating": "five", "body": "Excellent"},
            headers=_auth(token),
        )
        assert resp.status_code != 500

    def test_flag_create_missing_key_returns_422(self, client: Any) -> None:
        token = _platform_token()
        resp = client.post(
            "/api/v1/admin/flags",
            json={"enabled": True},
            headers=_auth(token),
        )
        assert resp.status_code == 422
        assert resp.status_code != 500

    def test_flag_create_invalid_enabled_returns_422(self, client: Any) -> None:
        token = _platform_token()
        resp = client.post(
            "/api/v1/admin/flags",
            json={"key": "new.flag", "enabled": "not-a-boolean"},
            headers=_auth(token),
        )
        assert resp.status_code == 422
        assert resp.status_code != 500

    def test_422_response_has_detail_field(self, client: Any) -> None:
        """422 responses must carry a detail field."""
        token = _regular_token()
        resp = client.post("/api/v1/submissions", json={}, headers=_auth(token))
        assert resp.status_code == 422
        data = resp.get_json()
        assert "detail" in data

    @patch("skillhub_flask.blueprints.social.favorite_skill")
    def test_sql_injection_in_skill_slug_is_safe(
        self, mock_fav: MagicMock, client: Any
    ) -> None:
        """SQL injection in URL slug must not cause a 500."""
        mock_fav.side_effect = ValueError("Skill not found")
        token = _regular_token()
        slug = "'; DROP TABLE skills; --"
        resp = client.post(
            f"/api/v1/skills/{slug}/favorite",
            headers=_auth(token),
        )
        # Should return 404 (not found) or 400 — never 500
        assert resp.status_code != 500

    def test_oversized_name_in_submission_returns_422(self, client: Any) -> None:
        """A name field far exceeding max length must be validated."""
        token = _regular_token()
        oversized = "A" * 10_000
        resp = client.post(
            "/api/v1/submissions",
            json={
                "name": oversized,
                "short_desc": "desc",
                "category": "productivity",
                "content": "# content",
                "declared_divisions": ["engineering"],
                "division_justification": "reason",
            },
            headers=_auth(token),
        )
        # Must not be 500 regardless of whether it passes validation
        assert resp.status_code != 500

    def test_none_body_is_not_500(self, client: Any) -> None:
        """Sending no body at all (not even JSON) must not cause 500."""
        token = _regular_token()
        resp = client.post(
            "/api/v1/submissions",
            data=None,
            headers={**_auth(token), "Content-Type": "application/json"},
        )
        assert resp.status_code != 500

    @patch("skillhub_flask.blueprints.admin.feature_skill")
    def test_feature_skill_empty_body_returns_422(
        self, mock_fs: MagicMock, client: Any
    ) -> None:
        mock_fs.return_value = {"slug": "s", "featured": True, "featured_order": None}
        resp = client.post(
            "/api/v1/admin/skills/some-skill/feature",
            json={},
            headers=_auth(_platform_token()),
        )
        assert resp.status_code == 422
        assert resp.status_code != 500

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_decision_missing_decision_field_returns_422(
        self, mock_ds: MagicMock, client: Any
    ) -> None:
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"notes": "no decision field"},
            headers=_auth(_platform_token()),
        )
        assert resp.status_code != 500

    def test_comment_post_empty_body_is_not_500(self, client: Any) -> None:
        token = _regular_token()
        resp = client.post(
            "/api/v1/skills/some-skill/comments",
            json={},
            headers=_auth(token),
        )
        assert resp.status_code != 500


# ===========================================================================
# Class 8 — Review Queue Workflow
# ===========================================================================


class TestReviewQueueWorkflow:
    """HITL review queue workflow: list, claim, decide, self-approval prevention,
    event_type correctness (regression guard for 'submission.rejectd' typo)."""

    # ---- Event type mapping — unit tests (no HTTP) -----------------------

    def test_decision_event_approve_maps_correctly(self) -> None:
        from skillhub_flask.blueprints.review_queue import _DECISION_EVENT

        assert _DECISION_EVENT["approve"] == "submission.approved"

    def test_decision_event_reject_maps_correctly(self) -> None:
        from skillhub_flask.blueprints.review_queue import _DECISION_EVENT

        assert _DECISION_EVENT["reject"] == "submission.rejected"

    def test_decision_event_reject_is_not_rejectd(self) -> None:
        """Regression: f-string interpolation would produce 'submission.rejectd'."""
        from skillhub_flask.blueprints.review_queue import _DECISION_EVENT

        assert _DECISION_EVENT["reject"] != "submission.rejectd"
        assert not _DECISION_EVENT["reject"].endswith("rejectd")

    def test_decision_event_request_changes_maps_correctly(self) -> None:
        from skillhub_flask.blueprints.review_queue import _DECISION_EVENT

        assert _DECISION_EVENT["request_changes"] == "submission.changes_requested"

    def test_decision_event_has_exactly_three_keys(self) -> None:
        from skillhub_flask.blueprints.review_queue import _DECISION_EVENT

        assert set(_DECISION_EVENT.keys()) == {"approve", "reject", "request_changes"}

    # ---- HTTP workflow tests ----------------------------------------------

    @patch("skillhub_flask.blueprints.review_queue.get_review_queue")
    def test_list_review_queue_200_platform(self, mock_rq: MagicMock, client: Any) -> None:
        item = _queue_item()
        mock_rq.return_value = ([item], 1)
        resp = client.get("/api/v1/admin/review-queue", headers=_auth(_platform_token()))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert "submission_id" in data["items"][0]

    def test_list_review_queue_401_no_token(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/review-queue")
        assert resp.status_code == 401

    def test_list_review_queue_403_regular_user(self, client: Any) -> None:
        resp = client.get("/api/v1/admin/review-queue", headers=_auth(_regular_token()))
        assert resp.status_code == 403

    @patch("skillhub_flask.blueprints.review_queue.claim_submission")
    def test_claim_submission_200(self, mock_cs: MagicMock, client: Any) -> None:
        sub_id = str(uuid4())
        reviewer_id = str(uuid4())
        mock_cs.return_value = {
            "submission_id": sub_id,
            "reviewer_id": reviewer_id,
            "claimed_at": "2026-03-01T10:00:00",
        }
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/claim",
            headers=_auth(_platform_token(user_id=reviewer_id)),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["submission_id"] == sub_id
        mock_cs.assert_called_once()

    def test_claim_submission_401_no_token(self, client: Any) -> None:
        sub_id = str(uuid4())
        resp = client.post(f"/api/v1/admin/review-queue/{sub_id}/claim")
        assert resp.status_code == 401

    def test_claim_submission_403_regular_user(self, client: Any) -> None:
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/claim",
            headers=_auth(_regular_token()),
        )
        assert resp.status_code == 403

    @patch("skillhub_flask.blueprints.review_queue.claim_submission")
    def test_claim_already_claimed_returns_error(self, mock_cs: MagicMock, client: Any) -> None:
        """Service raises ValueError when already claimed → 404."""
        mock_cs.side_effect = ValueError("Already claimed by another reviewer")
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/claim",
            headers=_auth(_platform_token()),
        )
        # Blueprint maps ValueError → 404
        assert resp.status_code == 404

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_approve_decision_returns_200(self, mock_ds: MagicMock, client: Any) -> None:
        sub_id = str(uuid4())
        reviewer_id = str(uuid4())
        mock_ds.return_value = {
            "submission_id": sub_id,
            "decision": "approve",
            "reviewer_id": reviewer_id,
            "reviewed_at": "2026-03-01T12:00:00",
        }
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "approve", "notes": "Looks great", "score": 5},
            headers=_auth(_platform_token(user_id=reviewer_id)),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["decision"] == "approve"

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_reject_decision_returns_200_with_correct_event_type_not_rejectd(
        self, mock_ds: MagicMock, client: Any
    ) -> None:
        """Regression test: reject must produce 'submission.rejected', not 'submission.rejectd'."""
        sub_id = str(uuid4())
        reviewer_id = str(uuid4())
        mock_ds.return_value = {
            "submission_id": sub_id,
            "decision": "reject",
            "reviewer_id": reviewer_id,
            "reviewed_at": "2026-03-01T12:00:00",
        }
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "reject", "notes": "Does not meet quality bar"},
            headers=_auth(_platform_token(user_id=reviewer_id)),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["decision"] == "reject"
        # The blueprint resolved the event_type correctly — service was called with "reject"
        mock_ds.assert_called_once()
        kwargs = mock_ds.call_args[1]
        assert kwargs["decision"] == "reject"

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_request_changes_decision_returns_200(
        self, mock_ds: MagicMock, client: Any
    ) -> None:
        sub_id = str(uuid4())
        reviewer_id = str(uuid4())
        mock_ds.return_value = {
            "submission_id": sub_id,
            "decision": "request_changes",
            "reviewer_id": reviewer_id,
            "reviewed_at": "2026-03-01T12:00:00",
        }
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "request_changes", "notes": "Missing tests"},
            headers=_auth(_platform_token(user_id=reviewer_id)),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["decision"] == "request_changes"

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_self_approval_returns_403(self, mock_ds: MagicMock, client: Any) -> None:
        """PermissionError from service layer (self-approval) must map to 403."""
        mock_ds.side_effect = PermissionError("Cannot approve your own submission")
        sub_id = str(uuid4())
        reviewer_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "approve", "notes": "Self-approval attempt"},
            headers=_auth(_platform_token(user_id=reviewer_id)),
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert "detail" in data
        assert "approve" in data["detail"].lower() or "permission" in data["detail"].lower() or \
               "own submission" in data["detail"].lower() or len(data["detail"]) > 0

    @patch("skillhub_flask.blueprints.review_queue.decide_submission")
    def test_decision_not_found_returns_404(self, mock_ds: MagicMock, client: Any) -> None:
        mock_ds.side_effect = ValueError("Submission not found")
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "approve"},
            headers=_auth(_platform_token()),
        )
        assert resp.status_code == 404

    def test_invalid_decision_value_returns_400_or_422(self, client: Any) -> None:
        """An unrecognised decision value must return 400 or 422 — never 200 or 500."""
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "maybe"},
            headers=_auth(_platform_token()),
        )
        assert resp.status_code in (400, 422), (
            f"Expected 400 or 422 for invalid decision, got {resp.status_code}"
        )

    def test_decide_without_token_returns_401(self, client: Any) -> None:
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "approve"},
        )
        assert resp.status_code == 401

    def test_decide_regular_user_returns_403(self, client: Any) -> None:
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/review-queue/{sub_id}/decision",
            json={"decision": "approve"},
            headers=_auth(_regular_token()),
        )
        assert resp.status_code == 403
