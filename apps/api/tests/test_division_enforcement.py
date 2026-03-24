"""Tests verifying cross-division data access is blocked server-side.

These tests exercise the division enforcement mechanisms that exist in the
actual implementation. Where a service does NOT check divisions for a
particular operation, that is noted as a gap rather than asserting behavior
that doesn't exist.

Division enforcement is implemented in:
  - install_skill (service) — PermissionError when skill has SkillDivision rows
    and user's division is not among them → 403 "division_restricted"
  - Admin endpoints — require_platform_team decorator → 403 for non-platform users
  - Submission detail (service) — PermissionError if not owner and not platform team

Noted gaps (no server-side enforcement in the service layer):
  - browse_skills / get_skill_detail: no division filtering per caller's JWT
    division; any authenticated user can browse/view skills regardless of
    their division claim (filtering is an optional client-supplied query param)
  - favorite_skill, fork_skill: no division check in service layer
  - create_submission: declared_divisions is caller-supplied metadata; the
    service does not verify the caller belongs to any listed division
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import jwt
import pytest

from tests.conftest import TEST_JWT_ALGORITHM, TEST_JWT_SECRET, make_token

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

SLUG = "test-skill"
SKILL_ID = str(uuid4())
USER_ID = str(uuid4())
FINANCE_USER_ID = str(uuid4())
NOW = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _engineering_token(user_id: str = USER_ID) -> str:
    """Token for a user in the engineering division."""
    return make_token(
        payload={
            "sub": "eng-user",
            "user_id": user_id,
            "division": "engineering",
            "is_platform_team": False,
        }
    )


def _finance_token(user_id: str = FINANCE_USER_ID) -> str:
    """Token for a user in the finance division."""
    return make_token(
        payload={
            "sub": "finance-user",
            "user_id": user_id,
            "division": "finance",
            "is_platform_team": False,
        }
    )


def _platform_token(user_id: str | None = None) -> str:
    """Token for a platform team member."""
    return make_token(
        payload={
            "sub": "platform-user",
            "user_id": user_id or str(uuid4()),
            "division": "platform",
            "is_platform_team": True,
        }
    )


def _no_division_token(user_id: str | None = None) -> str:
    """Token with no division claim."""
    return make_token(
        payload={
            "sub": "nodiv-user",
            "user_id": user_id or str(uuid4()),
            "is_platform_team": False,
        }
    )


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Shared result factories
# ---------------------------------------------------------------------------


def _install_result(user_id: str = USER_ID) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "skill_id": SKILL_ID,
        "user_id": user_id,
        "version": "1.0.0",
        "method": "claude-code",
        "installed_at": NOW,
    }


def _favorite_result(user_id: str = USER_ID) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "skill_id": SKILL_ID,
        "created_at": NOW,
    }


def _fork_result(user_id: str = USER_ID) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "original_skill_id": SKILL_ID,
        "forked_skill_id": str(uuid4()),
        "forked_skill_slug": f"{SLUG}-fork-abcd1234",
        "forked_by": user_id,
    }


def _submission_result() -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "display_id": "SUB-0001",
        "status": "gate1_failed",
        "gate1_result": {"gate": 1, "result": "pass", "findings": [], "score": 100},
    }


def _admin_summary() -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "display_id": "SUB-0001",
        "name": "My Skill",
        "short_desc": "A skill",
        "category": "code-review",
        "status": "gate1_passed",
        "submitted_by": USER_ID,
        "declared_divisions": ["engineering"],
        "created_at": NOW,
    }


def _skill_summary() -> dict[str, Any]:
    return {
        "id": SKILL_ID,
        "slug": SLUG,
        "name": "Test Skill",
        "short_desc": "A skill for testing",
        "category": "productivity",
        "divisions": ["engineering"],
        "tags": [],
        "author": "alice",
        "author_type": "individual",
        "version": "1.0.0",
        "install_method": "claude-code",
        "verified": False,
        "featured": False,
        "install_count": 0,
        "fork_count": 0,
        "favorite_count": 0,
        "avg_rating": None,
        "review_count": 0,
        "days_ago": 1,
        "user_has_installed": None,
        "user_has_favorited": None,
    }


def _skill_detail() -> dict[str, Any]:
    return {
        "id": SKILL_ID,
        "slug": SLUG,
        "name": "Test Skill",
        "short_desc": "A skill for testing",
        "category": "productivity",
        "divisions": ["engineering"],
        "tags": [],
        "author": "alice",
        "author_id": str(uuid4()),
        "author_type": "individual",
        "current_version": "1.0.0",
        "install_method": "claude-code",
        "data_sensitivity": "none",
        "external_calls": False,
        "verified": False,
        "featured": False,
        "status": "published",
        "install_count": 0,
        "fork_count": 0,
        "favorite_count": 0,
        "view_count": 10,
        "review_count": 0,
        "avg_rating": None,
        "trending_score": "0.00",
        "published_at": NOW,
        "deprecated_at": None,
        "user_has_installed": None,
        "user_has_favorited": None,
    }


# ===========================================================================
# Category 1: Install Division Restriction
# ===========================================================================


class TestInstallDivisionRestriction:
    """POST /api/v1/skills/<slug>/install — division enforcement via service layer."""

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_engineering_user_installs_engineering_skill_returns_201(
        self, mock_install: Any, client: Any
    ) -> None:
        """User in engineering can install a skill available to engineering."""
        mock_install.return_value = _install_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["skill_id"] == SKILL_ID

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_finance_user_cannot_install_engineering_skill_returns_403(
        self, mock_install: Any, client: Any
    ) -> None:
        """User in finance is blocked from a skill restricted to engineering."""
        mock_install.side_effect = PermissionError("division_restricted")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["detail"]["error"] == "division_restricted"

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_engineering_user_cannot_install_finance_skill_returns_403(
        self, mock_install: Any, client: Any
    ) -> None:
        """User in engineering is blocked from a skill restricted to finance."""
        mock_install.side_effect = PermissionError("division_restricted")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["detail"]["error"] == "division_restricted"

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_platform_team_user_can_install_cross_division_skill(
        self, mock_install: Any, client: Any
    ) -> None:
        """Platform team user succeeds because service allows it (no division restriction
        for platform team is a business decision; service does not special-case them,
        so this test verifies the 201 path when the service returns success)."""
        mock_install.return_value = _install_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 201

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_install_with_no_division_in_token_forwards_empty_string_to_service(
        self, mock_install: Any, client: Any
    ) -> None:
        """Blueprint extracts division with .get('division', ''), so a token
        without a division claim sends an empty string to the service."""
        mock_install.side_effect = PermissionError("division_restricted")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_no_division_token()),
        )
        assert resp.status_code == 403
        # Confirm service received empty-string division (positional arg index 3)
        call_args = mock_install.call_args
        user_division_arg = call_args.args[3] if len(call_args.args) > 3 else call_args.kwargs.get("user_division", "")
        assert user_division_arg == ""

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_install_skill_with_no_division_rows_succeeds(
        self, mock_install: Any, client: Any
    ) -> None:
        """When a skill has no SkillDivision rows (all-divisions), install succeeds."""
        mock_install.return_value = _install_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 201

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_install_passes_user_division_from_jwt_to_service(
        self, mock_install: Any, client: Any
    ) -> None:
        """Blueprint correctly extracts division from JWT and passes to service."""
        mock_install.return_value = _install_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 201
        call_args = mock_install.call_args
        user_division_arg = call_args.args[3] if len(call_args.args) > 3 else call_args.kwargs.get("user_division", "UNSET")
        assert user_division_arg == "engineering"

    def test_install_without_auth_returns_401(self, client: Any) -> None:
        """Unauthenticated install request is rejected before any division check."""
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
        )
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_install_skill_not_found_returns_404(
        self, mock_install: Any, client: Any
    ) -> None:
        """ValueError from service produces 404, not confused with 403."""
        mock_install.side_effect = ValueError(f"Skill '{SLUG}' not found")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 404
        assert "not found" in resp.get_json()["detail"].lower()

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_division_restricted_error_response_structure(
        self, mock_install: Any, client: Any
    ) -> None:
        """403 response wraps error in {detail: {error: 'division_restricted'}}."""
        mock_install.side_effect = PermissionError("any message")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 403
        body = resp.get_json()
        assert "detail" in body
        assert body["detail"]["error"] == "division_restricted"


# ===========================================================================
# Category 2: Skill Browse/Detail — Division Filtering
# ===========================================================================


class TestSkillBrowseDivisionFiltering:
    """GET /api/v1/skills — browse endpoint division behavior.

    Note: browse_skills does NOT automatically filter by caller's JWT division.
    The 'divisions' query param is the only way to filter by division.
    An authenticated user can browse all published skills regardless of their
    own division. This is by design (discovery is unrestricted; install is gated).
    """

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_authenticated_user_can_browse_all_published_skills(
        self, mock_get_db: MagicMock, mock_browse: Any, client: Any
    ) -> None:
        """Any authenticated user can browse all published skills."""
        mock_get_db.return_value = MagicMock()
        mock_browse.return_value = ([_skill_summary()], 1)
        resp = client.get(
            "/api/v1/skills",
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_browse_with_divisions_filter_passes_to_service(
        self, mock_get_db: MagicMock, mock_browse: Any, client: Any
    ) -> None:
        """Explicit ?divisions= query param is forwarded to browse_skills."""
        mock_get_db.return_value = MagicMock()
        mock_browse.return_value = ([_skill_summary()], 1)
        resp = client.get(
            "/api/v1/skills?divisions=engineering",
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 200
        call_kwargs = mock_browse.call_args.kwargs
        assert "engineering" in (call_kwargs.get("divisions") or [])

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_browse_without_division_filter_passes_none_to_service(
        self, mock_get_db: MagicMock, mock_browse: Any, client: Any
    ) -> None:
        """Without ?divisions=, service receives divisions=None (no filtering)."""
        mock_get_db.return_value = MagicMock()
        mock_browse.return_value = ([], 0)
        resp = client.get(
            "/api/v1/skills",
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 200
        call_kwargs = mock_browse.call_args.kwargs
        assert call_kwargs.get("divisions") is None

    @patch("skillhub_flask.blueprints.skills.get_skill_detail")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_get_skill_detail_accessible_to_authenticated_user_in_same_division(
        self, mock_get_db: MagicMock, mock_detail: Any, client: Any
    ) -> None:
        """Authenticated user in the skill's division can view detail."""
        mock_get_db.return_value = MagicMock()
        mock_detail.return_value = _skill_detail()
        resp = client.get(
            f"/api/v1/skills/{SLUG}",
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["slug"] == SLUG

    @patch("skillhub_flask.blueprints.skills.get_skill_detail")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_get_skill_detail_accessible_to_user_in_different_division(
        self, mock_get_db: MagicMock, mock_detail: Any, client: Any
    ) -> None:
        """Skill detail browse is not restricted by JWT division (discovery is open).
        Install is where division gating happens, not browse."""
        mock_get_db.return_value = MagicMock()
        mock_detail.return_value = _skill_detail()
        resp = client.get(
            f"/api/v1/skills/{SLUG}",
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.skills.get_skill_detail")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_get_skill_detail_not_found_returns_404(
        self, mock_get_db: MagicMock, mock_detail: Any, client: Any
    ) -> None:
        """Non-existent skill returns 404 regardless of division."""
        mock_get_db.return_value = MagicMock()
        mock_detail.return_value = None
        resp = client.get(
            f"/api/v1/skills/{SLUG}",
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 404

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_unauthenticated_browse_returns_401(
        self, mock_get_db: MagicMock, mock_browse: Any, client: Any
    ) -> None:
        """Unauthenticated browse is blocked by global auth middleware."""
        resp = client.get("/api/v1/skills")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.skills.get_skill_detail")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_unauthenticated_skill_detail_returns_401(
        self, mock_get_db: MagicMock, mock_detail: Any, client: Any
    ) -> None:
        """Unauthenticated skill detail request is rejected."""
        resp = client.get(f"/api/v1/skills/{SLUG}")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.skills.browse_skills")
    @patch("skillhub_flask.blueprints.skills.get_db")
    def test_browse_passes_caller_user_id_for_personalization(
        self, mock_get_db: MagicMock, mock_browse: Any, client: Any
    ) -> None:
        """browse_skills receives the caller's user_id for user_has_installed/favorited."""
        mock_get_db.return_value = MagicMock()
        mock_browse.return_value = ([], 0)
        resp = client.get(
            "/api/v1/skills",
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 200
        call_kwargs = mock_browse.call_args.kwargs
        assert call_kwargs.get("current_user_id") is not None


# ===========================================================================
# Category 3: Submission Division Validation
# ===========================================================================


class TestSubmissionDivisionValidation:
    """POST /api/v1/submissions — division validation behavior.

    Note: create_submission does NOT verify that the caller belongs to any of
    the declared_divisions. The service stores whatever divisions are declared
    and uses them for SkillDivision rows after approval. Division validation
    is a policy gap: a user can claim any division in their submission.
    """

    @patch("skillhub_flask.blueprints.submissions.create_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_engineering_user_submitting_to_engineering_division_returns_201(
        self, mock_get_db: MagicMock, mock_create: MagicMock, client: Any
    ) -> None:
        """User submitting a skill for their own division succeeds."""
        mock_get_db.return_value = MagicMock()
        mock_create.return_value = _submission_result()
        resp = client.post(
            "/api/v1/submissions",
            json={
                "name": "Eng Skill",
                "short_desc": "An engineering skill",
                "category": "code-review",
                "content": "# SKILL.md content here that is long enough",
                "declared_divisions": ["engineering"],
                "division_justification": "Engineering teams use this daily",
            },
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 201
        mock_create.assert_called_once()

    @patch("skillhub_flask.blueprints.submissions.create_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_user_declared_divisions_are_passed_to_service_as_provided(
        self, mock_get_db: MagicMock, mock_create: MagicMock, client: Any
    ) -> None:
        """Service receives declared_divisions exactly as submitted (no server-side
        filtering against JWT division — this is a documented policy gap)."""
        mock_get_db.return_value = MagicMock()
        mock_create.return_value = _submission_result()
        resp = client.post(
            "/api/v1/submissions",
            json={
                "name": "Cross Skill",
                "short_desc": "A cross-division skill",
                "category": "code-review",
                "content": "# SKILL.md content here that is long enough",
                "declared_divisions": ["engineering", "finance"],
                "division_justification": "Both teams benefit",
            },
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 201
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["declared_divisions"] == ["engineering", "finance"]

    @patch("skillhub_flask.blueprints.submissions.create_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_platform_team_can_submit_to_any_division(
        self, mock_get_db: MagicMock, mock_create: MagicMock, client: Any
    ) -> None:
        """Platform team member can submit a skill targeting any division."""
        mock_get_db.return_value = MagicMock()
        mock_create.return_value = _submission_result()
        resp = client.post(
            "/api/v1/submissions",
            json={
                "name": "All-Division Skill",
                "short_desc": "Available to all",
                "category": "code-review",
                "content": "# SKILL.md content here that is long enough",
                "declared_divisions": ["engineering", "finance", "legal"],
                "division_justification": "Platform-wide tool",
            },
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 201

    @patch("skillhub_flask.blueprints.submissions.get_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_submission_owner_can_view_their_submission(
        self, mock_get_db: MagicMock, mock_get: MagicMock, client: Any
    ) -> None:
        """Submission owner can always read their own submission."""
        mock_get_db.return_value = MagicMock()
        sub_id = str(uuid4())
        mock_get.return_value = {
            "id": sub_id,
            "display_id": "SUB-0001",
            "name": "My Skill",
            "short_desc": "A skill",
            "category": "code-review",
            "content": "# SKILL.md",
            "declared_divisions": ["engineering"],
            "division_justification": "Useful for engineering",
            "status": "gate1_passed",
            "submitted_by": USER_ID,
            "gate_results": [],
            "created_at": NOW,
            "updated_at": NOW,
        }
        resp = client.get(
            f"/api/v1/submissions/{sub_id}",
            headers=_auth_headers(_engineering_token(user_id=USER_ID)),
        )
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.submissions.get_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_other_user_cannot_view_submission_returns_403(
        self, mock_get_db: MagicMock, mock_get: MagicMock, client: Any
    ) -> None:
        """Non-owner, non-platform user is blocked from viewing a submission."""
        mock_get_db.return_value = MagicMock()
        sub_id = str(uuid4())
        mock_get.side_effect = PermissionError("Not the submission owner")
        resp = client.get(
            f"/api/v1/submissions/{sub_id}",
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 403

    @patch("skillhub_flask.blueprints.submissions.get_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_platform_team_can_view_any_submission(
        self, mock_get_db: MagicMock, mock_get: MagicMock, client: Any
    ) -> None:
        """Platform team member can read any submission."""
        mock_get_db.return_value = MagicMock()
        sub_id = str(uuid4())
        mock_get.return_value = {
            "id": sub_id,
            "display_id": "SUB-0099",
            "name": "Finance Tool",
            "short_desc": "For finance",
            "category": "code-review",
            "content": "# SKILL.md",
            "declared_divisions": ["finance"],
            "division_justification": "Finance only",
            "status": "gate1_passed",
            "submitted_by": FINANCE_USER_ID,
            "gate_results": [],
            "created_at": NOW,
            "updated_at": NOW,
        }
        resp = client.get(
            f"/api/v1/submissions/{sub_id}",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200

    def test_unauthenticated_submission_returns_401(self, client: Any) -> None:
        """Unauthenticated submission is rejected at auth middleware."""
        resp = client.post(
            "/api/v1/submissions",
            json={
                "name": "Skill",
                "short_desc": "A skill",
                "category": "code-review",
                "content": "# SKILL.md content here",
                "declared_divisions": ["engineering"],
                "division_justification": "For engineering",
            },
        )
        assert resp.status_code == 401


# ===========================================================================
# Category 4: Admin Endpoints Division Scope
# ===========================================================================


class TestAdminEndpointsDivisionScope:
    """Admin endpoints gated by require_platform_team decorator."""

    @patch("skillhub_flask.blueprints.submissions.list_admin_submissions")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_platform_team_can_list_all_submissions(
        self, mock_get_db: MagicMock, mock_list: MagicMock, client: Any
    ) -> None:
        """Platform team sees all submissions across all divisions."""
        mock_get_db.return_value = MagicMock()
        mock_list.return_value = ([_admin_summary()], 1)
        resp = client.get(
            "/api/v1/admin/submissions",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1

    def test_regular_user_cannot_list_admin_submissions_returns_403(
        self, client: Any
    ) -> None:
        """Non-platform user is blocked from admin submissions list."""
        resp = client.get(
            "/api/v1/admin/submissions",
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 403

    def test_finance_user_cannot_list_admin_submissions_returns_403(
        self, client: Any
    ) -> None:
        """Finance division user cannot access admin review queue."""
        resp = client.get(
            "/api/v1/admin/submissions",
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 403

    def test_unauthenticated_cannot_list_admin_submissions_returns_401(
        self, client: Any
    ) -> None:
        """Unauthenticated request is rejected before platform team check."""
        resp = client.get("/api/v1/admin/submissions")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.submissions.review_submission")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_platform_team_can_review_submission(
        self, mock_get_db: MagicMock, mock_review: MagicMock, client: Any
    ) -> None:
        """Platform team can approve/reject submissions from any division."""
        mock_get_db.return_value = MagicMock()
        mock_review.return_value = {"status": "approved"}
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/submissions/{sub_id}/review",
            json={"decision": "approved", "notes": "Looks good"},
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200

    def test_regular_user_cannot_review_submission_returns_403(
        self, client: Any
    ) -> None:
        """Regular division user cannot perform admin review."""
        sub_id = str(uuid4())
        resp = client.post(
            f"/api/v1/admin/submissions/{sub_id}/review",
            json={"decision": "approved", "notes": "ok"},
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 403

    @patch("skillhub_flask.blueprints.submissions.list_access_requests")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_platform_team_can_list_access_requests(
        self, mock_get_db: MagicMock, mock_list: MagicMock, client: Any
    ) -> None:
        """Platform team can view all cross-division access requests."""
        mock_get_db.return_value = MagicMock()
        mock_list.return_value = ([], 0)
        resp = client.get(
            "/api/v1/admin/access-requests",
            headers=_auth_headers(_platform_token()),
        )
        assert resp.status_code == 200

    def test_regular_user_cannot_list_access_requests_returns_403(
        self, client: Any
    ) -> None:
        """Regular user cannot access the admin access-requests list."""
        resp = client.get(
            "/api/v1/admin/access-requests",
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 403

    def test_no_division_user_cannot_access_admin_endpoints_returns_403(
        self, client: Any
    ) -> None:
        """User with no division claim still cannot access admin endpoints."""
        resp = client.get(
            "/api/v1/admin/submissions",
            headers=_auth_headers(_no_division_token()),
        )
        assert resp.status_code == 403


# ===========================================================================
# Category 5: Social Features Division Gating
# ===========================================================================


class TestSocialFeaturesDivisionGating:
    """Social features (favorite, fork) — division behavior.

    Note: favorite_skill and fork_skill do NOT check SkillDivision rows in the
    service layer. Division enforcement only applies to install_skill. This is by
    design: favorites and forks are non-destructive/low-stakes actions.
    """

    @patch("skillhub_flask.blueprints.social.favorite_skill")
    def test_engineering_user_can_favorite_engineering_skill(
        self, mock_fav: Any, client: Any
    ) -> None:
        """User favorites a skill in their own division — succeeds."""
        mock_fav.return_value = _favorite_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/favorite",
            headers=_auth_headers(_engineering_token()),
        )
        assert resp.status_code == 200

    @patch("skillhub_flask.blueprints.social.favorite_skill")
    def test_finance_user_can_favorite_engineering_skill(
        self, mock_fav: Any, client: Any
    ) -> None:
        """favorite_skill has no division check — cross-division favorite is allowed."""
        mock_fav.return_value = _favorite_result(user_id=FINANCE_USER_ID)
        resp = client.post(
            f"/api/v1/skills/{SLUG}/favorite",
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 200

    def test_favorite_without_auth_returns_401(self, client: Any) -> None:
        """Unauthenticated favorite is blocked."""
        resp = client.post(f"/api/v1/skills/{SLUG}/favorite")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.fork_skill")
    def test_user_can_fork_skill_from_different_division(
        self, mock_fork: Any, client: Any
    ) -> None:
        """fork_skill has no division check — cross-division fork is allowed."""
        mock_fork.return_value = _fork_result(user_id=FINANCE_USER_ID)
        resp = client.post(
            f"/api/v1/skills/{SLUG}/fork",
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "forked_skill_slug" in data

    def test_fork_without_auth_returns_401(self, client: Any) -> None:
        """Unauthenticated fork is blocked."""
        resp = client.post(f"/api/v1/skills/{SLUG}/fork")
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_install_is_the_gated_action_not_favorite(
        self, mock_install: Any, client: Any
    ) -> None:
        """Confirm install is where division gating happens for the same slug."""
        mock_install.side_effect = PermissionError("division_restricted")
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 403

    @patch("skillhub_flask.blueprints.social.create_review")
    def test_user_can_post_review_regardless_of_division(
        self, mock_review: Any, client: Any
    ) -> None:
        """create_review has no division check — cross-division reviews are allowed."""
        mock_review.return_value = {
            "id": str(uuid4()),
            "skill_id": SKILL_ID,
            "user_id": FINANCE_USER_ID,
            "rating": 4,
            "body": "Useful skill",
            "helpful_count": 0,
            "unhelpful_count": 0,
            "created_at": NOW,
            "updated_at": NOW,
        }
        resp = client.post(
            f"/api/v1/skills/{SLUG}/reviews",
            json={"rating": 4, "body": "Useful skill"},
            headers=_auth_headers(_finance_token()),
        )
        assert resp.status_code == 201


# ===========================================================================
# Category 6: Cross-Division Data Leakage and JWT Integrity
# ===========================================================================


class TestCrossDivisionDataLeakageAndJWTIntegrity:
    """JWT signature validation and division claim integrity."""

    def test_tampered_jwt_signature_rejected_returns_401(
        self, client: Any
    ) -> None:
        """A JWT with a tampered payload (different signature) is rejected."""
        valid_token = _engineering_token()
        # Corrupt the signature (last segment) by appending extra chars
        parts = valid_token.split(".")
        tampered_token = f"{parts[0]}.{parts[1]}.{parts[2]}TAMPERED"
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(tampered_token),
        )
        assert resp.status_code == 401

    def test_jwt_signed_with_wrong_secret_rejected_returns_401(
        self, client: Any
    ) -> None:
        """A JWT signed with a different secret is rejected — division claim cannot
        be upgraded by a token forged outside the system."""
        forged_token = jwt.encode(
            {
                "sub": "attacker",
                "user_id": str(uuid4()),
                "division": "engineering",
                "is_platform_team": True,
                "exp": int(time.time()) + 3600,
            },
            "wrong-secret",
            algorithm=TEST_JWT_ALGORITHM,
        )
        resp = client.get(
            "/api/v1/admin/submissions",
            headers=_auth_headers(forged_token),
        )
        assert resp.status_code == 401

    def test_expired_jwt_rejected_returns_401(self, client: Any) -> None:
        """An expired token is rejected even if its division claim would be valid."""
        expired_token = make_token(
            payload={
                "sub": "eng-user",
                "user_id": str(uuid4()),
                "division": "engineering",
                "is_platform_team": False,
            },
            expired=True,
        )
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(expired_token),
        )
        assert resp.status_code == 401
        assert "expired" in resp.get_json()["detail"].lower()

    def test_missing_authorization_header_returns_401(
        self, client: Any
    ) -> None:
        """Completely missing Authorization header returns 401."""
        resp = client.get("/api/v1/admin/submissions")
        assert resp.status_code == 401

    def test_bearer_prefix_required(self, client: Any) -> None:
        """Authorization header without 'Bearer ' prefix returns 401."""
        token = _engineering_token()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers={"Authorization": token},  # no "Bearer " prefix
        )
        assert resp.status_code == 401

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_division_from_jwt_used_not_query_param(
        self, mock_install: Any, client: Any
    ) -> None:
        """Division is read from the validated JWT payload — not from query params.
        A query param claiming a different division has no effect on authorization."""
        mock_install.return_value = _install_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install?division=engineering",  # ignored param
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_finance_token()),
        )
        # Service was called with division from JWT ("finance"), not query param
        assert resp.status_code == 201  # mock allows it; key check is in call_args
        call_args = mock_install.call_args
        user_division_arg = call_args.args[3] if len(call_args.args) > 3 else call_args.kwargs.get("user_division", "UNSET")
        assert user_division_arg == "finance"

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_division_cannot_be_overridden_via_request_body(
        self, mock_install: Any, client: Any
    ) -> None:
        """Request body fields cannot override the division extracted from the JWT."""
        mock_install.return_value = _install_result()
        resp = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={
                "method": "claude-code",
                "version": "1.0.0",
                "division": "engineering",  # attempted override — InstallRequest ignores this
            },
            headers=_auth_headers(_finance_token()),
        )
        # Division in service call must come from JWT, not body
        assert resp.status_code == 201
        call_args = mock_install.call_args
        user_division_arg = call_args.args[3] if len(call_args.args) > 3 else call_args.kwargs.get("user_division", "UNSET")
        assert user_division_arg == "finance"

    @patch("skillhub_flask.blueprints.social.install_skill")
    def test_two_users_same_division_but_different_ids_tracked_separately(
        self, mock_install: Any, client: Any
    ) -> None:
        """Two users in the same division have independent install records."""
        user_a = str(uuid4())
        user_b = str(uuid4())
        mock_install.return_value = _install_result(user_id=user_a)

        resp_a = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_engineering_token(user_id=user_a)),
        )
        assert resp_a.status_code == 201

        mock_install.return_value = _install_result(user_id=user_b)
        resp_b = client.post(
            f"/api/v1/skills/{SLUG}/install",
            json={"method": "claude-code", "version": "1.0.0"},
            headers=_auth_headers(_engineering_token(user_id=user_b)),
        )
        assert resp_b.status_code == 201
        # Each call used its own user_id
        assert mock_install.call_count == 2
        call_a_user_id = mock_install.call_args_list[0].args[2]
        call_b_user_id = mock_install.call_args_list[1].args[2]
        assert call_a_user_id != call_b_user_id

    @patch("skillhub_flask.blueprints.submissions.create_access_request")
    @patch("skillhub_flask.blueprints.submissions.get_db")
    def test_access_request_records_user_division_from_jwt(
        self, mock_get_db: MagicMock, mock_create: MagicMock, client: Any
    ) -> None:
        """When a cross-division access request is filed, the user_division stored
        comes from the JWT, not from the request body."""
        mock_get_db.return_value = MagicMock()
        mock_create.return_value = {
            "id": str(uuid4()),
            "skill_id": SKILL_ID,
            "requested_by": FINANCE_USER_ID,
            "user_division": "finance",
            "reason": "I need this",
            "status": "pending",
            "created_at": NOW,
        }
        resp = client.post(
            f"/api/v1/skills/{SLUG}/access-request",
            json={"reason": "I need this"},
            headers=_auth_headers(_finance_token(user_id=FINANCE_USER_ID)),
        )
        assert resp.status_code == 201
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["user_division"] == "finance"
