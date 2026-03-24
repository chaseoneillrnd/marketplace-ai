"""Skills browse, detail, and version endpoints."""

from __future__ import annotations

import logging
import threading
from typing import Any
from uuid import UUID

from flask import Blueprint, g, jsonify, request

from skillhub_flask.db import get_db

from skillhub_db.session import SessionLocal

from skillhub.schemas.skill import (
    SkillBrowseResponse,
    SkillDetail,
    SkillSummary,
    SkillVersionListItem,
    SkillVersionResponse,
    SortOption,
)
from skillhub.services.skills import browse_skills, get_skill_detail, increment_view_count

logger = logging.getLogger(__name__)

bp = Blueprint("skills", __name__)


@bp.route("/api/v1/skills", methods=["GET"])
def list_skills() -> tuple:
    """Browse/search skills with filters, sorting, and pagination."""
    db = get_db()

    q = request.args.get("q")
    category = request.args.get("category")
    divisions = request.args.getlist("divisions")
    sort_value = request.args.get("sort", SortOption.TRENDING.value)
    install_method = request.args.get("install_method")
    verified_raw = request.args.get("verified")
    featured_raw = request.args.get("featured")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Clamp pagination
    page = max(1, page)
    per_page = max(1, min(100, per_page))

    # Parse optional booleans
    verified: bool | None = None
    if verified_raw is not None:
        verified = verified_raw.lower() in ("true", "1")

    featured: bool | None = None
    if featured_raw is not None:
        featured = featured_raw.lower() in ("true", "1")

    # Optional user on public route
    user: dict[str, Any] | None = getattr(g, "current_user", None)
    current_user_id: UUID | None = None
    if user and user.get("user_id"):
        current_user_id = UUID(user["user_id"])

    items, total = browse_skills(
        db,
        q=q,
        category=category,
        divisions=divisions if divisions else None,
        sort=sort_value,
        install_method=install_method,
        verified=verified,
        featured=featured,
        page=page,
        per_page=per_page,
        current_user_id=current_user_id,
    )

    skill_summaries = [SkillSummary(**item) for item in items]
    has_more = (page * per_page) < total

    response = SkillBrowseResponse(
        items=skill_summaries,
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/skills/categories", methods=["GET"])
def list_categories() -> tuple:
    """List all available categories."""
    from skillhub_db.models.skill import Category

    db = get_db()
    categories = db.query(Category).order_by(Category.sort_order).all()
    return jsonify([{"slug": c.slug, "name": c.name, "sort_order": c.sort_order} for c in categories]), 200


@bp.route("/api/v1/skills/<slug>", methods=["GET"])
def get_skill(slug: str) -> tuple:
    """Get full skill detail by slug."""
    db = get_db()

    # Optional user on public route
    user: dict[str, Any] | None = getattr(g, "current_user", None)
    current_user_id: UUID | None = None
    if user and user.get("user_id"):
        current_user_id = UUID(user["user_id"])

    result = get_skill_detail(db, slug, current_user_id=current_user_id)
    if not result:
        return jsonify({"detail": f"Skill '{slug}' not found"}), 404

    # Fire-and-forget view count increment — use a fresh session because
    # the request-scoped `db` may be closed by the time the thread runs.
    skill_id = result["id"]

    def _bg_increment_view(sid: UUID) -> None:
        bg_db = SessionLocal()
        try:
            increment_view_count(bg_db, sid)
        finally:
            bg_db.close()

    threading.Thread(target=_bg_increment_view, args=(skill_id,), daemon=True).start()

    return jsonify(SkillDetail(**result).model_dump(mode="json")), 200


@bp.route("/api/v1/skills/<slug>/versions", methods=["GET"])
def list_versions(slug: str) -> tuple:
    """List all published versions for a skill. Auth required."""
    from skillhub_db.models.skill import Skill as SkillModel
    from skillhub_db.models.skill import SkillVersion as SkillVersionModel

    db = get_db()

    skill = db.query(SkillModel).filter(SkillModel.slug == slug).first()
    if not skill:
        return jsonify({"detail": f"Skill '{slug}' not found"}), 404

    versions = (
        db.query(SkillVersionModel)
        .filter(SkillVersionModel.skill_id == skill.id)
        .order_by(SkillVersionModel.published_at.desc())
        .all()
    )

    items = [
        SkillVersionListItem(
            id=v.id,
            version=v.version,
            changelog=v.changelog,
            published_at=v.published_at,
        ).model_dump(mode="json")
        for v in versions
    ]
    return jsonify(items), 200


@bp.route("/api/v1/skills/<slug>/versions/latest", methods=["GET"])
def get_latest_version(slug: str) -> tuple:
    """Get latest version content for a skill. Auth required."""
    from skillhub_db.models.skill import Skill as SkillModel
    from skillhub_db.models.skill import SkillVersion as SkillVersionModel

    db = get_db()

    skill = db.query(SkillModel).filter(SkillModel.slug == slug).first()
    if not skill:
        return jsonify({"detail": f"Skill '{slug}' not found"}), 404

    version = (
        db.query(SkillVersionModel)
        .filter(
            SkillVersionModel.skill_id == skill.id,
            SkillVersionModel.version == skill.current_version,
        )
        .first()
    )
    if not version:
        return jsonify({"detail": "Current version not found"}), 404

    response = SkillVersionResponse(
        id=version.id,
        version=version.version,
        content=version.content,
        frontmatter=version.frontmatter,
        changelog=version.changelog,
        published_at=version.published_at,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/api/v1/skills/<slug>/versions/<version>", methods=["GET"])
def get_version(slug: str, version: str) -> tuple:
    """Get specific version content for a skill. Auth required."""
    from skillhub_db.models.skill import Skill as SkillModel
    from skillhub_db.models.skill import SkillVersion as SkillVersionModel

    db = get_db()

    skill = db.query(SkillModel).filter(SkillModel.slug == slug).first()
    if not skill:
        return jsonify({"detail": f"Skill '{slug}' not found"}), 404

    # Resolve "latest" alias
    target_version = skill.current_version if version == "latest" else version

    ver = (
        db.query(SkillVersionModel)
        .filter(
            SkillVersionModel.skill_id == skill.id,
            SkillVersionModel.version == target_version,
        )
        .first()
    )
    if not ver:
        return jsonify({"detail": f"Version '{version}' not found"}), 404

    response = SkillVersionResponse(
        id=ver.id,
        version=ver.version,
        content=ver.content,
        frontmatter=ver.frontmatter,
        changelog=ver.changelog,
        published_at=ver.published_at,
    )
    return jsonify(response.model_dump(mode="json")), 200
