from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import NotificationEventType, NotificationStatus
from app.db.models.notification_event import NotificationEvent


class NotificationEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, notification_event: NotificationEvent) -> NotificationEvent:
        self.session.add(notification_event)
        await self.session.flush()
        return notification_event

    async def list_all(
        self,
        *,
        target_id: UUID | None = None,
        event_type: NotificationEventType | None = None,
        status_filter: NotificationStatus | None = None,
        limit: int = 100,
    ) -> list[NotificationEvent]:
        statement = (
            select(NotificationEvent).order_by(NotificationEvent.created_at.desc()).limit(limit)
        )
        if target_id is not None:
            statement = statement.where(NotificationEvent.target_id == target_id)
        if event_type is not None:
            statement = statement.where(NotificationEvent.event_type == event_type)
        if status_filter is not None:
            statement = statement.where(NotificationEvent.status == status_filter)

        result = await self.session.scalars(statement)
        return list(result.all())
