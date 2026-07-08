from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    CheckStatus,
    Environment,
    HttpMethod,
    MonitoringMode,
    TargetType,
)
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.check_run import CheckRun
    from app.db.models.incident import Incident
    from app.db.models.notification_event import NotificationEvent


def utc_now() -> datetime:
    return datetime.now(UTC)


class MonitoringTarget(Base):
    __tablename__ = "monitoring_targets"
    __table_args__ = (Index("ix_monitoring_targets_due", "enabled", "next_check_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    devbase_project_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    target_type: Mapped[TargetType] = mapped_column(
        Enum(
            TargetType,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            length=30,
        ),
        nullable=False,
        default=TargetType.API,
    )
    monitoring_mode: Mapped[MonitoringMode] = mapped_column(
        Enum(
            MonitoringMode,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            length=30,
        ),
        nullable=False,
        default=MonitoringMode.MONITOR,
    )
    environment: Mapped[Environment] = mapped_column(
        Enum(
            Environment,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            length=30,
        ),
        nullable=False,
        default=Environment.PRODUCTION,
    )
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    http_method: Mapped[HttpMethod] = mapped_column(
        Enum(
            HttpMethod,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            length=10,
        ),
        nullable=False,
        default=HttpMethod.GET,
    )
    expected_status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    request_headers_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_body_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_custom_headers: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_request_body: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    last_status: Mapped[CheckStatus] = mapped_column(
        Enum(
            CheckStatus,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            length=30,
        ),
        nullable=False,
        default=CheckStatus.PENDING,
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_check_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consecutive_successes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    check_runs: Mapped[list["CheckRun"]] = relationship(
        back_populates="target", cascade="all, delete-orphan"
    )
    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="target", cascade="all, delete-orphan"
    )
    notification_events: Mapped[list["NotificationEvent"]] = relationship(
        back_populates="target", cascade="all, delete-orphan"
    )
