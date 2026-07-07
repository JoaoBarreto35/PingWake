"""Add Discord notification event logs.

Revision ID: 20260707_0002
Revises: 20260707_0001
Create Date: 2026-07-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260707_0002"
down_revision: str | None = "20260707_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "incident_opened",
                "incident_resolved",
                name="notificationeventtype",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.Enum(
                "discord",
                name="notificationchannel",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "sent",
                "failed",
                name="notificationstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name=op.f("fk_notification_events_incident_id_incidents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_id"],
            ["monitoring_targets.id"],
            name=op.f("fk_notification_events_target_id_monitoring_targets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notification_events")),
    )
    op.create_index(
        "ix_notification_events_incident_id",
        "notification_events",
        ["incident_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_events_target_id",
        "notification_events",
        ["target_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_events_incident_created",
        "notification_events",
        ["incident_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_notification_events_target_created",
        "notification_events",
        ["target_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_events_target_created",
        table_name="notification_events",
    )
    op.drop_index(
        "ix_notification_events_incident_created",
        table_name="notification_events",
    )
    op.drop_index("ix_notification_events_target_id", table_name="notification_events")
    op.drop_index("ix_notification_events_incident_id", table_name="notification_events")
    op.drop_table("notification_events")
