"""Analytics engine: daily_metrics, export_jobs, users.admin_scopes, indexes.

Revision ID: 003_analytics
Revises: e20cb6415067
Create Date: 2026-03-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "003_analytics"
down_revision = "e20cb6415067"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users.admin_scopes
    op.add_column(
        "users",
        sa.Column(
            "admin_scopes",
            postgresql.JSON(astext_type=sa.Text()),
            server_default="'[]'::json",
            nullable=False,
        ),
    )

    # Performance indexes
    op.create_index("ix_installs_installed_at", "installs", ["installed_at"])
    op.create_index("ix_submissions_created_at", "submissions", ["created_at"])

    # daily_metrics table
    op.create_table(
        "daily_metrics",
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("division_slug", sa.String(100), nullable=False),
        sa.Column("new_installs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_installs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uninstalls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dau", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_submissions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_skills", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_reviews", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("funnel_submitted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("funnel_g1_pass", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("funnel_g2_pass", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("funnel_approved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("funnel_published", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("gate3_median_wait", sa.BigInteger(), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("metric_date", "division_slug"),
    )
    op.create_index(
        "ix_daily_metrics_date",
        "daily_metrics",
        [sa.text("metric_date DESC")],
    )
    op.create_index(
        "ix_daily_metrics_div_date",
        "daily_metrics",
        ["division_slug", sa.text("metric_date DESC")],
    )

    # export_jobs table
    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "requested_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column("format", sa.String(10), nullable=False, server_default="'csv'"),
        sa.Column(
            "filters", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="'queued'"),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("export_jobs")
    op.drop_index("ix_daily_metrics_div_date")
    op.drop_index("ix_daily_metrics_date")
    op.drop_table("daily_metrics")
    op.drop_index("ix_submissions_created_at")
    op.drop_index("ix_installs_installed_at")
    op.drop_column("users", "admin_scopes")
