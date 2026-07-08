from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import SchedulerRunStatus


class SchedulerStatusResponse(BaseModel):
    status: str
    expected_interval_minutes: int
    stale_after_seconds: int
    last_run_id: UUID | None
    last_run_status: SchedulerRunStatus | None
    last_run_started_at: datetime | None
    last_run_finished_at: datetime | None
    seconds_since_last_run: int | None
    selected_targets: int
    completed_targets: int
    retried_notifications: int
    pending_notification_retries: int


class ReliabilitySummaryResponse(BaseModel):
    service: str
    version: str
    scheduler: SchedulerStatusResponse
    check_retention_days: int
    notification_retention_days: int
