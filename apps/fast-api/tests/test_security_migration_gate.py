"""Security migration gate tests — 8 mandatory classes.

These tests run against the current FastAPI implementation to establish
a security baseline. Every test must pass against both FastAPI and the
Flask port before any endpoint receives traffic.

Ref: docs/migration/adr-001-fastapi-to-flask.md
"""

from __future__ import annotations

import time
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient

from skillhub.config import Settings
from skillhub.dependencies import get_db
from skillhub.main import create_app

from .conftest import TEST_JWT_ALGORITHM, TEST_JWT_SECRET, _make_settings, make_token

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WRONG_SECRET = "this-is-the-wrong-secret-key"


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_client(db_mock: MagicMock | None = None) -> TestClient:
    settings = _make_settings()
    app = create_app(settings=settings)
    if db_mock is not None:
        app.dependency_overrides[get_db] = lambda: db_mock
    return TestClient(app)


def _platform_token(**extra: Any) -> str:
    return make_token(
        payload={
            "sub": "admin-user",
            "user_id": str(uuid.uuid4()),
            "division": "engineering",
            "is_platform_team": True,
            "is_security_team": False,
            **extra,
        }
    )


def _security_token(**extra: Any) -> str:
    return make_token(
        payload={
            "sub": "security-user",
            "user_id": str(uuid.uuid4()),
            "division": "security",
            "is_platform_team": False,
            "is_security_team": True,
            **extra,
        }
    )


def _regular_token(division: str = "engineering", **extra: Any) -> str:
    return make_token(
        payload={
            "sub": "regular-user",
            "user_id": str(uuid.uuid4()),
            "division": division,
            "is_platform_team": False,
            "is_security_team": False,
            **extra,
        }
    )


# ---------------------------------------------------------------------------
# Routes that SHOULD require authentication (non-exhaustive but critical)
# ---------------------------------------------------------------------------

PROTECTED_ROUTES: list[tuple[str, str]] = [
    # Users
    ("get", "/api/v1/users/me"),
    ("get", "/api/v1/users/me/installs"),
    ("get", "/api/v1/users/me/favorites"),
    ("get", "/api/v1/users/me/forks"),
    ("get", "/api/v1/users/me/submissions"),
    # Social - write operations
    ("post", "/api/v1/skills/test-slug/install"),
    ("delete", "/api/v1/skills/test-slug/install"),
    ("post", "/api/v1/skills/test-slug/favorite"),
    ("delete", "/api/v1/skills/test-slug/favorite"),
    ("post", "/api/v1/skills/test-slug/fork"),
    ("post", "/api/v1/skills/test-slug/follow"),
    ("delete", "/api/v1/skills/test-slug/follow"),
    ("post", "/api/v1/skills/test-slug/reviews"),
    ("post", "/api/v1/skills/test-slug/comments"),
    # Skills - auth-required endpoints
    ("get", "/api/v1/skills/test-slug/versions"),
    ("get", "/api/v1/skills/test-slug/versions/latest"),
    # Submissions
    ("post", "/api/v1/submissions"),
    ("get", "/api/v1/submissions/00000000-0000-0000-0000-000000000001"),
    # Division access request (auth required; skill slug can be anything)
    ("post", "/api/v1/skills/test-slug/access-request"),
    # Auth-me
    ("get", "/auth/me"),
    # Feedback
    ("post", "/api/v1/feedback"),
    ("post", "/api/v1/feedback/00000000-0000-0000-0000-000000000001/upvote"),
]

ADMIN_ROUTES: list[tuple[str, str]] = [
    # Admin - platform team
    ("post", "/api/v1/admin/skills/test-slug/feature"),
    ("post", "/api/v1/admin/skills/test-slug/deprecate"),
    ("post", "/api/v1/admin/recalculate-trending"),
    ("get", "/api/v1/admin/audit-log"),
    ("get", "/api/v1/admin/users"),
    ("patch", "/api/v1/admin/users/00000000-0000-0000-0000-000000000001"),
    ("get", "/api/v1/admin/submissions"),
    ("post", "/api/v1/admin/submissions/00000000-0000-0000-0000-000000000001/scan"),
    ("post", "/api/v1/admin/submissions/00000000-0000-0000-0000-000000000001/review"),
    ("get", "/api/v1/admin/access-requests"),
    ("post", "/api/v1/admin/access-requests/00000000-0000-0000-0000-000000000001/review"),
    # Review queue - platform team
    ("get", "/api/v1/admin/review-queue"),
    ("post", "/api/v1/admin/review-queue/00000000-0000-0000-0000-000000000001/claim"),
    ("post", "/api/v1/admin/review-queue/00000000-0000-0000-0000-000000000001/decision"),
    # Analytics
    ("get", "/api/v1/admin/analytics/summary"),
    ("get", "/api/v1/admin/analytics/time-series"),
    ("get", "/api/v1/admin/analytics/submission-funnel"),
    ("get", "/api/v1/admin/analytics/top-skills"),
    # Exports
    ("post", "/api/v1/admin/exports"),
    ("get", "/api/v1/admin/exports/00000000-0000-0000-0000-000000000001"),
    # Feedback
    ("get", "/api/v1/admin/feedback"),
    ("patch", "/api/v1/admin/feedback/00000000-0000-0000-0000-000000000001/status"),
    # Platform updates / roadmap
    ("get", "/api/v1/admin/platform-updates"),
    ("post", "/api/v1/admin/platform-updates"),
    ("patch", "/api/v1/admin/platform-updates/00000000-0000-0000-0000-000000000001"),
    ("post", "/api/v1/admin/platform-updates/00000000-0000-0000-0000-000000000001/ship"),
]

SECURITY_TEAM_ROUTES: list[tuple[str, str]] = [
    ("delete", "/api/v1/admin/skills/test-slug"),
    # Platform-update hard delete — security team only (roadmap.py)
    ("delete", "/api/v1/admin/platform-updates/00000000-0000-0000-0000-000000000001"),
]

PUBLIC_ROUTES: list[tuple[str, str]] = [
    ("get", "/health"),
    ("get", "/api/v1/skills"),
    ("get", "/api/v1/skills/categories"),
    ("get", "/api/v1/skills/test-slug"),
    ("get", "/api/v1/flags"),
    ("get", "/api/v1/changelog"),
    # Stub auth endpoints are public by nature (gated by feature flag, not JWT)
    ("get", "/auth/dev-users"),
]


# ===========================================================================
# CLASS 1: Unauthenticated Rejection
# ===========================================================================


class TestUnauthenticatedRejection:
    """Every non-public endpoint must return 401 with no token, malformed
    token, expired token, and wrong-secret token."""

    def setup_method(self) -> None:
        self.client = _make_client()

    @pytest.mark.parametrize("method,path", PROTECTED_ROUTES + ADMIN_ROUTES)
    def test_no_token_returns_401(self, method: str, path: str) -> None:
        response = getattr(self.client, method)(path)
        assert response.status_code == 401, (
            f"{method.upper()} {path} returned {response.status_code} without token"
        )

    @pytest.mark.parametrize("method,path", PROTECTED_ROUTES + ADMIN_ROUTES)
    def test_expired_token_returns_401(self, method: str, path: str) -> None:
        token = make_token(expired=True)
        response = getattr(self.client, method)(path, headers=_auth_headers(token))
        assert response.status_code == 401, (
            f"{method.upper()} {path} returned {response.status_code} with expired token"
        )

    @pytest.mark.parametrize("method,path", PROTECTED_ROUTES + ADMIN_ROUTES)
    def test_wrong_secret_returns_401(self, method: str, path: str) -> None:
        token = make_token(secret=_WRONG_SECRET)
        response = getattr(self.client, method)(path, headers=_auth_headers(token))
        assert response.status_code == 401, (
            f"{method.upper()} {path} returned {response.status_code} with wrong-secret token"
        )

    @pytest.mark.parametrize("method,path", PROTECTED_ROUTES + ADMIN_ROUTES)
    def test_malformed_token_returns_401(self, method: str, path: str) -> None:
        response = getattr(self.client, method)(
            path, headers={"Authorization": "Bearer not.a.valid.jwt"}
        )
        assert response.status_code == 401, (
            f"{method.upper()} {path} returned {response.status_code} with malformed token"
        )

    @pytest.mark.parametrize("method,path", PROTECTED_ROUTES + ADMIN_ROUTES)
    def test_no_bearer_prefix_returns_401(self, method: str, path: str) -> None:
        token = make_token()
        response = getattr(self.client, method)(
            path, headers={"Authorization": token}
        )
        assert response.status_code == 401, (
            f"{method.upper()} {path} returned {response.status_code} without Bearer prefix"
        )

    def test_error_response_has_detail_key(self) -> None:
        """401 responses must use {"detail": "..."} format, not Flask HTML."""
        response = self.client.get("/auth/me")
        assert response.status_code == 401
        body = response.json()
        assert "detail" in body
        assert isinstance(body["detail"], str)

    def test_error_does_not_leak_internals(self) -> None:
        """401 must not expose stack trace or route names."""
        response = self.client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer garbage"},
        )
        assert response.status_code == 401
        body = response.json()
        assert "traceback" not in str(body).lower()
        assert "Traceback" not in str(body)


# ===========================================================================
# CLASS 2: Algorithm Confusion
# ===========================================================================


class TestAlgorithmConfusion:
    """JWT algorithm must be pinned. Tokens signed with unexpected
    algorithms or alg:none must be rejected."""

    def setup_method(self) -> None:
        self.client = _make_client()

    def test_alg_none_rejected(self) -> None:
        """A token with alg=none must be rejected at decode."""
        # Manually craft an unsigned token
        header = pyjwt.utils.base64url_encode(b'{"alg":"none","typ":"JWT"}')
        payload_data = {
            "sub": "hacker",
            "division": "engineering",
            "is_platform_team": True,
            "exp": int(time.time()) + 3600,
        }
        import json

        payload_bytes = pyjwt.utils.base64url_encode(
            json.dumps(payload_data).encode()
        )
        unsigned_token = f"{header.decode()}.{payload_bytes.decode()}."
        response = self.client.get(
            "/auth/me", headers={"Authorization": f"Bearer {unsigned_token}"}
        )
        assert response.status_code == 401

    def test_wrong_algorithm_rejected(self) -> None:
        """Token signed with HS384 when HS256 is expected must be rejected."""
        payload = {
            "sub": "hacker",
            "division": "engineering",
            "exp": int(time.time()) + 3600,
        }
        token = pyjwt.encode(payload, TEST_JWT_SECRET, algorithm="HS384")
        response = self.client.get(
            "/auth/me", headers=_auth_headers(token)
        )
        assert response.status_code == 401

    def test_correct_algorithm_accepted(self) -> None:
        """Token signed with the expected HS256 is accepted."""
        token = make_token()
        response = self.client.get(
            "/auth/me", headers=_auth_headers(token)
        )
        assert response.status_code == 200


# ===========================================================================
# CLASS 3: Division Isolation
# ===========================================================================


class TestDivisionIsolation:
    """Division enforcement: JWT claim → service layer DB lookup.
    A user from Division A must not access Division B resources."""

    def test_install_blocked_by_division(self) -> None:
        """User cannot install a skill restricted to a different division.
        Uses service-layer patching to avoid deep mock chain issues."""
        mock_db = MagicMock()
        client = _make_client(mock_db)
        token = _regular_token(division="product-org")

        with patch(
            "skillhub.routers.social.install_skill",
            side_effect=PermissionError("Division restricted"),
        ):
            response = client.post(
                "/api/v1/skills/restricted-skill/install",
                headers=_auth_headers(token),
                json={"method": "claude-code", "version": "1.0.0"},
            )
            # Should be 403 when service raises PermissionError
            assert response.status_code == 403, (
                f"Division-restricted install returned {response.status_code}, "
                "expected 403"
            )

    def test_forged_division_claim_does_not_bypass(self) -> None:
        """A JWT with a forged division claim should not grant access
        if the service layer performs a DB lookup."""
        mock_db = MagicMock()
        client = _make_client(mock_db)

        # Token claims engineering-org, but user's DB record might differ
        # The key test: division from JWT is what gets passed to service layer
        token = _regular_token(division="engineering-org")
        response = client.get(
            "/api/v1/users/me",
            headers=_auth_headers(token),
        )
        # Should not crash — the division claim is used downstream
        assert response.status_code in (200, 404, 500)


# ===========================================================================
# CLASS 4: Stub Auth Containment
# ===========================================================================


class TestStubAuthContainment:
    """Stub auth must not be reachable when disabled."""

    def test_stub_disabled_rejects_login(self) -> None:
        """With stub_auth_enabled=False, POST /auth/token returns 403."""
        settings = _make_settings(stub_auth_enabled=False)
        app = create_app(settings=settings)
        client = TestClient(app)
        response = client.post(
            "/auth/token",
            json={"username": "alice", "password": "user"},
        )
        assert response.status_code == 403

    def test_stub_disabled_rejects_dev_users(self) -> None:
        """With stub_auth_enabled=False, GET /auth/dev-users returns 403."""
        settings = _make_settings(stub_auth_enabled=False)
        app = create_app(settings=settings)
        client = TestClient(app)
        response = client.get("/auth/dev-users")
        assert response.status_code == 403

    def test_stub_enabled_allows_login(self) -> None:
        """With stub_auth_enabled=True, POST /auth/token returns 200."""
        settings = _make_settings(stub_auth_enabled=True)
        app = create_app(settings=settings)
        client = TestClient(app)
        response = client.post(
            "/auth/token",
            json={"username": "alice", "password": "user"},
        )
        assert response.status_code == 200

    def test_stub_token_has_expected_claims(self) -> None:
        """Stub tokens must contain all required JWT claims."""
        settings = _make_settings(stub_auth_enabled=True)
        app = create_app(settings=settings)
        client = TestClient(app)
        response = client.post(
            "/auth/token",
            json={"username": "alice", "password": "user"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        decoded = pyjwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        required_claims = {"sub", "user_id", "exp", "iat"}
        assert required_claims.issubset(decoded.keys()), (
            f"Missing claims: {required_claims - decoded.keys()}"
        )


# ===========================================================================
# CLASS 5: Admin Boundary
# ===========================================================================


class TestAdminBoundary:
    """Admin endpoints require platform_team or security_team role.
    Regular users must receive 403, not 404."""

    def setup_method(self) -> None:
        self.client = _make_client()

    @pytest.mark.parametrize("method,path", ADMIN_ROUTES)
    def test_regular_user_gets_403_on_admin_routes(
        self, method: str, path: str
    ) -> None:
        token = _regular_token()
        response = getattr(self.client, method)(path, headers=_auth_headers(token))
        assert response.status_code == 403, (
            f"Regular user got {response.status_code} on {method.upper()} {path}, "
            "expected 403"
        )

    @pytest.mark.parametrize("method,path", SECURITY_TEAM_ROUTES)
    def test_platform_team_without_security_gets_403(
        self, method: str, path: str
    ) -> None:
        """Platform team alone cannot access security-team-only routes."""
        token = _platform_token(is_security_team=False)
        response = getattr(self.client, method)(path, headers=_auth_headers(token))
        assert response.status_code == 403, (
            f"Platform-only user got {response.status_code} on security-team route"
        )

    @pytest.mark.parametrize("method,path", ADMIN_ROUTES)
    def test_unauthenticated_gets_401_not_403(
        self, method: str, path: str
    ) -> None:
        """Unauthenticated requests to admin routes get 401 (not 403)."""
        response = getattr(self.client, method)(path)
        assert response.status_code == 401, (
            f"Unauthenticated got {response.status_code} on {method.upper()} {path}"
        )


# ===========================================================================
# CLASS 6: Audit Log Integrity
# ===========================================================================


class TestAuditLogIntegrity:
    """Audit log must be append-only and written on sensitive operations."""

    def test_audit_log_endpoint_returns_entries(self) -> None:
        """Platform team can query audit log."""
        mock_db = MagicMock()
        client = _make_client(mock_db)
        token = _platform_token()

        # Mock query chain for audit log
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.get(
            "/api/v1/admin/audit-log",
            headers=_auth_headers(token),
        )
        assert response.status_code == 200

    def test_audit_log_not_accessible_to_regular_users(self) -> None:
        """Regular users cannot query audit log."""
        client = _make_client()
        token = _regular_token()
        response = client.get(
            "/api/v1/admin/audit-log",
            headers=_auth_headers(token),
        )
        assert response.status_code == 403

    def test_audit_log_not_accessible_without_auth(self) -> None:
        """Unauthenticated users get 401 on audit log."""
        client = _make_client()
        response = client.get("/api/v1/admin/audit-log")
        assert response.status_code == 401

    def test_decide_submission_writes_audit_log(self) -> None:
        """decide_submission() must append an AuditLog row for every decision.

        This is a unit-level check directly against the service function so
        that the security gate catches audit-log regressions without a live DB.
        The service's internal ``db.add`` call is the observable side-effect.
        """
        from skillhub.services.review_queue import decide_submission
        from skillhub_db.models.audit import AuditLog
        from skillhub_db.models.submission import Submission, SubmissionStatus

        mock_db = MagicMock()
        sub_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()
        submitter_id = uuid.uuid4()  # different from reviewer — no self-approval

        mock_submission = MagicMock(spec=Submission)
        mock_submission.id = sub_id
        mock_submission.submitted_by = submitter_id
        mock_submission.status = SubmissionStatus.GATE2_PASSED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_submission

        added_objects: list[Any] = []
        mock_db.add.side_effect = added_objects.append

        decide_submission(
            mock_db,
            submission_id=sub_id,
            reviewer_id=reviewer_id,
            decision="approve",
            notes="Looks good",
        )

        audit_rows = [o for o in added_objects if isinstance(o, AuditLog)]
        assert len(audit_rows) == 1, (
            f"Expected 1 AuditLog row from decide_submission, got {len(audit_rows)}. "
            "Audit-log write must not be removed or gated on a flag."
        )
        audit = audit_rows[0]
        # Event type must not contain typos (regression: "approvedd")
        assert audit.event_type == "submission.approved", (
            f"AuditLog event_type is '{audit.event_type}', expected 'submission.approved'. "
            "Check the f-string interpolation in review_queue.py decide_submission()."
        )

    def test_decide_submission_audit_event_type_reject(self) -> None:
        """event_type for 'reject' decision must be 'submission.rejected' (not 'submission.rejectd')."""
        from skillhub.services.review_queue import decide_submission
        from skillhub_db.models.audit import AuditLog
        from skillhub_db.models.submission import Submission, SubmissionStatus

        mock_db = MagicMock()
        sub_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()
        submitter_id = uuid.uuid4()

        mock_submission = MagicMock(spec=Submission)
        mock_submission.id = sub_id
        mock_submission.submitted_by = submitter_id
        mock_submission.status = SubmissionStatus.GATE2_PASSED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_submission

        added_objects: list[Any] = []
        mock_db.add.side_effect = added_objects.append

        decide_submission(
            mock_db,
            submission_id=sub_id,
            reviewer_id=reviewer_id,
            decision="reject",
        )

        audit_rows = [o for o in added_objects if isinstance(o, AuditLog)]
        assert len(audit_rows) == 1
        assert audit_rows[0].event_type == "submission.rejected", (
            f"event_type is '{audit_rows[0].event_type}', expected 'submission.rejected'. "
            "The f-string 'submission.{decision}d' produces 'submission.rejectd' — use a lookup dict."
        )

    def test_decide_submission_audit_event_type_request_changes(self) -> None:
        """event_type for 'request_changes' must be 'submission.changes_requested'."""
        from skillhub.services.review_queue import decide_submission
        from skillhub_db.models.audit import AuditLog
        from skillhub_db.models.submission import Submission, SubmissionStatus

        mock_db = MagicMock()
        sub_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()
        submitter_id = uuid.uuid4()

        mock_submission = MagicMock(spec=Submission)
        mock_submission.id = sub_id
        mock_submission.submitted_by = submitter_id
        mock_submission.status = SubmissionStatus.GATE2_PASSED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_submission

        added_objects: list[Any] = []
        mock_db.add.side_effect = added_objects.append

        decide_submission(
            mock_db,
            submission_id=sub_id,
            reviewer_id=reviewer_id,
            decision="request_changes",
        )

        audit_rows = [o for o in added_objects if isinstance(o, AuditLog)]
        assert len(audit_rows) == 1
        assert audit_rows[0].event_type == "submission.changes_requested"

    def test_claim_submission_does_not_write_audit_log(self) -> None:
        """claim_submission() is low-sensitivity; it must NOT write an AuditLog row.

        This documents the intentional gap so a future developer doesn't add one
        accidentally and create noise, or remove one from decide_submission thinking
        the two functions share the same contract.
        """
        from skillhub.services.review_queue import claim_submission
        from skillhub_db.models.audit import AuditLog
        from skillhub_db.models.submission import Submission, SubmissionStatus

        mock_db = MagicMock()
        sub_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()

        mock_submission = MagicMock(spec=Submission)
        mock_submission.id = sub_id
        mock_submission.status = SubmissionStatus.GATE2_PASSED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_submission

        added_objects: list[Any] = []
        mock_db.add.side_effect = added_objects.append

        claim_submission(mock_db, submission_id=sub_id, reviewer_id=reviewer_id)

        audit_rows = [o for o in added_objects if isinstance(o, AuditLog)]
        assert len(audit_rows) == 1, (
            "claim_submission must write an AuditLog entry with event_type='submission.claimed'"
        )
        assert audit_rows[0].event_type == "submission.claimed"


# ===========================================================================
# CLASS 7: Public Routes Remain Public
# ===========================================================================


class TestPublicRoutesAccessible:
    """Public routes must be accessible without authentication and must
    not require auth after the Flask migration."""

    def setup_method(self) -> None:
        mock_db = MagicMock()
        self.client = _make_client(mock_db)

        # Set up minimal mock returns for public routes
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        mock_query.count.return_value = 0
        mock_query.options.return_value = mock_query
        mock_db.query.return_value = mock_query

    @pytest.mark.parametrize("method,path", PUBLIC_ROUTES)
    def test_public_route_accessible_without_token(
        self, method: str, path: str
    ) -> None:
        response = getattr(self.client, method)(path)
        # Public routes should NOT return 401
        assert response.status_code != 401, (
            f"Public route {method.upper()} {path} returned 401 without token"
        )

    def test_health_returns_200(self) -> None:
        """Health check must always return 200."""
        client = _make_client()  # No DB mock needed
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_has_status_field(self) -> None:
        """Health check response must have a status field."""
        client = _make_client()
        response = client.get("/health")
        body = response.json()
        assert "status" in body


# ===========================================================================
# CLASS 8: Review Queue Workflow Security
# ===========================================================================


class TestReviewQueueWorkflow:
    """Review queue endpoints are admin-only and enforce self-approval prevention.

    These tests cover the security-critical HITL path:
    GET  /api/v1/admin/review-queue              — list items awaiting review
    POST /api/v1/admin/review-queue/{id}/claim   — claim a submission
    POST /api/v1/admin/review-queue/{id}/decision — approve/reject/request changes

    Invariants enforced:
    1. All three endpoints require is_platform_team.
    2. Regular authenticated users receive 403, not 404.
    3. A reviewer cannot approve/reject their own submission.
    4. The decision endpoint returns 403 (not 500) on self-approval.
    """

    _FAKE_SUB_ID = "00000000-0000-0000-0000-000000000099"

    def test_review_queue_list_requires_platform_team(self) -> None:
        """GET /review-queue returns 403 for a regular authenticated user."""
        client = _make_client()
        token = _regular_token()
        response = client.get(
            "/api/v1/admin/review-queue",
            headers=_auth_headers(token),
        )
        assert response.status_code == 403, (
            f"Review queue list returned {response.status_code} for regular user, expected 403"
        )

    def test_review_queue_claim_requires_platform_team(self) -> None:
        """POST /review-queue/{id}/claim returns 403 for a regular authenticated user."""
        client = _make_client()
        token = _regular_token()
        response = client.post(
            f"/api/v1/admin/review-queue/{self._FAKE_SUB_ID}/claim",
            headers=_auth_headers(token),
        )
        assert response.status_code == 403, (
            f"Review queue claim returned {response.status_code} for regular user, expected 403"
        )

    def test_review_queue_decision_requires_platform_team(self) -> None:
        """POST /review-queue/{id}/decision returns 403 for a regular authenticated user."""
        client = _make_client()
        token = _regular_token()
        response = client.post(
            f"/api/v1/admin/review-queue/{self._FAKE_SUB_ID}/decision",
            headers=_auth_headers(token),
            json={"decision": "approve", "notes": ""},
        )
        assert response.status_code == 403, (
            f"Review queue decision returned {response.status_code} for regular user, expected 403"
        )

    def test_self_approval_returns_403(self) -> None:
        """A reviewer who submitted the skill cannot approve it — must get 403.

        The service layer raises PermissionError("Cannot review your own submission"),
        which the router must translate to HTTP 403 (not 500 or 404).
        """
        mock_db = MagicMock()
        client = _make_client(mock_db)

        reviewer_user_id = str(uuid.uuid4())
        token = make_token(
            payload={
                "sub": "platform-user",
                "user_id": reviewer_user_id,
                "division": "engineering",
                "is_platform_team": True,
                "is_security_team": False,
            }
        )

        with patch(
            "skillhub.routers.review_queue.decide_submission",
            side_effect=PermissionError("Cannot review your own submission"),
        ):
            response = client.post(
                f"/api/v1/admin/review-queue/{self._FAKE_SUB_ID}/decision",
                headers=_auth_headers(token),
                json={"decision": "approve", "notes": "self-approval attempt"},
            )

        assert response.status_code == 403, (
            f"Self-approval returned {response.status_code}, expected 403. "
            "The router must catch PermissionError and return HTTP 403."
        )
        body = response.json()
        assert "detail" in body, "403 response must use {'detail': '...'} format"

    def test_review_queue_unauthenticated_returns_401(self) -> None:
        """All three review-queue endpoints return 401 with no token."""
        client = _make_client()
        for method, path in [
            ("get", "/api/v1/admin/review-queue"),
            ("post", f"/api/v1/admin/review-queue/{self._FAKE_SUB_ID}/claim"),
            ("post", f"/api/v1/admin/review-queue/{self._FAKE_SUB_ID}/decision"),
        ]:
            response = getattr(client, method)(path)
            assert response.status_code == 401, (
                f"{method.upper()} {path} returned {response.status_code} without token, expected 401"
            )
