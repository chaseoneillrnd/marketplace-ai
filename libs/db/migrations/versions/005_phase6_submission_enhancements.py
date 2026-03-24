"""Phase 6 prerequisites: submission enhancements, state transitions table.

Revision ID: 005_phase6
Revises: 004_feedback
Create Date: 2026-03-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "005_phase6"
down_revision = "004_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- New columns on submissions ---
    op.add_column(
        "submissions",
        sa.Column(
            "revision_number",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "submissions",
        sa.Column("content_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_submissions_content_hash", "submissions", ["content_hash"])

    op.add_column(
        "submissions",
        sa.Column(
            "parent_submission_id",
            sa.Uuid(),
            sa.ForeignKey("submissions.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "submissions",
        sa.Column(
            "target_skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "submissions",
        sa.Column("rejection_category", sa.String(50), nullable=True),
    )
    op.add_column(
        "submissions",
        sa.Column(
            "change_request_flags",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "submissions",
        sa.Column(
            "submitted_via",
            sa.String(20),
            nullable=False,
            server_default="form",
        ),
    )

    # --- New column on skill_versions ---
    op.add_column(
        "skill_versions",
        sa.Column(
            "submission_id",
            sa.Uuid(),
            sa.ForeignKey("submissions.id"),
            nullable=True,
        ),
    )

    # --- New table: submission_state_transitions ---
    op.create_table(
        "submission_state_transitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "submission_id",
            sa.Uuid(),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(30), nullable=False),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column(
            "actor_id",
            sa.Uuid(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "diff_snapshot",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "change_flags_resolved",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_submission_state_transitions_submission_id",
        "submission_state_transitions",
        ["submission_id"],
    )


def downgrade() -> None:
    op.drop_table("submission_state_transitions")

    op.drop_column("skill_versions", "submission_id")

    op.drop_column("submissions", "submitted_via")
    op.drop_column("submissions", "change_request_flags")
    op.drop_column("submissions", "rejection_category")
    op.drop_column("submissions", "target_skill_id")
    op.drop_column("submissions", "parent_submission_id")
    op.drop_index("ix_submissions_content_hash", table_name="submissions")
    op.drop_column("submissions", "content_hash")
    op.drop_column("submissions", "revision_number")
