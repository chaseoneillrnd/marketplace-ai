"""Add skill_feedback and platform_updates tables.

Revision ID: 004_feedback
Revises: 004_review_queue
Create Date: 2026-03-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "004_feedback"
down_revision = "004_review_queue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skill_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("skill_id", sa.Uuid(), sa.ForeignKey("skills.id"), nullable=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(20), server_default="neutral", nullable=False),
        sa.Column("upvotes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(20), server_default="open", nullable=False),
        sa.Column("allow_contact", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_skill_feedback_category", "skill_feedback", ["category"])
    op.create_index("ix_skill_feedback_status", "skill_feedback", ["status"])
    op.create_index("ix_skill_feedback_user_id", "skill_feedback", ["user_id"])

    op.create_table(
        "platform_updates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), server_default="planned", nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_quarter", sa.String(10), nullable=True),
        sa.Column(
            "linked_feedback_ids",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_platform_updates_status", "platform_updates", ["status"])
    op.create_index("ix_platform_updates_sort_order", "platform_updates", ["sort_order"])


def downgrade() -> None:
    op.drop_table("platform_updates")
    op.drop_table("skill_feedback")
