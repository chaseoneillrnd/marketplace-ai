"""Add feedback_upvotes table for idempotent upvote tracking.

Revision ID: 006_feedback_upvotes
Revises: 005_phase6
Create Date: 2026-03-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "006_feedback_upvotes"
down_revision = "005_phase6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback_upvotes",
        sa.Column(
            "feedback_id",
            sa.Uuid(),
            sa.ForeignKey("skill_feedback.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("feedback_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("feedback_upvotes")
