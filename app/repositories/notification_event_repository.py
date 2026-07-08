from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import NotificationEventType, NotificationStatus
from app.db.models.notification_event import NotificationEvent


class NotificationEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, notification_id: UUID) -> NotificationEvent | None:
        return await self.session.get(NotificationEvent, notification_id)

    async def get_for_transition(
        self,
        incident_id: UUID,
        event_type: NotificationEventType,
    ) -> NotificationEvent | None:
        statement = (
            select(NotificationEvent)
            .where(
                NotificationEvent.incident_id == incident_id,
                NotificationEvent.event_type == event_type,
            )
            .order_by(NotificationEvent.created_at.desc())
            .limit(1)
        )
        result = await self.session.scalars(statement)
        return result.first()

    async def list_due_retries(self, now: datetime, limit: int = 100) -> list[NotificationEvent]:
        statement = (
            select(NotificationEvent)
            .where(
                NotificationEvent.status.in_(
                    [
                        NotificationStatus.PENDING,
                        NotificationStatus.RETRYING,
                    ]
                ),
                NotificationEvent.next_retry_at.is_not(None),
                NotificationEvent.next_retry_at <= now,
                NotificationEvent.attempt_count < NotificationEvent.max_attempts,
            )
            .order_by(NotificationEvent.next_retry_at)
            .limit(limit)
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def delete_older_than(self, cutoff: datetime) -> int:
        ids_result = await self.session.scalars(
            select(NotificationEvent.id).where(
                NotificationEvent.created_at < cutoff,
                NotificationEvent.status.in_([NotificationStatus.SENT, NotificationStatus.FAILED]),
            )
        )
        ids = list(ids_result.all())
        if ids:
            await self.session.execute(
                delete(NotificationEvent).where(NotificationEvent.id.in_(ids))
            )
        return len(ids)

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
