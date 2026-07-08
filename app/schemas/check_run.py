from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CheckStatus


class CheckRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_id: UUID
    status: CheckStatus
    http_status_code: int | None
    latency_ms: int | None
    started_at: datetime
    finished_at: datetime
    attempt_number: int
    trigger_source: str
    error_type: str | None
    error_message: str | None
    created_at: datetime


class BatchCheckResponse(BaseModel):
    scheduler_run_id: str
    selected: int = Field(ge=0)
    completed: int = Field(ge=0)
    healthy: int = Field(ge=0)
    degraded: int = Field(ge=0)
    failed: int = Field(ge=0)
    retried_notifications: int = Field(ge=0)
    pruned_check_runs: int = Field(ge=0)
    pruned_notifications: int = Field(ge=0)
