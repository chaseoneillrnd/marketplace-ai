"""Initial schema — all 23 tables.

Revision ID: 001
Revises:
Create Date: 2026-03-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Identity ---
    op.create_table(
        "divisions",
        sa.Column("slug", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("color", sa.String(7), nullable=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "division",
            sa.String(100),
            sa.ForeignKey("divisions.slug"),
            nullable=False,
        ),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("oauth_provider", sa.String(50), nullable=True),
        sa.Column("oauth_sub", sa.String(255), nullable=True),
        sa.Column("is_platform_team", sa.Boolean(), default=False),
        sa.Column("is_security_team", sa.Boolean(), default=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "oauth_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("access_token_hash", sa.String(128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # --- Skill Core ---
    op.create_table(
        "categories",
        sa.Column("slug", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer(), default=0),
    )

    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_desc", sa.String(255), nullable=False),
        sa.Column(
            "category",
            sa.String(100),
            sa.ForeignKey("categories.slug"),
            nullable=False,
        ),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("author_type", sa.String(20), default="community"),
        sa.Column("current_version", sa.String(50), default="1.0.0"),
        sa.Column("install_method", sa.String(20), default="all"),
        sa.Column("data_sensitivity", sa.String(10), default="low"),
        sa.Column("external_calls", sa.Boolean(), default=False),
        sa.Column("verified", sa.Boolean(), default=False),
        sa.Column("featured", sa.Boolean(), default=False),
        sa.Column("featured_order", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), default="draft"),
        sa.Column("install_count", sa.Integer(), default=0),
        sa.Column("fork_count", sa.Integer(), default=0),
        sa.Column("favorite_count", sa.Integer(), default=0),
        sa.Column("view_count", sa.Integer(), default=0),
        sa.Column("review_count", sa.Integer(), default=0),
        sa.Column("avg_rating", sa.Numeric(3, 2), default=0),
        sa.Column("trending_score", sa.Numeric(10, 4), default=0),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "skill_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("frontmatter", sa.JSON(), nullable=True),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False, index=True),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "skill_divisions",
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "division_slug",
            sa.String(100),
            sa.ForeignKey("divisions.slug"),
            primary_key=True,
        ),
    )

    op.create_table(
        "skill_tags",
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("tag", sa.String(100), primary_key=True),
    )

    op.create_table(
        "trigger_phrases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phrase", sa.String(500), nullable=False),
    )

    # --- Social ---
    op.create_table(
        "installs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column(
            "installed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("uninstalled_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "forks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "original_skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "forked_skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "forked_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("upstream_version_at_fork", sa.String(50), nullable=False),
        sa.Column(
            "forked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "favorites",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "follows",
        sa.Column(
            "follower_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "followed_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("helpful_count", sa.Integer(), default=0),
        sa.Column("unhelpful_count", sa.Integer(), default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("skill_id", "user_id", name="uq_reviews_skill_user"),
    )

    op.create_table(
        "review_votes",
        sa.Column(
            "review_id",
            sa.Uuid(),
            sa.ForeignKey("reviews.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("vote", sa.String(10), nullable=False),
    )

    op.create_table(
        "comments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("upvote_count", sa.Integer(), default=0),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "replies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "comment_id",
            sa.Uuid(),
            sa.ForeignKey("comments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "comment_votes",
        sa.Column(
            "comment_id",
            sa.Uuid(),
            sa.ForeignKey("comments.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # --- Submission ---
    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("display_id", sa.String(10), unique=True, nullable=False),
        sa.Column("skill_id", sa.Uuid(), sa.ForeignKey("skills.id"), nullable=True),
        sa.Column("submitted_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_desc", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("declared_divisions", sa.JSON(), nullable=False),
        sa.Column("division_justification", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), default="submitted"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "submission_gate_results",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "submission_id",
            sa.Uuid(),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("gate", sa.Integer(), nullable=False),
        sa.Column("result", sa.String(10), nullable=False),
        sa.Column("findings", sa.JSON(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("reviewer_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "division_access_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("requested_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("user_division", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(10), default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # --- Platform ---
    op.create_table(
        "feature_flags",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("enabled", sa.Boolean(), default=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("division_overrides", sa.JSON(), nullable=True),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", sa.String(255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Audit log append-only trigger: block UPDATE and DELETE
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_log_immutable()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only: UPDATE and DELETE are not allowed';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_log_immutable
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();
    """)


def downgrade() -> None:
    # Drop trigger first
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_immutable ON audit_log;")
    op.execute("DROP FUNCTION IF EXISTS audit_log_immutable();")

    # Drop tables in reverse dependency order
    tables = [
        "audit_log",
        "feature_flags",
        "division_access_requests",
        "submission_gate_results",
        "submissions",
        "comment_votes",
        "replies",
        "comments",
        "review_votes",
        "reviews",
        "follows",
        "favorites",
        "forks",
        "installs",
        "trigger_phrases",
        "skill_tags",
        "skill_divisions",
        "skill_versions",
        "skills",
        "categories",
        "oauth_sessions",
        "users",
        "divisions",
    ]
    for table in tables:
        op.drop_table(table)
