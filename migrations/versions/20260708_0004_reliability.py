"""Add reliability policies, notification retries and scheduler watchdog.

Revision ID: 20260708_0004
Revises: 20260708_0003
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260708_0004"
down_revision: str | None = "20260708_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("monitoring_targets") as batch_op:
        batch_op.add_column(sa.Column("degraded_latency_ms", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("failure_threshold", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("recovery_threshold", sa.Integer(), nullable=True))

    with op.batch_alter_table("notification_events") as batch_op:
        batch_op.add_column(
            sa.Column(
                "attempt_count",
                sa.Integer(),
                nullable=False,
                server_default="1",
            )
        )
        batch_op.add_column(
            sa.Column(
                "max_attempts",
                sa.Integer(),
                nullable=False,
                server_default="4",
            )
        )
        batch_op.add_column(sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.drop_constraint(
            op.f("ck_notification_events_notificationstatus"),
            type_="check",
        )
        batch_op.create_check_constraint(
            op.f("ck_notification_events_notificationstatus"),
            "status IN ('pending', 'retrying', 'sent', 'failed')",
        )

    with op.batch_alter_table("notification_events") as batch_op:
        batch_op.alter_column("attempt_count", server_default=None)
        batch_op.alter_column("max_attempts", server_default=None)

    op.create_index(
        "ix_notification_events_retry_due",
        "notification_events",
        ["status", "next_retry_at"],
        unique=False,
    )

    op.create_table(
        "scheduler_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "running",
                "completed",
                "partial",
                "failed",
                name="schedulerrunstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("selected_targets", sa.Integer(), nullable=False),
        sa.Column("completed_targets", sa.Integer(), nullable=False),
        sa.Column("healthy_targets", sa.Integer(), nullable=False),
        sa.Column("failed_targets", sa.Integer(), nullable=False),
        sa.Column("retried_notifications", sa.Integer(), nullable=False),
        sa.Column("pruned_check_runs", sa.Integer(), nullable=False),
        sa.Column("pruned_notifications", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scheduler_runs")),
    )
    op.create_index(
        "ix_scheduler_runs_started",
        "scheduler_runs",
        ["started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_scheduler_runs_started", table_name="scheduler_runs")
    op.drop_table("scheduler_runs")

    op.drop_index("ix_notification_events_retry_due", table_name="notification_events")
    with op.batch_alter_table("notification_events") as batch_op:
        batch_op.drop_constraint(
            op.f("ck_notification_events_notificationstatus"),
            type_="check",
        )
        batch_op.create_check_constraint(
            op.f("ck_notification_events_notificationstatus"),
            "status IN ('sent', 'failed')",
        )
        batch_op.drop_column("next_retry_at")
        batch_op.drop_column("last_attempt_at")
        batch_op.drop_column("max_attempts")
        batch_op.drop_column("attempt_count")

    with op.batch_alter_table("monitoring_targets") as batch_op:
        batch_op.drop_column("recovery_threshold")
        batch_op.drop_column("failure_threshold")
        batch_op.drop_column("degraded_latency_ms")
