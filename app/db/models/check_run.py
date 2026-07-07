from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CheckStatus
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.monitoring_target import MonitoringTarget


def utc_now() -> datetime:
    return datetime.now(UTC)


class CheckRun(Base):
    __tablename__ = "check_runs"
    __table_args__ = (Index("ix_check_runs_target_started", "target_id", "started_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    target_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitoring_targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[CheckStatus] = mapped_column(
        Enum(
            CheckStatus,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            length=30,
        ),
        nullable=False,
    )
    http_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    trigger_source: Mapped[str] = mapped_column(String(30), nullable=False)
    error_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    target: Mapped["MonitoringTarget"] = relationship(back_populates="check_runs")
