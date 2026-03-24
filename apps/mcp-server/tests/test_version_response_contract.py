"""Schema contract tests — verify MCP tool expectations match real API schemas.

These tests import the actual Pydantic schemas from the API and assert that
fields the MCP tools depend on actually exist. This prevents drift where mocked
test fixtures include fields the real API doesn't return.
"""

from __future__ import annotations

import re

import pytest

from skillhub_mcp.tools.install import _is_valid_slug


class TestSkillVersionResponseContract:
    """Verify SkillVersionResponse has the fields MCP tools depend on."""

    def test_divisions_field_exists(self) -> None:
        """SkillVersionResponse must have a 'divisions' field for install/update enforcement."""
        from skillhub.schemas.skill import SkillVersionResponse

        fields = SkillVersionResponse.model_fields
        assert "divisions" in fields, (
            "SkillVersionResponse is missing 'divisions' field. "
            "install_skill and update_skill read data.get('divisions', []) from the "
            "version endpoint response. Without this field, division enforcement is dead code."
        )

    def test_divisions_field_is_list_of_str(self) -> None:
        """The divisions field should default to an empty list."""
        from skillhub.schemas.skill import SkillVersionResponse

        field = SkillVersionResponse.model_fields["divisions"]
        assert field.default == []

    def test_version_response_has_content_field(self) -> None:
        """SkillVersionResponse must have 'content' — install_skill writes it to SKILL.md."""
        from skillhub.schemas.skill import SkillVersionResponse

        assert "content" in SkillVersionResponse.model_fields

    def test_version_response_has_version_field(self) -> None:
        """SkillVersionResponse must have 'version' — used for staleness checks."""
        from skillhub.schemas.skill import SkillVersionResponse

        assert "version" in SkillVersionResponse.model_fields


class TestSkillDetailContract:
    """Verify SkillDetail has the fields get_skill tool depends on."""

    def test_detail_has_divisions(self) -> None:
        """SkillDetail must include divisions for display."""
        from skillhub.schemas.skill import SkillDetail

        assert "divisions" in SkillDetail.model_fields

    def test_detail_has_current_version_content(self) -> None:
        """SkillDetail must embed version content for the get_skill tool."""
        from skillhub.schemas.skill import SkillDetail

        assert "current_version_content" in SkillDetail.model_fields

    def test_detail_has_install_count(self) -> None:
        """SkillDetail must have install_count for display."""
        from skillhub.schemas.skill import SkillDetail

        assert "install_count" in SkillDetail.model_fields


class TestSlugValidation:
    """Verify slug validation prevents path traversal."""

    @pytest.mark.parametrize(
        "slug",
        [
            "code-review-assistant",
            "my-skill",
            "a1",
            "test-123-skill",
        ],
    )
    def test_valid_slugs(self, slug: str) -> None:
        assert _is_valid_slug(slug) is True

    @pytest.mark.parametrize(
        "slug",
        [
            "../etc/passwd",
            "../../.ssh/authorized_keys",
            "",
            "a",  # single char too short
            "-bad-start",
            "bad-end-",
            "UPPERCASE",
            "has spaces",
            "has/slash",
            "has.dot",
            "has\x00null",
        ],
    )
    def test_invalid_slugs(self, slug: str) -> None:
        assert _is_valid_slug(slug) is False
