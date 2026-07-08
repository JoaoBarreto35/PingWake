"""Add encrypted custom headers and JSON request bodies.

Revision ID: 20260708_0003
Revises: 20260707_0002
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260708_0003"
down_revision: str | None = "20260707_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("monitoring_targets") as batch_op:
        batch_op.add_column(sa.Column("request_headers_encrypted", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("request_body_encrypted", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "has_custom_headers",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "has_request_body",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    with op.batch_alter_table("monitoring_targets") as batch_op:
        batch_op.alter_column("has_custom_headers", server_default=None)
        batch_op.alter_column("has_request_body", server_default=None)
        batch_op.drop_constraint(
            op.f("ck_monitoring_targets_httpmethod"),
            type_="check",
        )
        batch_op.create_check_constraint(
            op.f("ck_monitoring_targets_httpmethod"),
            "http_method IN ('GET', 'HEAD', 'POST')",
        )


def downgrade() -> None:
    with op.batch_alter_table("monitoring_targets") as batch_op:
        batch_op.drop_constraint(
            op.f("ck_monitoring_targets_httpmethod"),
            type_="check",
        )
        batch_op.create_check_constraint(
            op.f("ck_monitoring_targets_httpmethod"),
            "http_method IN ('GET', 'HEAD')",
        )
        batch_op.drop_column("has_request_body")
        batch_op.drop_column("has_custom_headers")
        batch_op.drop_column("request_body_encrypted")
        batch_op.drop_column("request_headers_encrypted")
