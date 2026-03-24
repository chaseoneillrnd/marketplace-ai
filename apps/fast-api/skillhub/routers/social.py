"""Social layer endpoints: install, favorite, fork, follow, reviews, comments."""

from __future__ import annotations

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_current_user, get_db
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

router = APIRouter(prefix="/api/v1/skills", tags=["social"])


# --- Install ---


@router.post("/{slug}/install", response_model=InstallResponse, status_code=status.HTTP_201_CREATED)
def post_install(
    slug: str,
    body: InstallRequest,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InstallResponse:
    """Install a skill. Checks division authorization."""
    user_id = UUID(current_user["user_id"])
    user_division = current_user.get("division", "")
    try:
        result = install_skill(
            db, slug, user_id, user_division, body.method, body.version
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "division_restricted"},
        )
    return InstallResponse(**result)


@router.delete("/{slug}/install", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_install(
    slug: str,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Uninstall a skill (soft delete)."""
    user_id = UUID(current_user["user_id"])
    try:
        uninstall_skill(db, slug, user_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


# --- Favorite ---


@router.post("/{slug}/favorite", response_model=FavoriteResponse, status_code=status.HTTP_200_OK)
def post_favorite(
    slug: str,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FavoriteResponse:
    """Favorite a skill (idempotent upsert)."""
    user_id = UUID(current_user["user_id"])
    try:
        result = favorite_skill(db, slug, user_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return FavoriteResponse(**result)


@router.delete("/{slug}/favorite", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_favorite(
    slug: str,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Remove a favorite."""
    user_id = UUID(current_user["user_id"])
    try:
        unfavorite_skill(db, slug, user_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


# --- Fork ---


@router.post("/{slug}/fork", response_model=ForkResponse, status_code=status.HTTP_201_CREATED)
def post_fork(
    slug: str,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ForkResponse:
    """Fork a skill."""
    user_id = UUID(current_user["user_id"])
    try:
        result = fork_skill(db, slug, user_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return ForkResponse(**result)


# --- Follow ---


@router.post("/{slug}/follow", response_model=FollowResponse, status_code=status.HTTP_200_OK)
def post_follow(
    slug: str,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FollowResponse:
    """Follow the author of a skill (idempotent upsert)."""
    user_id = UUID(current_user["user_id"])
    try:
        result = follow_user(db, slug, user_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return FollowResponse(**result)


@router.delete("/{slug}/follow", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_follow(
    slug: str,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Unfollow the author of a skill."""
    user_id = UUID(current_user["user_id"])
    try:
        unfollow_user(db, slug, user_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


# --- Reviews ---


@router.get("/{slug}/reviews", response_model=ReviewListResponse)
def get_reviews(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> ReviewListResponse:
    """Get paginated reviews sorted by helpful_count DESC."""
    try:
        items, total = list_reviews(db, slug, page=page, per_page=per_page)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    has_more = (page * per_page) < total
    return ReviewListResponse(
        items=[ReviewResponse(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.post("/{slug}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def post_review(
    slug: str,
    body: ReviewCreateRequest,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReviewResponse:
    """Create a review. 409 if already reviewed."""
    user_id = UUID(current_user["user_id"])
    try:
        result = create_review(db, slug, user_id, body.rating, body.body)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except DuplicateReviewError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    return ReviewResponse(**result)


@router.patch("/{slug}/reviews/{review_id}", response_model=ReviewResponse)
def patch_review(
    slug: str,
    review_id: UUID,
    body: ReviewUpdateRequest,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReviewResponse:
    """Update a review. Owner only."""
    user_id = UUID(current_user["user_id"])
    try:
        result = update_review(
            db, slug, review_id, user_id, rating=body.rating, body=body.body
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err
    return ReviewResponse(**result)


@router.post("/{slug}/reviews/{review_id}/vote", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def post_review_vote(
    slug: str,
    review_id: UUID,
    body: ReviewVoteRequest,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Vote on a review (helpful/unhelpful)."""
    user_id = UUID(current_user["user_id"])
    try:
        vote_on_review(db, slug, review_id, user_id, body.vote)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


# --- Comments ---


@router.get("/{slug}/comments", response_model=CommentListResponse)
def get_comments(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> CommentListResponse:
    """Get paginated comments with nested replies."""
    try:
        items, total = list_comments(db, slug, page=page, per_page=per_page)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    has_more = (page * per_page) < total
    return CommentListResponse(
        items=[CommentResponse(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.post("/{slug}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def post_comment(
    slug: str,
    body: CommentCreateRequest,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CommentResponse:
    """Create a comment on a skill."""
    user_id = UUID(current_user["user_id"])
    try:
        result = create_comment(db, slug, user_id, body.body)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return CommentResponse(**result)


@router.delete("/{slug}/comments/{comment_id}", status_code=status.HTTP_200_OK, response_model=CommentResponse)
def remove_comment(
    slug: str,
    comment_id: UUID,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CommentResponse:
    """Soft delete a comment (owner or platform team)."""
    user_id = UUID(current_user["user_id"])
    is_platform = current_user.get("is_platform_team", False)
    try:
        result = delete_comment(db, slug, comment_id, user_id, is_platform_team=is_platform)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err
    return CommentResponse(**result)


@router.post("/{slug}/comments/{comment_id}/replies", response_model=ReplyResponse, status_code=status.HTTP_201_CREATED)
def post_reply(
    slug: str,
    comment_id: UUID,
    body: ReplyCreateRequest,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReplyResponse:
    """Reply to a comment."""
    user_id = UUID(current_user["user_id"])
    try:
        result = create_reply(db, slug, comment_id, user_id, body.body)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return ReplyResponse(**result)


@router.post("/{slug}/comments/{comment_id}/vote", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def post_comment_vote(
    slug: str,
    comment_id: UUID,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Upvote a comment (idempotent)."""
    user_id = UUID(current_user["user_id"])
    try:
        vote_on_comment(db, slug, comment_id, user_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
