"""Create initial PingWake schema.

Revision ID: 20260707_0001
Revises:
Create Date: 2026-07-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260707_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "monitoring_targets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("project_name", sa.String(length=120), nullable=True),
        sa.Column("devbase_project_id", sa.String(length=120), nullable=True),
        sa.Column(
            "target_type",
            sa.Enum(
                "api",
                "database",
                "website",
                "webhook",
                name="targettype",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "monitoring_mode",
            sa.Enum(
                "monitor",
                "keep_awake",
                "database_activity",
                name="monitoringmode",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "environment",
            sa.Enum(
                "development",
                "staging",
                "production",
                name="environment",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column(
            "http_method",
            sa.Enum("GET", "HEAD", name="httpmethod", native_enum=False, create_constraint=True),
            nullable=False,
        ),
        sa.Column("expected_status_code", sa.Integer(), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "last_status",
            sa.Enum(
                "pending",
                "healthy",
                "degraded",
                "unhealthy",
                "timeout",
                "configuration_error",
                name="checkstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("consecutive_successes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_monitoring_targets")),
    )
    op.create_index(
        "ix_monitoring_targets_devbase_project_id",
        "monitoring_targets",
        ["devbase_project_id"],
        unique=False,
    )
    op.create_index(
        "ix_monitoring_targets_due",
        "monitoring_targets",
        ["enabled", "next_check_at"],
        unique=False,
    )

    op.create_table(
        "check_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "healthy",
                "degraded",
                "unhealthy",
                "timeout",
                "configuration_error",
                name="checkstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("trigger_source", sa.String(length=30), nullable=False),
        sa.Column("error_type", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["target_id"],
            ["monitoring_targets.id"],
            name=op.f("fk_check_runs_target_id_monitoring_targets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_check_runs")),
    )
    op.create_index("ix_check_runs_target_id", "check_runs", ["target_id"], unique=False)
    op.create_index(
        "ix_check_runs_target_started",
        "check_runs",
        ["target_id", "started_at"],
        unique=False,
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "acknowledged",
                "resolved",
                name="incidentstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_failure_run_id", sa.Uuid(), nullable=False),
        sa.Column("last_failure_run_id", sa.Uuid(), nullable=False),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("consecutive_successes", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["target_id"],
            ["monitoring_targets.id"],
            name=op.f("fk_incidents_target_id_monitoring_targets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incidents")),
    )
    op.create_index("ix_incidents_target_id", "incidents", ["target_id"], unique=False)
    op.create_index(
        "ix_incidents_target_started",
        "incidents",
        ["target_id", "started_at"],
        unique=False,
    )
    op.create_index(
        "uq_incidents_one_open_per_target",
        "incidents",
        ["target_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )


def downgrade() -> None:
    op.drop_index("uq_incidents_one_open_per_target", table_name="incidents")
    op.drop_index("ix_incidents_target_started", table_name="incidents")
    op.drop_index("ix_incidents_target_id", table_name="incidents")
    op.drop_table("incidents")
    op.drop_index("ix_check_runs_target_started", table_name="check_runs")
    op.drop_index("ix_check_runs_target_id", table_name="check_runs")
    op.drop_table("check_runs")
    op.drop_index("ix_monitoring_targets_due", table_name="monitoring_targets")
    op.drop_index("ix_monitoring_targets_devbase_project_id", table_name="monitoring_targets")
    op.drop_table("monitoring_targets")
