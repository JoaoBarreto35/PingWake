from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import Environment, MonitoringMode, OperationalStatus


class DevBaseTargetSummary(BaseModel):
    id: UUID
    name: str
    project_name: str | None
    status: OperationalStatus
    raw_status: str
    enabled: bool
    monitoring_mode: MonitoringMode
    environment: Environment
    last_checked_at: datetime | None
    next_check_at: datetime
    latency_ms: int | None
    http_status_code: int | None
    consecutive_failures: int
    consecutive_successes: int
    open_incident: bool
    incident_started_at: datetime | None
    incident_summary: str | None
    is_stale: bool
    stale_after_seconds: int
    seconds_since_last_check: int | None
    degraded_latency_ms: int
    failure_threshold: int
    recovery_threshold: int
