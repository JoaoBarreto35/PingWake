from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import NotificationChannel, NotificationEventType, NotificationStatus


class NotificationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    target_id: UUID
    event_type: NotificationEventType
    channel: NotificationChannel
    status: NotificationStatus
    sent_at: datetime | None
    attempt_count: int
    max_attempts: int
    last_attempt_at: datetime | None
    next_retry_at: datetime | None
    error_message: str | None
    created_at: datetime
