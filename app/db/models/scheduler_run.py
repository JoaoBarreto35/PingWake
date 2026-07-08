from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import SchedulerRunStatus
from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class SchedulerRun(Base):
    __tablename__ = "scheduler_runs"
    __table_args__ = (Index("ix_scheduler_runs_started", "started_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[SchedulerRunStatus] = mapped_column(
        Enum(
            SchedulerRunStatus,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            length=20,
        ),
        nullable=False,
        default=SchedulerRunStatus.RUNNING,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    selected_targets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_targets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    healthy_targets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_targets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retried_notifications: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pruned_check_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pruned_notifications: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
