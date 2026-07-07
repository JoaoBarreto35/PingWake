from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import IncidentStatus


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_id: UUID
    status: IncidentStatus
    started_at: datetime
    resolved_at: datetime | None
    first_failure_run_id: UUID
    last_failure_run_id: UUID
    consecutive_failures: int
    consecutive_successes: int
    summary: str
    created_at: datetime
    updated_at: datetime
