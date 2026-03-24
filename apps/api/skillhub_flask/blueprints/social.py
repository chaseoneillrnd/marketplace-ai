"""Social layer blueprint: install, favorite, fork, follow, reviews, comments."""

from __future__ import annotations

import logging
from uuid import UUID

from flask import Blueprint, g, jsonify, request

from skillhub_flask.db import get_db
from skillhub_flask.validation import DivisionRestrictedError

from skillhub.schemas.social import (
    CommentCreateRequest,
    CommentListResponse,
    CommentResponse,
    FavoriteResponse,
    FollowResponse,
    ForkResponse,
    InstallRequest,
    InstallResponse,
    ReplyCreateRequest,
    ReplyResponse,
    ReviewCreateRequest,
    ReviewListResponse,
    ReviewResponse,
    ReviewUpdateRequest,
    ReviewVoteRequest,
)
from skillhub.services.reviews import (
    DuplicateReviewError,
    create_comment,
    create_reply,
    create_review,
    delete_comment,
    list_comments,
    list_reviews,
    update_review,
    vote_on_comment,
    vote_on_review,
)
from skillhub.services.social import (
    favorite_skill,
    follow_user,
    fork_skill,
    install_skill,
    unfavorite_skill,
    unfollow_user,
    uninstall_skill,
)

logger = logging.getLogger(__name__)

bp = Blueprint("social", __name__, url_prefix="/api/v1/skills")


@bp.errorhandler(DivisionRestrictedError)
def handle_division_restricted(exc: DivisionRestrictedError) -> tuple:
    """Return 403 with structured error for division-restricted access."""
    return jsonify({"detail": {"error": "division_restricted"}}), 403


# --- Install ---


@bp.route("/<slug>/install", methods=["POST"])
def post_install(slug: str) -> tuple:
    """Install a skill. Checks division authorization."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    user_division = current_user.get("division", "")
    body = InstallRequest(**request.get_json())
    db = get_db()
    try:
        result = install_skill(
            db, slug, user_id, user_division, body.method, body.version
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    except PermissionError:
        raise DivisionRestrictedError()
    return jsonify(InstallResponse(**result).model_dump(mode="json")), 201


@bp.route("/<slug>/install", methods=["DELETE"])
def delete_install(slug: str) -> tuple:
    """Uninstall a skill (soft delete)."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    db = get_db()
    try:
        uninstall_skill(db, slug, user_id)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    return "", 204


# --- Favorite ---


@bp.route("/<slug>/favorite", methods=["POST"])
def post_favorite(slug: str) -> tuple:
    """Favorite a skill (idempotent upsert)."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    db = get_db()
    try:
        result = favorite_skill(db, slug, user_id)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    return jsonify(FavoriteResponse(**result).model_dump(mode="json")), 200


@bp.route("/<slug>/favorite", methods=["DELETE"])
def delete_favorite(slug: str) -> tuple:
    """Remove a favorite."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    db = get_db()
    try:
        unfavorite_skill(db, slug, user_id)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    return "", 204


# --- Fork ---


@bp.route("/<slug>/fork", methods=["POST"])
def post_fork(slug: str) -> tuple:
    """Fork a skill."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    db = get_db()
    try:
        result = fork_skill(db, slug, user_id)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    return jsonify(ForkResponse(**result).model_dump(mode="json")), 201


# --- Follow ---


@bp.route("/<slug>/follow", methods=["POST"])
def post_follow(slug: str) -> tuple:
    """Follow the author of a skill (idempotent upsert)."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    db = get_db()
    try:
        result = follow_user(db, slug, user_id)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    return jsonify(FollowResponse(**result).model_dump(mode="json")), 200


@bp.route("/<slug>/follow", methods=["DELETE"])
def delete_follow(slug: str) -> tuple:
    """Unfollow the author of a skill."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    db = get_db()
    try:
        unfollow_user(db, slug, user_id)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    return "", 204


# --- Reviews ---


@bp.route("/<slug>/reviews", methods=["GET"])
def get_reviews(slug: str) -> tuple:
    """Get paginated reviews sorted by helpful_count DESC."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    page = max(1, page)
    per_page = max(1, min(100, per_page))
    db = get_db()
    try:
        items, total = list_reviews(db, slug, page=page, per_page=per_page)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    has_more = (page * per_page) < total
    response = ReviewListResponse(
        items=[ReviewResponse(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/<slug>/reviews", methods=["POST"])
def post_review(slug: str) -> tuple:
    """Create a review. 409 if already reviewed."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    body = ReviewCreateRequest(**request.get_json())
    db = get_db()
    try:
        result = create_review(db, slug, user_id, body.rating, body.body)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    except DuplicateReviewError as err:
        return jsonify({"detail": str(err)}), 409
    return jsonify(ReviewResponse(**result).model_dump(mode="json")), 201


@bp.route("/<slug>/reviews/<uuid:review_id>", methods=["PATCH"])
def patch_review(slug: str, review_id: UUID) -> tuple:
    """Update a review. Owner only."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    body = ReviewUpdateRequest(**request.get_json())
    db = get_db()
    try:
        result = update_review(
            db, slug, review_id, user_id, rating=body.rating, body=body.body
        )
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    except PermissionError as err:
        return jsonify({"detail": str(err)}), 403
    return jsonify(ReviewResponse(**result).model_dump(mode="json")), 200


@bp.route("/<slug>/reviews/<uuid:review_id>/vote", methods=["POST"])
def post_review_vote(slug: str, review_id: UUID) -> tuple:
    """Vote on a review (helpful/unhelpful)."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    body = ReviewVoteRequest(**request.get_json())
    db = get_db()
    try:
        vote_on_review(db, slug, review_id, user_id, body.vote)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    return "", 204


# --- Comments ---


@bp.route("/<slug>/comments", methods=["GET"])
def get_comments(slug: str) -> tuple:
    """Get paginated comments with nested replies."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    page = max(1, page)
    per_page = max(1, min(100, per_page))
    db = get_db()
    try:
        items, total = list_comments(db, slug, page=page, per_page=per_page)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    has_more = (page * per_page) < total
    response = CommentListResponse(
        items=[CommentResponse(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )
    return jsonify(response.model_dump(mode="json")), 200


@bp.route("/<slug>/comments", methods=["POST"])
def post_comment(slug: str) -> tuple:
    """Create a comment on a skill."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    body = CommentCreateRequest(**request.get_json())
    db = get_db()
    try:
        result = create_comment(db, slug, user_id, body.body)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    return jsonify(CommentResponse(**result).model_dump(mode="json")), 201


@bp.route("/<slug>/comments/<uuid:comment_id>", methods=["DELETE"])
def remove_comment(slug: str, comment_id: UUID) -> tuple:
    """Soft delete a comment (owner or platform team)."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    is_platform = current_user.get("is_platform_team", False)
    db = get_db()
    try:
        result = delete_comment(db, slug, comment_id, user_id, is_platform_team=is_platform)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    except PermissionError as err:
        return jsonify({"detail": str(err)}), 403
    return jsonify(CommentResponse(**result).model_dump(mode="json")), 200


@bp.route("/<slug>/comments/<uuid:comment_id>/replies", methods=["POST"])
def post_reply(slug: str, comment_id: UUID) -> tuple:
    """Reply to a comment."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    body = ReplyCreateRequest(**request.get_json())
    db = get_db()
    try:
        result = create_reply(db, slug, comment_id, user_id, body.body)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    return jsonify(ReplyResponse(**result).model_dump(mode="json")), 201


@bp.route("/<slug>/comments/<uuid:comment_id>/vote", methods=["POST"])
def post_comment_vote(slug: str, comment_id: UUID) -> tuple:
    """Upvote a comment (idempotent)."""
    current_user = g.current_user
    user_id = UUID(current_user["user_id"])
    db = get_db()
    try:
        vote_on_comment(db, slug, comment_id, user_id)
    except ValueError as err:
        return jsonify({"detail": str(err)}), 404
    return "", 204
