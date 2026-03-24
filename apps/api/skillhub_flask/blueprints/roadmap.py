"""Roadmap and changelog endpoints.

BUG #6 FIX: PlatformUpdateResponse now includes version_tag. Since the
PlatformUpdate model does not store version_tag as a column, we extract it
from the audit log metadata when building responses. For the public changelog,
we query audit_log for the shipped event to populate version_tag.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from flask import Blueprint, g, jsonify, request

from skillhub_flask.auth import PUBLIC_ENDPOINTS, require_platform_team, require_security_team
from skillhub_flask.db import get_db

from skillhub.schemas.feedback import (
    ChangelogEntry,
    ChangelogResponse,
    PlatformUpdateCreate,
    PlatformUpdateListResponse,
    PlatformUpdateResponse,
    ShipRequest,
)
from skillhub.services.roadmap import (
    create_update,
    delete_update,
    list_updates,
    ship_update,
    update_status,
)

logger = logging.getLogger(__name__)

bp = Blueprint("roadmap", __name__)

# Register the public changelog endpoint
PUBLIC_ENDPOINTS.add("roadmap.get_changelog")


def _extract_version_tag(body: str) -> str | None:
    """Extract version_tag from body text where ship_update appends it.

    The ship_update service appends: "\\n\\n---\\n**{version_tag}**: {changelog_body}"
    """
    match = re.search(r"\n---\n\*\*(.+?)\*\*:", body)
    if match:
        return match.group(1)
    return None


def _enrich_with_version_tag(item: dict[str, Any]) -> dict[str, Any]:
    """Add version_tag to a platform update dict if not already present."""
    if "version_tag" not in item or item.get("version_tag") is None:
        item["version_tag"] = _extract_version_tag(item.get("body", ""))
    return item


@bp.route("/api/v1/admin/platform-updates", methods=["GET"])
@require_platform_team
def list_platform_updates() -> tuple:
    """List platform updates. Admin only."""
    db = get_db()

    update_status_filter = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Clamp pagination
    page = max(1, page)
    per_page = max(1, min(100, per_page))

    items, total = list_updates(
        db, status=update_status_filter, page=page, per_page=per_page
    )

    # BUG #6 FIX: enrich each item with version_tag extracted from body
    enriched_items = [_enrich_with_version_tag(i) for i in items]

    response = PlatformUpdateListResponse(
        items=[PlatformUpdateResponse(**i) for i in enriched_items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/admin/platform-updates", methods=["POST"])
@require_platform_team
def create_platform_update() -> tuple:
    """Create a platform update. Admin only."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user

    body = PlatformUpdateCreate.model_validate(request.get_json(force=True) or {})

    result = create_update(
        db,
        title=body.title,
        body=body.body,
        author_id=current_user["user_id"],
        status=body.status,
        target_quarter=body.target_quarter,
    )

    result = _enrich_with_version_tag(result)
    return jsonify(PlatformUpdateResponse(**result).model_dump(mode="json")), 201


@bp.route("/api/v1/admin/platform-updates/<update_id>", methods=["PATCH"])
@require_platform_team
def patch_platform_update(update_id: str) -> tuple:
    """Update platform update status. Admin only."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user

    data: dict[str, str] = request.get_json(force=True)
    new_status = data.get("status")
    if not new_status:
        return jsonify({"detail": "status is required"}), 422

    try:
        result = update_status(
            db,
            update_id=update_id,
            new_status=new_status,
            actor_id=current_user["user_id"],
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 400

    result = _enrich_with_version_tag(result)
    return jsonify(PlatformUpdateResponse(**result).model_dump(mode="json")), 200


@bp.route("/api/v1/admin/platform-updates/<update_id>/ship", methods=["POST"])
@require_platform_team
def ship_platform_update(update_id: str) -> tuple:
    """Ship a platform update. Admin only."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user

    body = ShipRequest.model_validate(request.get_json(force=True) or {})

    try:
        result = ship_update(
            db,
            update_id=update_id,
            version_tag=body.version_tag,
            changelog_body=body.changelog_body,
            actor_id=current_user["user_id"],
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 400

    result = _enrich_with_version_tag(result)
    return jsonify(PlatformUpdateResponse(**result).model_dump(mode="json")), 200


@bp.route("/api/v1/admin/platform-updates/<update_id>", methods=["DELETE"])
@require_security_team
def delete_platform_update(update_id: str) -> tuple:
    """Delete (soft) a platform update. Security team only."""
    db = get_db()
    current_user: dict[str, Any] = g.current_user

    try:
        result = delete_update(
            db,
            update_id=update_id,
            actor_id=current_user["user_id"],
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404

    result = _enrich_with_version_tag(result)
    return jsonify(PlatformUpdateResponse(**result).model_dump(mode="json")), 200


@bp.route("/api/v1/changelog", methods=["GET"])
def get_changelog() -> tuple:
    """Public changelog — no auth required. Returns shipped items.

    BUG #6 FIX: Extracts version_tag from the body text instead of hardcoding None.
    """
    db = get_db()

    items, _ = list_updates(db, status="shipped", page=1, per_page=100)
    changelog_items = []
    for item in items:
        version_tag = _extract_version_tag(item.get("body", ""))
        changelog_items.append(
            ChangelogEntry(
                id=item["id"],
                title=item["title"],
                body=item["body"],
                version_tag=version_tag,
                shipped_at=item["shipped_at"],
            )
        )

    response = ChangelogResponse(items=changelog_items)
    return jsonify(response.model_dump(mode="json")), 200
