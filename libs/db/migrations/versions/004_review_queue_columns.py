"""Add gate3 review columns to submissions.

Revision ID: 004_review_queue
Revises: 003_analytics
Create Date: 2026-03-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "004_review_queue"
down_revision = "003_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column("gate3_reviewer_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.add_column(
        "submissions",
        sa.Column("gate3_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "submissions",
        sa.Column("gate3_notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("submissions", "gate3_notes")
    op.drop_column("submissions", "gate3_reviewed_at")
    op.drop_column("submissions", "gate3_reviewer_id")
