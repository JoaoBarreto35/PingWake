from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import CheckStatus, Environment, MonitoringMode


class DevBaseTargetSummary(BaseModel):
    id: UUID
    name: str
    project_name: str | None
    status: CheckStatus
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
